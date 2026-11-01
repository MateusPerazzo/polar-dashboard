import streamlit as st
from PIL import Image
from streamlit_cropper import st_cropper

from app import settings, ui
from app.insights import LEVELS, RECHARGE_STATUS, TEXT_LIMITS

# Tamanho máximo da imagem na moldura de recorte (o componente desenha num canvas desse tamanho).
CROPPER_SIZE = (520, 420)
# Espessura da borda da moldura. O componente mede a moldura com a borda incluída, então ela é
# descontada na leitura e na posição inicial; sem isso, o recorte cresceria a cada salvamento.
CROPPER_STROKE = 3

# Campo do nível -> (rótulo, caixa de várias linhas?). Coluna da esquerda: Insight; da direita: personagem.
TEXT_FIELDS = {
    "headline": ("Título do Insight", False),
    "summary": ("Frase do topo do Resumo", False),
    "advice": ("Conselho", True),
    "character": ("Personagem", False),
    "mood": ("Humor do personagem", False),
    "quote": ("Fala do personagem", True),
}

# Prévia com a mesma moldura do Insight do dia (--image-ratio, cantos arredondados), sem o botão
# de tela cheia.
CSS = """
<style>
[class*="st-key-preview-"] img {
    width: 100%; aspect-ratio: var(--image-ratio); object-fit: cover;
    border-radius: 16px; border: 1px solid var(--border);
}
[class*="st-key-preview-"] [data-testid="stElementToolbar"] { display: none; }
</style>
"""


def save_colors():
    data = settings.load()
    # Guarda só as cores diferentes do padrão (grupos e Insight ficam juntos em "colors").
    data["colors"] = {
        name: st.session_state[f"color-{name}"]
        for name, info in {**ui.GROUPS, **ui.INSIGHT_COLORS}.items()
        if st.session_state[f"color-{name}"].lower() != info["color"]
    }
    if not data["colors"]:
        del data["colors"]
    settings.save(data)
    st.toast("Cores salvas.", icon=":material/check:")


def restore_colors():
    data = settings.load()
    data.pop("colors", None)
    settings.save(data)
    # Sem isso, os seletores continuariam mostrando a cor antiga (o widget guarda o valor na sessão).
    for name in {**ui.GROUPS, **ui.INSIGHT_COLORS}:
        st.session_state.pop(f"color-{name}", None)


def save_levels():
    data = settings.load()
    # Por nível, só os campos preenchidos e diferentes do padrão.
    data["levels"] = {}
    for status, defaults in LEVELS.items():
        changed = {
            field: st.session_state[f"level-{status}-{field}"].strip()
            for field in TEXT_FIELDS
            if st.session_state[f"level-{status}-{field}"].strip() not in ("", defaults[field])
        }
        if changed:
            data["levels"][str(status)] = changed
    if not data["levels"]:
        del data["levels"]
    settings.save(data)
    st.toast("Mensagens salvas.", icon=":material/check:")


def restore_levels():
    # Os 6 níveis voltam ao padrão por inteiro: textos, imagens (as de app/assets/recharge/) e
    # recortes. As imagens enviadas são apagadas de data/recharge/.
    data = settings.load()
    data.pop("levels", None)
    data.pop("images", None)
    settings.save(data)
    for status in LEVELS:
        settings.remove_image(status)
        next_image_round(status)  # moldura e upload recomeçam
        for field in TEXT_FIELDS:
            st.session_state.pop(f"level-{status}-{field}", None)
    st.toast("Textos, imagens e recortes dos 6 níveis restaurados.", icon=":material/check:")


def image_round(status):
    # Trocar a imagem muda este número, que entra na key do uploader e da moldura:
    # o uploader volta vazio (ele continua segurando o arquivo enviado) e a moldura recomeça.
    return st.session_state.get(f"image-round-{status}", 0)


def next_image_round(status):
    st.session_state[f"image-round-{status}"] = image_round(status) + 1


def set_crop(status, crop):
    """Salva o recorte do nível (None apaga). Também limpa campos antigos (formato, altura)."""
    data = settings.load()
    images = data.setdefault("images", {})
    if crop is None:
        images.pop(str(status), None)
    else:
        images[str(status)] = {"crop": crop}
    if not images:
        del data["images"]
    settings.save(data)


def save_image(status, key):
    file = st.session_state[key]
    if file is None:
        return
    settings.save_image(status, file.name.rsplit(".", 1)[-1], file.getvalue())
    set_crop(status, None)  # o recorte salvo era da imagem anterior
    next_image_round(status)
    st.toast("Imagem salva.", icon=":material/check:")


def restore_image(status):
    settings.remove_image(status)
    set_crop(status, None)
    next_image_round(status)
    st.toast("Imagem padrão restaurada.", icon=":material/check:")


