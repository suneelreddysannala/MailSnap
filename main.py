# ✅ Keep all imports
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from summarizer import summarize_email
import os, base64

load_dotenv()
app = FastAPI()

# ✅ Your routes come BEFORE mounting
summaries_cache = {}

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

flow = Flow.from_client_secrets_file(
    'credentials.json',
    scopes=SCOPES,
    redirect_uri='http://localhost:8000/auth/callback'
)

@app.get("/auth")
def auth():
    auth_url, _ = flow.authorization_url(prompt='consent')
    return RedirectResponse(auth_url)

@app.get("/auth/callback")
def callback(request: Request):
    flow.fetch_token(authorization_response=str(request.url))
    creds = flow.credentials
    service = build('gmail', 'v1', credentials=creds)

    messages = service.users().messages().list(
        userId='me', maxResults=5, q="is:unread"
    ).execute().get('messages', [])

    summary_map = {}
    for i, msg in enumerate(messages):
        full = service.users().messages().get(
            userId='me', id=msg['id'], format='full'
        ).execute()
        
        parts = full['payload'].get('parts', [])
        body = ''
        for part in parts:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data')
                if data:
                    body = base64.urlsafe_b64decode(data.encode()).decode()
                break

        summary = summarize_email(body, f"email{i+1}")
        print("summary issssssss", summary)

        if isinstance(summary, dict):
            summary_map.update(summary)
        else:
            print("⚠️ Summary not a dict:", summary)

    # ✅ Move this outside the loop to store all summaries
    summaries_cache["latest"] = summary_map

    return RedirectResponse(url="/index.html?done=true")

@app.get("/summaries")
def get_summaries():
    return {"summaries": summaries_cache.get("latest", {})}

# ✅ Mount static files LAST so they don’t override route handling
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
