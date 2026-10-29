import json
from datetime import date, timedelta
from pathlib import Path

import requests

BASE_URL = "https://www.polaraccesslink.com"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TOKEN_FILE = DATA_DIR / "token.json"
RAW_DIR = DATA_DIR / "raw"
MAX_KEYS_SHOWN = 15

today = date.today()
ENDPOINTS = {
    "sleep": ("/v3/users/sleep", {}),
    "nightly_recharge": ("/v3/users/nightly-recharge", {}),
    "activities": ("/v3/users/activities", {}),
    "continuous_hr": (
        "/v3/users/continuous-heart-rate",
        {"from": str(today - timedelta(days=6)), "to": str(today)},
    ),
}


def describe(value, indent=0):
    pad = "  " * indent
    if isinstance(value, dict):
        if len(value) > MAX_KEYS_SHOWN:
            print(f"{pad}dict com {len(value)} chaves")
            return
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                print(f"{pad}{key}: {type(item).__name__}")
                describe(item, indent + 1)
            else:
                print(f"{pad}{key}: {type(item).__name__}")
    elif isinstance(value, list):
        print(f"{pad}lista com {len(value)} itens; primeiro item:")
        if value:
            describe(value[0], indent + 1)


def fetch(access_token, path, params):
    return requests.get(
        BASE_URL + path,
        params=params,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        },
        timeout=30,
    )


def main():
    token = json.loads(TOKEN_FILE.read_text(encoding="utf-8"))
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    for name, (path, params) in ENDPOINTS.items():
        print(f"\n=== {name} ({path}) ===")
        response = fetch(token["access_token"], path, params)
        print(f"status: {response.status_code}")

        if response.status_code == 204:
            print("sem dados (204)")
            continue
        if response.status_code != 200:
            print(f"erro: {response.text[:200]}")
            continue

        data = response.json()
        (RAW_DIR / f"{name}.json").write_text(
            json.dumps(data, indent=2), encoding="utf-8"
        )
        describe(data)


if __name__ == "__main__":
    main()
