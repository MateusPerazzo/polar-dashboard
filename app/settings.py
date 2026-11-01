"""Personalizações do usuário (cores e níveis), guardadas em data/settings.json.

O arquivo guarda só o que foi alterado; o resto vem dos padrões do código.
Fica em data/, que não vai para o Git. Sem dependência do Streamlit.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SETTINGS_FILE = DATA_DIR / "settings.json"
# Imagens dos níveis (1.png = muito ruim ... 6.png = muito boa). As enviadas pelo
# usuário ficam em data/recharge/ e têm prioridade sobre as padrão.
DEFAULT_IMAGES_DIR = ROOT / "app" / "assets" / "recharge"
IMAGES_DIR = DATA_DIR / "recharge"
IMAGE_TYPES = ["png", "jpg", "jpeg", "webp"]
# A imagem do Insight ocupa sempre a mesma moldura (largura toda do cartão, 3:2); o recorte
# só escolhe o trecho e o zoom: [esquerda, topo, largura, altura] em frações (0 a 1).
# Era 16:9; recortes salvos em outro formato são adaptados por fit_crop.
IMAGE_RATIO = (3, 2)
HEX_COLOR = re.compile(r"#[0-9a-fA-F]{6}")
# Aparência de todas as páginas, em duas escolhas independentes. As cores dos grupos e do
# Insight valem em todas. Quadrados "gradient": neutros (cinza no preto, brancos no branco), com
# degradê das cores; "solid": cada um num tom liso da sua cor, sem degradê.
BACKGROUNDS = {"dark": "Preto", "light": "Branco"}
CARD_STYLES = {"gradient": "Degradê", "solid": "Sólido"}
DEFAULT_LOOK = {"background": "dark", "cards": "gradient"}


def load():
    """Devolve as personalizações salvas; {} se o arquivo não existe ou está corrompido."""
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save(data):
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def look():
    """Fundo e estilo dos quadrados salvos."""
    return apply_look(load())


def apply_look(data):
    """{"background", "cards"} a partir do JSON; valor ausente ou desconhecido volta ao padrão."""
    options = {"background": BACKGROUNDS, "cards": CARD_STYLES}
    return {key: data[key] if data.get(key) in options[key] else default
            for key, default in DEFAULT_LOOK.items()}


def is_light():
    """Fundo branco?"""
    return look()["background"] == "light"


def is_solid():
    """Quadrados em cor lisa (sem degradê)?"""
    return look()["cards"] == "solid"


def custom_image(status):
    """Imagem enviada pelo usuário para o nível, ou None."""
    found = sorted(IMAGES_DIR.glob(f"{status}.*"))
    return found[0] if found else None


def image_path(status):
    return custom_image(status) or DEFAULT_IMAGES_DIR / f"{status}.png"


def save_image(status, extension, content):
    """Grava data/recharge/<status>.<extensão>, apagando a imagem anterior do nível."""
    extension = extension.lower().lstrip(".")
    if extension not in IMAGE_TYPES:
        raise ValueError(f"Formato não suportado: {extension}")
    remove_image(status)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    (IMAGES_DIR / f"{status}.{extension}").write_bytes(content)


def remove_image(status):
    for path in IMAGES_DIR.glob(f"{status}.*"):
        path.unlink()


def image_crop(status):
    """Recorte salvo para a imagem do nível, ou None."""
    crop = load().get("images", {}).get(str(status), {}).get("crop")
    return crop if is_valid_crop(crop) else None


def is_valid_crop(crop):
    """[esquerda, topo, largura, altura] em frações, com a moldura dentro da imagem."""
    if not (isinstance(crop, list) and len(crop) == 4
            and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in crop)):
        return False
    left, top, width, height = crop
    # Folga de 0,001 para arredondamentos do componente de recorte.
    return (left >= 0 and top >= 0 and width > 0 and height > 0
            and left + width <= 1.001 and top + height <= 1.001)


def clamp_crop(crop):
    """Traz para dentro da imagem uma moldura que passou da borda (o componente às vezes
    devolve um pouco além do limite). Frações arredondadas em 4 casas."""
    left, top = (min(max(value, 0), 1) for value in crop[:2])
    width, height = min(crop[2], 1 - left), min(crop[3], 1 - top)
    return [round(value, 4) for value in (left, top, width, height)]


def fit_crop(crop, size, ratio=IMAGE_RATIO):
    """Ajusta ao formato ratio uma moldura salva em outro formato, na imagem de tamanho size:
    mantém o centro e a largura e muda só a altura (de 16:9 para 3:2, mostra um pouco mais
    acima e abaixo). Se a altura não couber na imagem, usa a altura toda e estreita.
    Uma moldura que já está no formato volta igual."""
    width, height = size
    left, top = crop[0] * width, crop[1] * height
    crop_width, crop_height = crop[2] * width, crop[3] * height
    target = ratio[0] / ratio[1]
    new_width, new_height = crop_width, crop_width / target
    if new_height > height:
        new_width, new_height = height * target, height
    # Mesmo centro, sem passar das bordas da imagem.
    new_left = min(max(left + (crop_width - new_width) / 2, 0), width - new_width)
    new_top = min(max(top + (crop_height - new_height) / 2, 0), height - new_height)
    return [new_left / width, new_top / height, new_width / width, new_height / height]


def default_crop(size, ratio=IMAGE_RATIO):
    """Maior moldura centralizada no formato ratio, em frações.
    É o mesmo trecho que o CSS mostra quando não há recorte salvo."""
    width, height = size
    target = ratio[0] / ratio[1]
    if width / height > target:
        fraction = height * target / width
        return [(1 - fraction) / 2, 0, fraction, 1]
    fraction = width / target / height
    return [0, (1 - fraction) / 2, 1, fraction]


def crop_pixels(crop, size):
    """Frações -> caixa do Pillow (x0, y0, x1, y1) em pixels, limitada à imagem."""
    width, height = size
    left, top, crop_width, crop_height = crop
    return (round(left * width), round(top * height),
            min(width, round((left + crop_width) * width)), min(height, round((top + crop_height) * height)))


def apply_colors(groups, overrides):
    """Copia de groups com as cores personalizadas; cor inválida (fora de #rrggbb) é ignorada."""
    merged = {}
    for name, info in groups.items():
        color = overrides.get(name)
        valid = isinstance(color, str) and HEX_COLOR.fullmatch(color)
        merged[name] = {**info, "color": color} if valid else info
    return merged


def apply_levels(levels, overrides):
    """Copia de levels com os textos personalizados. As chaves do JSON são texto ("3");
    campos desconhecidos ou vazios são ignorados (o campo fica com o padrão)."""
    merged = {}
    for status, texts in levels.items():
        custom = overrides.get(str(status), {})
        merged[status] = {
            field: custom[field] if isinstance(custom.get(field), str) and custom[field].strip() else default
            for field, default in texts.items()
        }
    return merged
