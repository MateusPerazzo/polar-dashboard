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
# Dimensões da imagem no Insight, por nível. "Original" mostra a imagem inteira, sem corte.
IMAGE_RATIOS = ["16:9", "4:3", "1:1", "3:4", "Original"]
IMAGE_POSITIONS = {"top": "Topo", "center": "Centro", "bottom": "Base"}
IMAGE_HEIGHTS = (120, 480)
IMAGE_DEFAULTS = {"ratio": "16:9", "height": 220, "position": "center"}
HEX_COLOR = re.compile(r"#[0-9a-fA-F]{6}")


def load():
    """Devolve as personalizações salvas; {} se o arquivo não existe ou está corrompido."""
    try:
        return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save(data):
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


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


def image_style(status):
    """Formato, altura máxima e enquadramento salvos para a imagem do nível."""
    return apply_image_style(load().get("images", {}).get(str(status), {}))


def apply_image_style(custom):
    """Padrões + valores personalizados; valor fora das opções volta ao padrão."""
    low, high = IMAGE_HEIGHTS
    height = custom.get("height")
    valid = {
        "ratio": custom.get("ratio") in IMAGE_RATIOS,
        "height": isinstance(height, int) and not isinstance(height, bool) and low <= height <= high,
        "position": custom.get("position") in IMAGE_POSITIONS,
    }
    return {field: custom[field] if valid[field] else default for field, default in IMAGE_DEFAULTS.items()}


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
