import streamlit as st

from app import settings, ui
from app.insights import LEVELS, RECHARGE_STATUS

# Campo do nível -> (rótulo, caixa de várias linhas?). Coluna da esquerda: Insight; da direita: personagem.
TEXT_FIELDS = {
    "headline": ("Título do Insight", False),
    "summary": ("Frase do topo do Resumo", False),
    "advice": ("Conselho", True),
    "character": ("Personagem", False),
    "mood": ("Humor do personagem", False),
    "quote": ("Fala do personagem", True),
}

# Prévia com o mesmo corte do Insight do dia (variáveis de ui.image_vars), sem o botão de tela cheia.
CSS = """
<style>
[class*="st-key-preview-"] img {
    width: 100%; aspect-ratio: var(--img-ratio); max-height: var(--img-height);
    object-fit: var(--img-fit); object-position: var(--img-position);
    border-radius: 16px; border: 1px solid var(--border);
}
[class*="st-key-preview-"] [data-testid="stElementToolbar"] { display: none; }
</style>
"""


def save_colors():
    data = settings.load()
    # Guarda só as cores diferentes do padrão.
    data["colors"] = {
        name: st.session_state[f"color-{name}"]
        for name, info in ui.GROUPS.items()
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
    for name in ui.GROUPS:
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
    data = settings.load()
    data.pop("levels", None)
    settings.save(data)
    for status in LEVELS:
        for field in TEXT_FIELDS:
            st.session_state.pop(f"level-{status}-{field}", None)


def upload_key(status):
    # O uploader continua segurando o arquivo depois do envio; trocar a key cria um vazio.
    return f"upload-{status}-{st.session_state.get(f'upload-round-{status}', 0)}"


def save_image(status, key):
    file = st.session_state[key]
    if file is None:
        return
    settings.save_image(status, file.name.rsplit(".", 1)[-1], file.getvalue())
    st.session_state[f"upload-round-{status}"] = st.session_state.get(f"upload-round-{status}", 0) + 1
    st.toast("Imagem salva.", icon=":material/check:")


def save_style(status):
    data = settings.load()
    images = data.setdefault("images", {})
    # Só os valores diferentes do padrão.
    changed = {
        field: st.session_state[f"image-{status}-{field}"]
        for field, default in settings.IMAGE_DEFAULTS.items()
        if st.session_state[f"image-{status}-{field}"] != default
    }
    if changed:
        images[str(status)] = changed
    else:
        images.pop(str(status), None)
    if not images:
        del data["images"]
    settings.save(data)


def restore_image(status):
    # A imagem padrão foi enquadrada para o formato padrão, então as dimensões voltam junto.
    settings.remove_image(status)
    data = settings.load()
    images = data.get("images", {})
    images.pop(str(status), None)
    if not images:
        data.pop("images", None)
    settings.save(data)
    for field in settings.IMAGE_DEFAULTS:
        st.session_state.pop(f"image-{status}-{field}", None)
    st.toast("Imagem padrão restaurada.", icon=":material/check:")


st.html(CSS)
st.html(f"""
<div class="eyebrow" style="color:var(--muted)">{ui.icon('settings')} Personalização</div>
<div class="page-title">Configurações</div>
<div class="page-subtitle">Cores dos grupos e mensagens de cada nível de recuperação.
Tudo fica salvo só no seu computador.</div>""")

with st.container(border=True, key="panel-colors"):
    ui.panel_title("Cores dos grupos", "A cor de cada grupo vale para todo o app",
                   "Usada nos cartões do Resumo, nos títulos e nos gráficos. "
                   "A cor segue o dado: a FC aparece com a cor dela em qualquer página.")
    current = ui.groups()
    for column, (name, info) in zip(st.columns(len(current)), current.items()):
        column.color_picker(f":material/{info['icon']}: {info['title']}",
                            value=info["color"], key=f"color-{name}")
    with st.container(horizontal=True):
        st.button("Salvar cores", icon=":material/save:", type="primary", on_click=save_colors)
        st.button("Restaurar padrão", icon=":material/restart_alt:", on_click=restore_colors,
                  key="restore-colors")

with st.container(border=True, key="panel-levels"):
    ui.panel_title("Níveis de recuperação", "Mensagens do Insight do dia para cada status do Nightly Recharge",
                   "O status vai de 1 (muito ruim) a 6 (muito boa). Um campo deixado vazio "
                   "volta ao texto padrão.")
    current = ui.levels()
    tabs = st.tabs([f"{status} · {ui.capitalize(RECHARGE_STATUS[status])}" for status in current])
    for tab, (status, texts) in zip(tabs, current.items()):
        insight_col, character_col = tab.columns(2, gap="medium")
        for index, (field, (label, multiline)) in enumerate(TEXT_FIELDS.items()):
            column = insight_col if index < 3 else character_col
            widget = column.text_area if multiline else column.text_input
            widget(label, value=texts[field], key=f"level-{status}-{field}")
        with character_col:
            image = settings.image_path(status)
            style = settings.image_style(status)
            ui.image_vars(f".st-key-preview-{status}", style)
            with st.container(key=f"preview-{status}"):
                if image.exists():
                    st.image(str(image), width="stretch")
                else:
                    st.caption("Sem imagem para este nível.")
            # Dimensões: salvas a cada mudança, e a prévia acompanha.
            st.segmented_control("Formato", settings.IMAGE_RATIOS, default=style["ratio"], required=True,
                                 key=f"image-{status}-ratio", on_change=save_style, args=(status,),
                                 help="Proporção do corte. \"Original\" mostra a imagem inteira, sem corte.")
            st.slider("Altura máxima (px)", *settings.IMAGE_HEIGHTS, value=style["height"], step=10,
                      key=f"image-{status}-height", on_change=save_style, args=(status,),
                      help="Se a imagem ficar mais alta que isso, ela é cortada. Imagens altas "
                           "esticam o cartão do Insight e, com ele, os cartões vizinhos.")
            st.segmented_control("Enquadramento", list(settings.IMAGE_POSITIONS), default=style["position"],
                                 format_func=settings.IMAGE_POSITIONS.get, required=True,
                                 key=f"image-{status}-position", on_change=save_style, args=(status,),
                                 help="Qual parte da imagem fica visível quando ela é cortada.")
            key = upload_key(status)
            st.file_uploader("Trocar imagem", type=settings.IMAGE_TYPES, key=key,
                             on_change=save_image, args=(status, key),
                             help="A imagem fica salva só no seu computador.")
            customized = settings.custom_image(status) is not None or style != settings.IMAGE_DEFAULTS
            st.button("Restaurar imagem padrão", icon=":material/restart_alt:", key=f"restore-image-{status}",
                      on_click=restore_image, args=(status,), disabled=not customized,
                      help="Volta a imagem e as dimensões ao padrão.")
    with st.container(horizontal=True):
        st.button("Salvar mensagens", icon=":material/save:", type="primary", on_click=save_levels)
        st.button("Restaurar padrão", icon=":material/restart_alt:", on_click=restore_levels,
                  key="restore-levels")
