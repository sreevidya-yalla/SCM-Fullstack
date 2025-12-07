import os
from authlib.integrations.starlette_client import OAuth

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8000/auth")

if not CLIENT_ID or not CLIENT_SECRET:
    print("⚠️ Google OAuth credentials missing! Check .env and docker-compose.")
else:
    print(f"🔑 Google OAuth Active | Redirect: {REDIRECT_URI}")

oauth = OAuth()

oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    client_kwargs={
        'scope': 'email openid profile',
        'redirect_uri': REDIRECT_URI
    }
)
