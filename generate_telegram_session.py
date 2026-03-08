#!/usr/bin/env python3
"""Generate Telegram session string for GitHub Actions"""
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

api_id = 37496063
api_hash = 'bc119f3b0d91b4f22973a5de7a95b11d'

print("Generating Telegram session...")
print("You'll need to enter your phone number and the code sent to your Telegram app.\n")

with TelegramClient(StringSession(), api_id, api_hash) as client:
    session_string = client.session.save()
    print(f"\n🔑 Session string generated!")
    print(f"\nAdd this to GitHub Secrets as TELEGRAM_SESSION:")
    print(f"\n{session_string}")
    
    # Save to file
    with open('telegram_session.txt', 'w') as f:
        f.write(session_string)
    print(f"\n✅ Also saved to telegram_session.txt")
