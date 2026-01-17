#!/usr/bin/env python3
"""
Generate YouTube OAuth Token (run locally with browser)

This creates credentials/youtube_token.pickle which can then be
copied to the cluster for headless YouTube uploads.

Usage:
    python generate_youtube_token.py
    
After running, copy to cluster:
    scp credentials/youtube_token.pickle user@cluster:~/sknwpl-meetings/credentials/
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from transcript_tools.upload_youtube import get_authenticated_service, CREDENTIALS_DIR, TOKEN_FILE


def main():
    print("=" * 60)
    print("🔐 YouTube Token Generator")
    print("=" * 60)
    print()
    print("This will open a browser window for Google OAuth login.")
    print("After login, the token will be saved for future use.")
    print()
    print(f"Token file: {TOKEN_FILE}")
    print()
    
    # Check for client_secrets.json
    client_secrets = CREDENTIALS_DIR / "client_secrets.json"
    if not client_secrets.exists():
        print("❌ ERROR: client_secrets.json not found!")
        print()
        print("Setup instructions:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project")
        print("3. Enable 'YouTube Data API v3'")
        print("4. Go to Credentials > Create Credentials > OAuth client ID")
        print("5. Select 'Desktop app'")
        print(f"6. Download JSON and save as: {client_secrets}")
        return 1
    
    input("Press Enter to open browser for Google login...")
    
    try:
        # This will open browser and generate token
        youtube = get_authenticated_service()
        
        print()
        print("=" * 60)
        print("✅ Token generated successfully!")
        print("=" * 60)
        print()
        print(f"Token saved to: {TOKEN_FILE}")
        print()
        print("To use on cluster, copy the token file:")
        print()
        print(f"  scp {TOKEN_FILE} user@cluster:~/sknwpl-meetings/credentials/")
        print()
        print("Or if using rsync:")
        print()
        print(f"  rsync -av credentials/ user@cluster:~/sknwpl-meetings/credentials/")
        print()
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
