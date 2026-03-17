import hashlib
import os
import secrets
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

import httpx
import keyring

from whoop_cli.config import (
    AUTH_URL,
    KEYRING_ACCESS_TOKEN,
    KEYRING_REFRESH_TOKEN,
    KEYRING_SERVICE,
    REDIRECT_URI,
    SCOPES,
    TOKEN_URL,
    get_client_credentials,
)


def save_tokens(access_token: str, refresh_token: str) -> None:
    keyring.set_password(KEYRING_SERVICE, KEYRING_ACCESS_TOKEN, access_token)
    keyring.set_password(KEYRING_SERVICE, KEYRING_REFRESH_TOKEN, refresh_token)


def load_tokens() -> tuple[str | None, str | None]:
    access = keyring.get_password(KEYRING_SERVICE, KEYRING_ACCESS_TOKEN)
    refresh = keyring.get_password(KEYRING_SERVICE, KEYRING_REFRESH_TOKEN)
    return access, refresh


def clear_tokens() -> None:
    try:
        keyring.delete_password(KEYRING_SERVICE, KEYRING_ACCESS_TOKEN)
    except keyring.errors.PasswordDeleteError:
        pass
    try:
        keyring.delete_password(KEYRING_SERVICE, KEYRING_REFRESH_TOKEN)
    except keyring.errors.PasswordDeleteError:
        pass


def get_access_token() -> str | None:
    env_token = os.environ.get("WHOOP_ACCESS_TOKEN")
    if env_token:
        return env_token
    access, _ = load_tokens()
    return access


def start_oauth_flow() -> tuple[str, str]:
    """Run the full OAuth 2.0 authorization code flow with PKCE. Returns (access_token, refresh_token)."""
    client_id, client_secret = get_client_credentials()

    # PKCE
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = (
        hashlib.sha256(code_verifier.encode()).digest()
        .hex()  # not used — base64url below
    )
    import base64

    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b"=").decode()

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "scope": " ".join(SCOPES),
        "state": secrets.token_hex(16),
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    auth_url = f"{AUTH_URL}?{urlencode(params)}"
    authorization_code: str | None = None
    error_message: str | None = None

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            nonlocal authorization_code, error_message
            qs = parse_qs(urlparse(self.path).query)

            if "error" in qs:
                error_message = qs["error"][0]
                self.send_response(400)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>Authorization failed</h1><p>You can close this tab.</p>")
                return

            authorization_code = qs.get("code", [None])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<h1>Success!</h1><p>You can close this tab and return to the terminal.</p>"
            )

        def log_message(self, format: str, *args: object) -> None:
            pass  # suppress logs

    server = HTTPServer(("localhost", 8910), CallbackHandler)

    print(f"Opening browser for Whoop authorization...")
    webbrowser.open(auth_url)
    print("Waiting for callback on http://localhost:8910/callback ...")

    server.handle_request()
    server.server_close()

    if error_message:
        raise RuntimeError(f"OAuth error: {error_message}")
    if not authorization_code:
        raise RuntimeError("No authorization code received")

    # Exchange code for tokens
    response = httpx.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": REDIRECT_URI,
            "client_id": client_id,
            "client_secret": client_secret,
            "code_verifier": code_verifier,
        },
    )
    response.raise_for_status()
    data = response.json()

    access_token = data["access_token"]
    refresh_token = data["refresh_token"]
    save_tokens(access_token, refresh_token)
    return access_token, refresh_token


def refresh_access_token() -> str | None:
    """Refresh the access token using the stored refresh token. Returns new access token or None."""
    _, refresh_token = load_tokens()
    if not refresh_token:
        return None

    try:
        client_id, client_secret = get_client_credentials()
    except ValueError:
        return None

    response = httpx.post(
        TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        },
    )

    if response.status_code != 200:
        return None

    data = response.json()
    new_access = data["access_token"]
    new_refresh = data.get("refresh_token", refresh_token)
    save_tokens(new_access, new_refresh)
    return new_access
