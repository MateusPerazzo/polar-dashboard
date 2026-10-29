import json
from pathlib import Path

import requests

BASE_URL = "https://www.polaraccesslink.com"
TOKEN_FILE = Path(__file__).resolve().parent.parent / "data" / "token.json"


def load_access_token():
    return json.loads(TOKEN_FILE.read_text(encoding="utf-8"))["access_token"]


def get(path, params=None):
    response = requests.get(
        BASE_URL + path,
        params=params,
        headers={
            "Authorization": f"Bearer {load_access_token()}",
            "Accept": "application/json",
        },
        timeout=30,
    )
    if response.status_code == 204:
        return None
    response.raise_for_status()
    return response.json()
