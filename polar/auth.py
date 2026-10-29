import json
import os
import secrets
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from dotenv import load_dotenv

AUTH_URL = "https://flow.polar.com/oauth2/authorization"
TOKEN_URL = "https://polarremote.com/v2/oauth2/token"
REGISTER_URL = "https://www.polaraccesslink.com/v3/users"
MEMBER_ID = "polar-dashboard-local"
ROOT = Path(__file__).resolve().parent.parent
TOKEN_FILE = ROOT / "data" / "token.json"


def load_config():
    load_dotenv(ROOT / ".env")
    config = {
        "client_id": os.getenv("POLAR_CLIENT_ID"),
        "client_secret": os.getenv("POLAR_CLIENT_SECRET"),
        "redirect_uri": os.getenv("POLAR_REDIRECT_URI"),
    }
    missing = [name for name, value in config.items() if not value]
    if missing:
        sys.exit(f"Faltando no .env: {', '.join(missing)}")
    return config


class CallbackHandler(BaseHTTPRequestHandler):
    params = {}

    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        CallbackHandler.params = {key: values[0] for key, values in query.items()}
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("Autorizado. Pode fechar esta aba.".encode("utf-8"))

    def log_message(self, format, *args):
        pass


def wait_for_code(redirect_uri, expected_state):
    port = urlparse(redirect_uri).port
    server = HTTPServer(("localhost", port), CallbackHandler)
    print(f"Aguardando a Polar chamar {redirect_uri} ...")
    server.handle_request()
    server.server_close()

    params = CallbackHandler.params
    if "error" in params:
        sys.exit(f"A Polar retornou um erro: {params['error']}")
    if params.get("state") != expected_state:
        sys.exit("O state não confere. Abortando por segurança.")
    if "code" not in params:
        sys.exit("A resposta da Polar não trouxe o code.")
    return params["code"]


def exchange_code(config, code):
    response = requests.post(
        TOKEN_URL,
        auth=(config["client_id"], config["client_secret"]),
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": config["redirect_uri"],
        },
        headers={"Accept": "application/json"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def register_user(access_token):
    response = requests.post(
        REGISTER_URL,
        json={"member-id": MEMBER_ID},
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        },
        timeout=30,
    )
    if response.status_code == 409:
        print("Usuário já estava registrado (409), seguindo.")
        return
    response.raise_for_status()
    print(f"Usuário registrado (status {response.status_code}).")


def save_token(token_data):
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    to_save = {
        "access_token": token_data["access_token"],
        "x_user_id": token_data["x_user_id"],
    }
    TOKEN_FILE.write_text(json.dumps(to_save, indent=2), encoding="utf-8")
    print(f"Token salvo em {TOKEN_FILE}")


def main():
    config = load_config()
    state = secrets.token_urlsafe(16)

    query = urlencode(
        {
            "response_type": "code",
            "client_id": config["client_id"],
            "redirect_uri": config["redirect_uri"],
            "state": state,
        }
    )
    webbrowser.open(f"{AUTH_URL}?{query}")

    code = wait_for_code(config["redirect_uri"], state)
    token_data = exchange_code(config, code)
    register_user(token_data["access_token"])
    save_token(token_data)


if __name__ == "__main__":
    main()