@st.cache_data(show_spinner=False)
def thumbnail(path, modified):
    """Imagem reduzida para a moldura de recorte; modified entra na chave do cache."""
    with Image.open(path) as image:
        image.thumbnail(CROPPER_SIZE)
        return image.copy()


def image_editor(status):
    """Moldura de recorte (travada em 16:9) à esquerda; prévia e troca da imagem à direita."""
    image = settings.image_path(status)
    crop_col, side_col = st.columns([3, 2], gap="medium")
    current = None
    with crop_col:
        if not image.exists():
            st.caption("Sem imagem para este nível.")
        else:
            thumb = thumbnail(str(image), image.stat().st_mtime)
            saved = settings.image_crop(status)
            crop_key = f"crop-{status}-{image_round(status)}"
            # O componente guarda a moldura em st.session_state[crop_key] depois que ela é mexida.
            # Até lá (moldura acabou de aparecer), a posição inicial é recalculada a partir do
            # recorte salvo; depois, fica fixa: se mudasse, o componente reposicionaria a moldura
            # mantendo o zoom, e o salvamento automático entraria em ciclo.
            touched = st.session_state.get(crop_key) is not None
            if not touched:
                # Recorte salvo num formato anterior (16:9) é adaptado ao atual, mantendo o centro.
                st.session_state[f"crop-start-{status}"] = (
                    settings.fit_crop(saved, thumb.size) if saved else settings.default_crop(thumb.size))
            x0, y0, x1, y1 = settings.crop_pixels(st.session_state[f"crop-start-{status}"], thumb.size)
            half = CROPPER_STROKE / 2
            # default_coords = (esquerda, direita, topo, base); a borda fica do lado de fora do recorte.
            box = st_cropper(thumb, aspect_ratio=settings.IMAGE_RATIO,
                             default_coords=(x0 - half, x1 - half, y0 - half, y1 - half),
                             box_color="#f0efec", return_type="box", should_resize_image=False,
                             stroke_width=CROPPER_STROKE, key=crop_key)
            width, height = thumb.size
            current = settings.clamp_crop([(box["left"] + half) / width, (box["top"] + half) / height,
                                           (box["width"] - CROPPER_STROKE) / width,
                                           (box["height"] - CROPPER_STROKE) / height])
            # Salva sozinho a cada movimento da moldura (só depois que ela foi mexida).
            if touched and current != saved:
                set_crop(status, current)
            st.caption("Arraste a moldura para escolher o trecho; puxe os cantos para aproximar ou afastar. "
                       "O formato é fixo, igual ao das imagens padrão. O recorte é salvo automaticamente.")
    with side_col:
        # A prévia acompanha a moldura ao vivo, mesmo antes de salvar.
        with st.container(key=f"preview-{status}"):
            if current is not None:
                st.image(thumb.crop(settings.crop_pixels(current, thumb.size)), width="stretch",
                         caption="Prévia")
        key = f"upload-{status}-{image_round(status)}"
        st.file_uploader("Trocar imagem", type=settings.IMAGE_TYPES, key=key,
                         on_change=save_image, args=(status, key),
                         help="A imagem fica salva só no seu computador.")
        customized = settings.custom_image(status) is not None or settings.image_crop(status) is not None
        st.button("Restaurar imagem padrão", icon=":material/restart_alt:", key=f"restore-image-{status}",
                  on_click=restore_image, args=(status,), disabled=not customized,
                  help="Volta a imagem e o recorte ao padrão.")


def colors_editor():
    current = ui.groups()
    for column, (name, info) in zip(st.columns(len(current)), current.items()):
        column.color_picker(f":material/{info['icon']}: {info['title']}",
                            value=info["color"], key=f"color-{name}")
    # Mesma grade de 4 colunas da linha de cima, para os seletores ficarem alinhados.
    for column, (name, info) in zip(st.columns(len(current)), ui.insight_colors().items()):
        column.color_picker(f":material/auto_awesome: {info['title']}", value=info["color"],
                            help=info["help"], key=f"color-{name}")
    with st.container(horizontal=True):
        st.button("Salvar cores", icon=":material/save:", type="primary", on_click=save_colors)
        st.button("Restaurar padrão", icon=":material/restart_alt:", on_click=restore_colors,
                  key="restore-colors")


