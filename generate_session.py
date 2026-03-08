#!/usr/bin/env python3
"""Generate Instagram session file"""
import instaloader
import base64
import os

# Login with provided credentials
L = instaloader.Instaloader(
    quiet=True,
    compress_json=False,
    download_pictures=False,
    download_videos=False,
    download_video_thumbnails=False,
)

print("Logging in as GulfWatch...")
try:
    L.login('GulfWatch', 'Folly.4Ape')
    L.save_session_to_file('.instaloader_session')
    print("✅ Session saved!")
    
    # Convert to base64
    with open('.instaloader_session', 'rb') as f:
        session_data = f.read()
        session_b64 = base64.b64encode(session_data).decode('utf-8')
    
    print(f"\n🔑 Session Base64 (add to GitHub Secrets as INSTAGRAM_SESSION_B64):")
    print(session_b64)
    
    # Save to file for reference
    with open('session_b64.txt', 'w') as f:
        f.write(session_b64)
    
    print("\n✅ Also saved to session_b64.txt")
    
except Exception as e:
    print(f"❌ Error: {e}")
