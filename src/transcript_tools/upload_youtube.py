"""
Moduł do uploadowania wideo na YouTube.
Wymaga konfiguracji Google Cloud i OAuth2.

SETUP:
1. Idź do https://console.cloud.google.com/
2. Stwórz nowy projekt
3. Włącz YouTube Data API v3
4. Stwórz OAuth 2.0 credentials (Desktop app)
5. Pobierz client_secrets.json i umieść w katalogu projektu
6. Przy pierwszym uruchomieniu zaloguj się przez przeglądarkę
"""

import os
import json
import pickle
from pathlib import Path
from typing import Optional
from datetime import datetime


# Ścieżki do plików credentials
CREDENTIALS_DIR = Path(__file__).parent.parent.parent / "credentials"
CLIENT_SECRETS_FILE = CREDENTIALS_DIR / "client_secrets.json"
TOKEN_FILE = CREDENTIALS_DIR / "youtube_token.pickle"


def setup_credentials_dir():
    """Tworzy katalog na credentials jeśli nie istnieje."""
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Dodaj .gitignore żeby nie commitować credentials
    gitignore = CREDENTIALS_DIR / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("*\n!.gitignore\n")


def get_authenticated_service():
    """
    Zwraca zaautentykowany serwis YouTube API.
    Przy pierwszym użyciu otworzy przeglądarkę do logowania.
    """
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
    except ImportError:
        raise ImportError(
            "Zainstaluj wymagane pakiety:\n"
            "pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client"
        )
    
    setup_credentials_dir()
    
    if not CLIENT_SECRETS_FILE.exists():
        raise FileNotFoundError(
            f"Nie znaleziono {CLIENT_SECRETS_FILE}\n\n"
            "Aby skonfigurować YouTube API:\n"
            "1. Idź do https://console.cloud.google.com/\n"
            "2. Stwórz nowy projekt\n"
            "3. Włącz 'YouTube Data API v3'\n"
            "4. Przejdź do Credentials > Create Credentials > OAuth client ID\n"
            "5. Wybierz 'Desktop app'\n"
            "6. Pobierz JSON i zapisz jako:\n"
            f"   {CLIENT_SECRETS_FILE}"
        )
    
    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
    credentials = None
    
    # Wczytaj zapisany token jeśli istnieje
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, "rb") as token:
            credentials = pickle.load(token)
    
    # Jeśli nie ma ważnych credentials, zaloguj się
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            print("🔄 Odświeżam token...")
            credentials.refresh(Request())
        else:
            print("🌐 Otwieranie przeglądarki do logowania...")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CLIENT_SECRETS_FILE), SCOPES
            )
            credentials = flow.run_local_server(port=8888)
        
        # Zapisz token na przyszłość
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(credentials, token)
        print("✅ Token zapisany")
    
    return build("youtube", "v3", credentials=credentials)


def upload_video(
    video_path: str,
    title: str,
    description: str = "",
    tags: Optional[list] = None,
    category_id: str = "22",  # 22 = People & Blogs
    privacy_status: str = "unlisted",
    notify_subscribers: bool = False,
) -> dict:
    """
    Uploaduje wideo na YouTube.
    
    Args:
        video_path: Ścieżka do pliku wideo
        title: Tytuł wideo
        description: Opis wideo
        tags: Lista tagów
        category_id: ID kategorii (22 = People & Blogs, 27 = Education)
        privacy_status: "public", "private", lub "unlisted"
        notify_subscribers: Czy powiadomić subskrybentów
    
    Returns:
        Dict z informacjami o uploadowanym wideo
    """
    try:
        from googleapiclient.http import MediaFileUpload
    except ImportError:
        raise ImportError("Zainstaluj google-api-python-client")
    
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Nie znaleziono wideo: {video_path}")
    
    youtube = get_authenticated_service()
    
    tags = tags or []
    
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
            "notifySubscribers": notify_subscribers,
        },
    }
    
    print(f"📤 Uploaduję na YouTube: {video_path.name}")
    print(f"   Tytuł: {title}")
    print(f"   Status: {privacy_status}")
    
    # Przygotuj media do uploadu
    media = MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        resumable=True,
        chunksize=10 * 1024 * 1024  # 10MB chunks
    )
    
    # Rozpocznij upload
    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media
    )
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            progress = int(status.progress() * 100)
            print(f"   Postęp: {progress}%")
    
    video_id = response["id"]
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    print(f"✅ Upload zakończony!")
    print(f"   URL: {video_url}")
    
    return {
        "video_id": video_id,
        "url": video_url,
        "title": title,
        "privacy_status": privacy_status,
    }


def generate_meeting_title(date: Optional[str] = None, topic: str = "") -> str:
    """Generuje tytuł spotkania."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    if topic:
        return f"Spotkanie SKNWPL {date} - {topic}"
    return f"Spotkanie SKNWPL {date}"


def generate_meeting_description(
    date: str,
    agenda: str = "",
    highlights: str = "",
    transcript_link: str = ""
) -> str:
    """Generuje opis spotkania dla YouTube."""
    parts = [
        f"Nagranie spotkania Sekcji Koła Naukowego z dnia {date}.",
        "",
    ]
    
    if agenda:
        parts.extend([
            "📋 AGENDA:",
            agenda,
            "",
        ])
    
    if highlights:
        parts.extend([
            "⭐ NAJWAŻNIEJSZE PUNKTY:",
            highlights,
            "",
        ])
    
    if transcript_link:
        parts.extend([
            f"📝 Pełny transkrypt: {transcript_link}",
            "",
        ])
    
    parts.extend([
        "---",
        "Automatycznie wygenerowane przez SKNWPL Meetings System",
    ])
    
    return "\n".join(parts)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Upload wideo na YouTube")
    parser.add_argument("video", help="Ścieżka do pliku wideo")
    parser.add_argument("--title", "-t", required=True, help="Tytuł wideo")
    parser.add_argument("--description", "-d", default="", help="Opis wideo")
    parser.add_argument("--tags", nargs="+", help="Tagi")
    parser.add_argument("--privacy", choices=["public", "private", "unlisted"],
                        default="unlisted", help="Status prywatności")
    
    args = parser.parse_args()
    
    result = upload_video(
        args.video,
        title=args.title,
        description=args.description,
        tags=args.tags,
        privacy_status=args.privacy,
    )
    
    print(f"\nLink do wideo: {result['url']}")

