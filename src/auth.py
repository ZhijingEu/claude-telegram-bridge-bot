"""Google OAuth2 flow and token management."""

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar"]
TASKS_SCOPES = ["https://www.googleapis.com/auth/tasks"]

_ROOT = Path(__file__).parent.parent  # project root (one level above src/)
TOKEN_PATH = _ROOT / "token.json"
TASKS_TOKEN_PATH = _ROOT / "token_tasks.json"
CREDENTIALS_PATH = _ROOT / "credentials.json"


def get_credentials(
    scopes: list[str] = None,
    token_path: Path = None,
) -> Credentials:
    """Load credentials from token file, refresh if expired, or run OAuth flow.

    Defaults to calendar.readonly scope + token.json (preserves existing behaviour).
    Pass scopes=TASKS_SCOPES and token_path=TASKS_TOKEN_PATH for Tasks auth.
    """
    if scopes is None:
        scopes = CALENDAR_SCOPES
    if token_path is None:
        token_path = TOKEN_PATH

    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                raise FileNotFoundError(
                    "credentials.json not found. Download your OAuth 2.0 client credentials "
                    "from Google Cloud Console and place them in the project root."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), scopes)
            creds = flow.run_local_server(port=0)

        token_path.write_text(creds.to_json())

    return creds
