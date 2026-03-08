#!/usr/bin/env python3
"""
Gulf Watch Telegram Scraper
Fetches messages from government Telegram channels
Uses official Telegram API (Telethon)
"""
import json
import os
import re
from datetime import datetime, timezone, timedelta
from typing import List, Dict

# Government Telegram channels to monitor
TELEGRAM_CHANNELS = {
    # UAE
    'uae': [
        {'channel': 'moiuae', 'name': 'UAE Ministry of Interior', 'country': 'UAE', 'credibility': 100},
        {'channel': 'NCEMAUAE', 'name': 'UAE National Emergency', 'country': 'UAE', 'credibility': 100},
        {'channel': 'modgovae', 'name': 'UAE Ministry of Defence', 'country': 'UAE', 'credibility': 100},
        {'channel': 'wamnews', 'name': 'WAM News Agency', 'country': 'UAE', 'credibility': 95},
    ],
    # Saudi Arabia
    'saudi': [
        {'channel': 'saudimoi', 'name': 'Saudi Ministry of Interior', 'country': 'Saudi Arabia', 'credibility': 100},
        {'channel': 'SaudiDCD', 'name': 'Saudi Civil Defense', 'country': 'Saudi Arabia', 'credibility': 100},
        {'channel': 'SPAregions', 'name': 'Saudi Press Agency', 'country': 'Saudi Arabia', 'credibility': 95},
    ],
    # Qatar
    'qatar': [
        {'channel': 'MOI_Qatar', 'name': 'Qatar Ministry of Interior', 'country': 'Qatar', 'credibility': 100},
        {'channel': 'civildefenceqa', 'name': 'Qatar Civil Defence', 'country': 'Qatar', 'credibility': 100},
        {'channel': 'QatarNewsAgency', 'name': 'Qatar News Agency', 'country': 'Qatar', 'credibility': 95},
    ],
    # Bahrain
    'bahrain': [
        {'channel': 'moi_bahrain', 'name': 'Bahrain Ministry of Interior', 'country': 'Bahrain', 'credibility': 100},
        {'channel': 'bahraindefence', 'name': 'Bahrain Defence Force', 'country': 'Bahrain', 'credibility': 100},
    ],
    # Kuwait
    'kuwait': [
        {'channel': 'moi_kuwait', 'name': 'Kuwait Ministry of Interior', 'country': 'Kuwait', 'credibility': 100},
        {'channel': 'kff_kw', 'name': 'Kuwait Fire Force', 'country': 'Kuwait', 'credibility': 100},
    ],
    # Israel
    'israel': [
        {'channel': 'idfhebrew', 'name': 'IDF Hebrew', 'country': 'Israel', 'credibility': 95},
        {'channel': 'IDFarabic', 'name': 'IDF Arabic', 'country': 'Israel', 'credibility': 95},
    ],
}

# Security keywords to filter messages
SECURITY_KEYWORDS = [
    'missile', 'rocket', 'drone', 'uav', 'air defense', 'interceptor',
    'attack', 'strike', 'explosion', 'bomb', 'threat', 'hostile',
    'enemy', 'military', 'defense', 'security', 'alert', 'warning',
    'siren', 'evacuation', 'interception', 'حريق', 'انفجار', 'هجوم',
    'صاروخ', 'طائرة', 'مسيرة', 'دفاع', 'تحذير', 'إنذار',
]

def is_security_related(text: str) -> bool:
    """Check if message is security-related"""
    if not text:
        return False
    text_lower = text.lower()
    return any(kw in text_lower for kw in SECURITY_KEYWORDS)

def classify_incident(text: str) -> str:
    """Classify incident type"""
    text_lower = text.lower()
    
    if any(k in text_lower for k in ['missile', 'rocket', 'صاروخ']):
        return 'missile'
    if any(k in text_lower for k in ['drone', 'uav', 'مسيرة']):
        return 'drone'
    if any(k in text_lower for k in ['air defense', 'interceptor', 'دفاع']):
        return 'air_defense'
    if any(k in text_lower for k in ['explosion', 'blast', 'bomb', 'انفجار']):
        return 'explosion'
    if any(k in text_lower for k in ['siren', 'alert', 'warning', 'تحذير']):
        return 'alert'
    if any(k in text_lower for k in ['attack', 'strike', 'هجوم', 'قصف']):
        return 'attack'
    
    return 'security'

