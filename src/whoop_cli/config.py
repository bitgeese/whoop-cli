import os

API_BASE = "https://api.prod.whoop.com/developer"
AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
REDIRECT_URI = "http://localhost:8910/callback"
SCOPES = [
    "read:profile",
    "read:body_measurement",
    "read:cycles",
    "read:recovery",
    "read:sleep",
    "read:workout",
]
KEYRING_SERVICE = "whoop-cli"
KEYRING_ACCESS_TOKEN = "access_token"
KEYRING_REFRESH_TOKEN = "refresh_token"


def get_client_credentials() -> tuple[str, str]:
    client_id = os.environ.get("WHOOP_CLIENT_ID", "")
    client_secret = os.environ.get("WHOOP_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        raise ValueError(
            "WHOOP_CLIENT_ID and WHOOP_CLIENT_SECRET must be set. "
            "Register at https://developer.whoop.com"
        )
    return client_id, client_secret