def levels_editor():
    current = ui.levels()
    # on_change="rerun" faz cada aba saber se está aberta (tab.open). A moldura de recorte só é
    # desenhada na aba aberta: numa aba escondida, o componente mede altura zero ao nascer e
    # continua vazio quando a aba é aberta.
    tabs = st.tabs([f"{status} · {ui.capitalize(RECHARGE_STATUS[status])}" for status in current],
                   key="level-tabs", on_change="rerun")
    for tab, (status, texts) in zip(tabs, current.items()):
        insight_col, character_col = tab.columns(2, gap="medium")
        for index, (field, (label, multiline)) in enumerate(TEXT_FIELDS.items()):
            column = insight_col if index < 3 else character_col
            widget = column.text_area if multiline else column.text_input
            # O limite mantém cada seção do Insight do dia no tamanho fixo. O valor é cortado no
            # limite porque o Streamlit dá erro se um texto salvo antes for maior que max_chars.
            limit = TEXT_LIMITS[field]
            widget(label, value=texts[field][:limit], max_chars=limit, key=f"level-{status}-{field}")
        if tab.open:
            with tab:
                ui.panel_title("Imagem do personagem", "Arraste a moldura para escolher o que aparece no Insight")
                image_editor(status)
    with st.container(horizontal=True):
        st.button("Salvar mensagens", icon=":material/save:", type="primary", on_click=save_levels)
        st.button("Restaurar padrão", icon=":material/restart_alt:", on_click=restore_levels,
                  key="restore-levels",
                  help="Volta textos, imagens e recortes dos 6 níveis ao padrão (imagens de anime em "
                       "8 bits). As imagens que você enviou são apagadas.")


def save_look(key):
    # Vale na hora: o callback roda antes da página, e o CSS de todas as páginas lê o que está salvo.
    data = settings.load()
    data.pop("appearance", None)  # opção única da versão anterior, substituída por fundo + quadrados
    choice = st.session_state[f"look-{key}"]
    if choice == settings.DEFAULT_LOOK[key]:
        data.pop(key, None)
    else:
        data[key] = choice
    settings.save(data)


def look_editor():
    current = settings.look()
    # Cada escolha: (chave, rótulo, opções, legenda de cada opção).
    choices = [
        ("background", "Fundo", settings.BACKGROUNDS,
         ["Página escura (padrão).", "Página clara, com texto escuro."]),
        ("cards", "Quadrados", settings.CARD_STYLES,
         ["Neutros (cinza no preto, brancos no branco), com degradê das cores (padrão).",
          "Cada um num tom liso da sua cor, sem degradê."]),
    ]
    for column, (key, label, options, captions) in zip(st.columns(2, gap="medium"), choices):
        values = list(options)
        column.radio(label, values, index=values.index(current[key]), format_func=options.get,
                     captions=captions, key=f"look-{key}", on_change=save_look, args=(key,))


def section(key, title, icon, subtitle, help_text):
    """Seção recolhível pela seta do título (aberta no início). O conteúdo só é desenhado com a
    seção aberta (on_change="rerun" + .open), pelo mesmo motivo das abas: a moldura de recorte
    fica vazia se nascer escondida. Fechar a seção descarta o que não foi salvo nela."""
    expander = st.expander(title, expanded=True, icon=icon, key=f"section-{key}", on_change="rerun")
    if expander.open:
        expander.html(f'<div class="panel-head"><span class="panel-subtitle">{subtitle}</span>'
                      f'{ui.tip(help_text)}</div>')
    return expander


st.html(CSS)
st.html(f"""
<div class="eyebrow" style="color:var(--muted)">{ui.icon('settings')} Personalização</div>
<div class="page-title">Configurações</div>
<div class="page-subtitle">Aparência, cores do app e mensagens de cada nível de recuperação.
Tudo fica salvo só no seu computador.</div>""")

appearance = section("appearance", "Aparência", ":material/contrast:",
                     "Fundo da página e estilo dos quadrados, em todas as páginas",
                     "As duas escolhas são independentes e valem na hora. As cores dos grupos e do "
                     "Insight continuam as escolhidas abaixo. Com quadrados sólidos, cada cartão ganha "
                     "um tom da sua cor (o Insight, a do resultado; nas páginas de detalhe, a cor do "
                     "grupo da página).")
if appearance.open:
    with appearance:
        look_editor()

colors = section("colors", "Cores", ":material/palette:",
                 "Grupos na primeira linha; Insight do dia, por resultado da recuperação, na segunda",
                 "A cor de cada grupo vale para todo o app: cartões do Resumo, títulos e gráficos "
                 "(a FC aparece com a cor dela em qualquer página). A do Insight do dia muda com o "
                 "resultado da noite e pinta a borda, o fundo, o selo da noite, o anel da avaliação "
                 "e o nome do personagem.")
if colors.open:
    with colors:
        colors_editor()

levels = section("levels", "Níveis de recuperação", ":material/auto_awesome:",
                 "Mensagens e imagem do Insight do dia para cada status do Nightly Recharge",
                 "O status vai de 1 (muito ruim) a 6 (muito boa). Um campo deixado vazio volta ao "
                 "texto padrão.")
if levels.open:
    with levels:
        levels_editor()