def extract_location(text: str, country: str) -> Dict:
    """Extract location from text"""
    cities = {
        'dubai': ('Dubai', 'UAE'),
        'abu dhabi': ('Abu Dhabi', 'UAE'),
        'riyadh': ('Riyadh', 'Saudi Arabia'),
        'jeddah': ('Jeddah', 'Saudi Arabia'),
        'doha': ('Doha', 'Qatar'),
        'manama': ('Manama', 'Bahrain'),
        'kuwait': ('Kuwait City', 'Kuwait'),
        'tel aviv': ('Tel Aviv', 'Israel'),
        'jerusalem': ('Jerusalem', 'Israel'),
        'gaza': ('Gaza', 'Palestine'),
    }
    
    text_lower = text.lower()
    for city_key, (city_name, city_country) in cities.items():
        if city_key in text_lower:
            return {'name': city_name, 'country': city_country}
    
    return {'name': 'Unknown', 'country': country}

async def fetch_telegram_messages(channel: str, name: str, country: str, credibility: int) -> List[Dict]:
    """Fetch recent messages from a Telegram channel"""
    posts = []
    
    try:
        from telethon import TelegramClient
        from telethon.tl.types import Message
        
        # Initialize client
        api_id = int(os.environ.get('TELEGRAM_API_ID', '0'))
        api_hash = os.environ.get('TELEGRAM_API_HASH', '')
        session_string = os.environ.get('TELEGRAM_SESSION', '')
        
        if not api_id or not api_hash:
            print(f"   ❌ Missing Telegram API credentials")
            return posts
        
        # Use session string if available, otherwise use session file
        if session_string:
            from telethon.sessions import StringSession
            client = TelegramClient(StringSession(session_string), api_id, api_hash)
        else:
            client = TelegramClient('gulfwatch_session', api_id, api_hash)
        
        await client.connect()
        
        if not await client.is_user_authorized():
            print(f"   ❌ Not authorized. Run locally first to generate session.")
            await client.disconnect()
            return posts
        
        # Get channel entity
        try:
            entity = await client.get_entity(channel)
        except Exception as e:
            print(f"   ❌ Cannot access channel @{channel}: {e}")
            await client.disconnect()
            return posts
        
        # Get last 20 messages
        async for message in client.iter_messages(entity, limit=20):
            if not message.text:
                continue
            
            # Check if within last 48 hours
            msg_date = message.date.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) - msg_date > timedelta(hours=48):
                continue
            
            # Filter for security-related content
            if not is_security_related(message.text):
                continue
            
            # Extract location
            location = extract_location(message.text, country)
            
            # Build post URL
            post_url = f"https://t.me/{channel}/{message.id}"
            
            post_data = {
                'id': f"{channel}_{message.id}",
                'title': message.text[:200] if message.text else f"Message from {name}",
                'source': f"Telegram - {name}",
                'source_url': post_url,
                'published': msg_date.isoformat(),
                'type': classify_incident(message.text),
                'status': 'confirmed',
                'location': location,
                'credibility': credibility,
                'is_government': True,
            }
            
            posts.append(post_data)
            print(f"   ✅ {message.text[:60]}..." if message.text else f"   ✅ Message from {name}")
        
        await client.disconnect()
        
        # Print session string for GitHub Actions
        if not session_string and hasattr(client, 'session'):
            session_str = client.session.save()
            print(f"   🔑 Session string (save to TELEGRAM_SESSION env var):")
            print(f"   {session_str[:50]}...")
        
    except Exception as e:
        print(f"   ❌ Error fetching @{channel}: {str(e)[:50]}")
    
    return posts

async def fetch_all_telegram():
    """Fetch from all Telegram channels"""
    print("📱 Gulf Watch Telegram Scraper")
    print("=" * 60)
    print(f"⏰ {datetime.now(timezone.utc).isoformat()} UTC")
    print()
    
    all_posts = []
    
    for country, channels in TELEGRAM_CHANNELS.items():
        print(f"\n🏛️ {country.upper()}")
        print("-" * 40)
        
        for ch in channels:
            print(f"📡 @{ch['channel']}...")
            posts = await fetch_telegram_messages(
                ch['channel'],
                ch['name'],
                ch['country'],
                ch['credibility']
            )
            all_posts.extend(posts)
            if posts:
                print(f"   Found {len(posts)} security-related messages")
    
    # Deduplicate
    seen = set()
    unique = []
    for post in all_posts:
        key = post['title'].lower()[:50]
        if key not in seen:
            seen.add(key)
            unique.append(post)
    
    # Sort by date
    unique.sort(key=lambda x: x['published'], reverse=True)
    
    # Generate output
    output = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'total_incidents': len(unique),
        'source': 'telegram',
        'incidents': unique
    }
    
    # Write to JSON
    os.makedirs('public', exist_ok=True)
    with open('public/telegram_incidents.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print()
    print("=" * 60)
    print(f"✅ Generated {len(unique)} unique incidents from Telegram")
    print(f"📁 Saved to public/telegram_incidents.json")

def main():
    """Main function"""
    import asyncio
    asyncio.run(fetch_all_telegram())

if __name__ == '__main__':
    main()
