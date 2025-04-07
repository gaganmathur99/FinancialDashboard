from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse
from backend.auth import exchange_code_for_token, get_auth_url
from backend.db import save_tokens, get_user_tokens
from backend.utils import decrypt, encrypt
import requests
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from backend.transaction_db import save_transaction, get_transactions

# Load environment variables from .env file
load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")


app = FastAPI()

# Configure CORS to allow requests from Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Allow Streamlit frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/login")
def login():
    return RedirectResponse(get_auth_url())

@app.get("/callback")
def callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")

    tokens = exchange_code_for_token(code)
    save_tokens("demo_user", tokens)
    return {"message": "Login successful"}


@app.get("/accounts")
def accounts():
    print("Fetching tokens for demo_user...")
    tokens = get_user_tokens("demo_user")
    print(f"Tokens retrieved: {tokens}")

    access_token = decrypt(tokens["access_token"])
    refresh_token = decrypt(tokens["refresh_token"])
    print(f"Access Token: {access_token}")
    print(f"Refresh Token: {refresh_token}")

    headers = {"Authorization": f"Bearer {access_token}"}
    print("Fetching accounts from TrueLayer API...")
    res = requests.get("https://api.truelayer.com/data/v1/accounts", headers=headers)
    print(f"Accounts API response status: {res.status_code}")

    # Check if the access token is expired based on the response
    if res.status_code == 401:  # Unauthorized, likely due to expired token
        print("Access token expired. Attempting to refresh...")
        refresh_url = "https://auth.truelayer.com/connect/token"
        payload = {
            "grant_type": "refresh_token",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": refresh_token,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        refresh_res = requests.post(refresh_url, data=payload, headers=headers)
        print(f"Refresh response status: {refresh_res.status_code}")
        print(f"Refresh response body: {refresh_res.text}")

        if refresh_res.status_code == 200:
            new_tokens = refresh_res.json()
            print(f"New tokens: {new_tokens}")
            access_token = new_tokens["access_token"]
            refresh_token = new_tokens["refresh_token"]
            tokens["access_token"] = encrypt(access_token)
            tokens["refresh_token"] = encrypt(refresh_token)
            save_tokens("demo_user", tokens)  # Save the updated tokens
            print("Access token refreshed successfully.")

            # Retry the accounts API request with the new access token
            headers = {"Authorization": f"Bearer {access_token}"}
            print("Retrying accounts API request with refreshed token...")
            res = requests.get("https://api.truelayer.com/data/v1/accounts", headers=headers)
            print(f"Accounts API response status: {res.status_code}")
            print(f"Accounts API response body: {res.text}")
        else:
            print("Failed to refresh access token.")
            raise HTTPException(status_code=401, detail="Failed to refresh access token")

    return res.json().get("results", [])



@app.get("/transactions")
def transactions(account_id: str, from_date: str, to_date: str):
    # Fetch tokens for the user
    tokens = get_user_tokens("demo_user")
    access_token = decrypt(tokens["access_token"])

    # Fetch transactions from the TrueLayer API
    url = f"https://api.truelayer.com/data/v1/accounts/{account_id}/transactions?from={from_date}&to={to_date}"
    res = requests.get(url, headers={"Authorization": f"Bearer {access_token}"})

    if res.status_code == 200:
        # Parse the API response
        api_transactions = res.json().get("results", [])
        print(f"Fetched transactions from API: {api_transactions}")

        # Save transactions into the database
        save_transaction("demo_user", api_transactions)

        # Retrieve transactions from the database
        db_transactions = get_transactions("demo_user")
        print(f"Retrieved transactions from database: {db_transactions}")

        return db_transactions
    else:
        # Handle API errors
        print(f"Error fetching transactions: {res.status_code} - {res.text}")
        raise HTTPException(status_code=res.status_code, detail=res.text)

@app.get("/test")
async def test():
    return {"message": "Test successful"}