import requests, urllib.parse, os
from backend.utils import encrypt

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
AUTH_URL = "https://auth.truelayer.com/"
TOKEN_URL = "https://auth.truelayer.com/connect/token"
SCOPES = "info accounts balance transactions offline_access"

def get_auth_url():
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": "secure123"
    }
    return f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

def exchange_code_for_token(code: str):
    data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "code": code
    }
    response = requests.post(TOKEN_URL, data=data)
    if response.status_code != 200:
        raise Exception(f"Failed to exchange code for token: {response.json()}")
    tokens = response.json()
    print(tokens)
    return {
        "access_token": encrypt(tokens["access_token"]),
        "refresh_token": encrypt(tokens["refresh_token"])
    }
