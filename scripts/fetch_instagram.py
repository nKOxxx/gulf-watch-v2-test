#!/usr/bin/env python3
"""
Gulf Watch Instagram Scraper
Fetches posts from government Instagram accounts
Runs every 30 minutes via GitHub Actions
"""
import json
import os
import re
from datetime import datetime, timezone, timedelta
from typing import List, Dict

# Government Instagram accounts to monitor
INSTAGRAM_ACCOUNTS = {
    # UAE
    'uae': [
        {'handle': 'moiuae', 'name': 'UAE Ministry of Interior', 'country': 'UAE', 'credibility': 100},
        {'handle': 'modgovae', 'name': 'UAE Ministry of Defence', 'country': 'UAE', 'credibility': 100},
        {'handle': 'NCEMAUAE', 'name': 'UAE National Emergency', 'country': 'UAE', 'credibility': 100},
        {'handle': 'Uaengc', 'name': 'UAE National Guard', 'country': 'UAE', 'credibility': 100},
        {'handle': 'UAEmediaoffice', 'name': 'UAE Government Media', 'country': 'UAE', 'credibility': 100},
        {'handle': 'wamnews', 'name': 'WAM News Agency', 'country': 'UAE', 'credibility': 95},
        {'handle': 'DXBMediaOffice', 'name': 'Dubai Media Office', 'country': 'UAE', 'credibility': 95},
        {'handle': 'CivilDefenceAD', 'name': 'Abu Dhabi Civil Defence', 'country': 'UAE', 'credibility': 100},
    ],
    # Saudi Arabia
    'saudi': [
        {'handle': 'MOISaudiArabia', 'name': 'Saudi Ministry of Interior', 'country': 'Saudi Arabia', 'credibility': 100},
        {'handle': 'SaudiDCD', 'name': 'Saudi Civil Defense', 'country': 'Saudi Arabia', 'credibility': 100},
        {'handle': 'MOD_Saudi', 'name': 'Saudi Ministry of Defence', 'country': 'Saudi Arabia', 'credibility': 100},
        {'handle': 'SPAregions', 'name': 'Saudi Press Agency', 'country': 'Saudi Arabia', 'credibility': 95},
    ],
    # Qatar
    'qatar': [
        {'handle': 'MOI_QatarEn', 'name': 'Qatar Ministry of Interior', 'country': 'Qatar', 'credibility': 100},
        {'handle': 'civildefenceqa', 'name': 'Qatar Civil Defence', 'country': 'Qatar', 'credibility': 100},
        {'handle': 'MOD_Qatar', 'name': 'Qatar Ministry of Defence', 'country': 'Qatar', 'credibility': 100},
        {'handle': 'QatarNewsAgency', 'name': 'Qatar News Agency', 'country': 'Qatar', 'credibility': 95},
    ],
    # Bahrain
    'bahrain': [
        {'handle': 'moi_bahrain', 'name': 'Bahrain Ministry of Interior', 'country': 'Bahrain', 'credibility': 100},
        {'handle': 'bahraindefence', 'name': 'Bahrain Defence Force', 'country': 'Bahrain', 'credibility': 100},
        {'handle': 'bna_bh', 'name': 'Bahrain News Agency', 'country': 'Bahrain', 'credibility': 95},
    ],
    # Kuwait
    'kuwait': [
        {'handle': 'moi_kuw_en', 'name': 'Kuwait Ministry of Interior', 'country': 'Kuwait', 'credibility': 100},
        {'handle': 'kff_kw', 'name': 'Kuwait Fire Force', 'country': 'Kuwait', 'credibility': 100},
        {'handle': 'KUNA_en', 'name': 'Kuwait News Agency', 'country': 'Kuwait', 'credibility': 95},
    ],
    # Oman
    'oman': [
        {'handle': 'RoyalOmanPolice', 'name': 'Royal Oman Police', 'country': 'Oman', 'credibility': 100},
        {'handle': 'MoDOman', 'name': 'Oman Ministry of Defence', 'country': 'Oman', 'credibility': 100},
        {'handle': 'ONA_Oman', 'name': 'Oman News Agency', 'country': 'Oman', 'credibility': 95},
    ],
    # Israel
    'israel': [
        {'handle': 'IDF', 'name': 'Israel Defense Forces', 'country': 'Israel', 'credibility': 95},
        {'handle': 'Israel_MOD', 'name': 'Israel Ministry of Defense', 'country': 'Israel', 'credibility': 95},
        {'handle': 'Mdais', 'name': 'Magen David Adom', 'country': 'Israel', 'credibility': 95},
    ],
}

# Security keywords to filter posts
SECURITY_KEYWORDS = [
    'missile', 'rocket', 'drone', 'air defense', 'interceptor',
    'attack', 'strike', 'explosion', 'bomb', 'threat',
    'hostile', 'enemy', 'military', 'defense', 'security',
    'alert', 'warning', 'siren', 'evacuation', 'interception',
    'حريق', 'انفجار', 'هجوم', 'صاروخ', 'طائرة', 'مسيرة',
]

def is_security_related(text: str) -> bool:
    """Check if post is security-related"""
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
        'kuwait city': ('Kuwait City', 'Kuwait'),
        'muscat': ('Muscat', 'Oman'),
        'tel aviv': ('Tel Aviv', 'Israel'),
        'jerusalem': ('Jerusalem', 'Israel'),
        'gaza': ('Gaza', 'Palestine'),
    }
    
    text_lower = text.lower()
    for city_key, (city_name, city_country) in cities.items():
        if city_key in text_lower:
            return {'name': city_name, 'country': city_country}
    
    return {'name': 'Unknown', 'country': country}

def fetch_instagram_posts(handle: str, name: str, country: str, credibility: int) -> List[Dict]:
    """Fetch recent posts from an Instagram account"""
    posts = []
    
    try:
        import instaloader
        
        # Initialize instaloader
        L = instaloader.Instaloader(
            quiet=True,
            compress_json=False,
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
        )
        
        # Try to load session from environment or file
        session_file = '.instaloader_session'
        if os.path.exists(session_file):
            L.load_session_from_file(os.environ.get('INSTAGRAM_USER', 'gulfwatch'), session_file)
        elif os.environ.get('INSTAGRAM_USER') and os.environ.get('INSTAGRAM_PASS'):
            L.login(os.environ['INSTAGRAM_USER'], os.environ['INSTAGRAM_PASS'])
            L.save_session_to_file(session_file)
        else:
            # Anonymous mode (limited, may fail)
            pass
        
        # Get profile
        profile = instaloader.Profile.from_username(L.context, handle)
        
        # Get last 10 posts
        for post in profile.get_posts():
            if len(posts) >= 10:
                break
            
            # Check if posted within last 48 hours
            post_date = post.date_utc
            if datetime.now(timezone.utc) - post_date > timedelta(hours=48):
                continue
            
            # Get caption
            caption = post.caption or ''
            
            # Skip if not security-related
            if not is_security_related(caption):
                continue
            
            # Extract location
            location = extract_location(caption, country)
            
            post_data = {
                'id': f"{handle}_{post.shortcode}",
                'title': caption[:200] if caption else f"Post from {name}",
                'source': f"Instagram - {name}",
                'source_url': f"https://instagram.com/p/{post.shortcode}",
                'published': post_date.isoformat(),
                'type': classify_incident(caption),
                'status': 'confirmed',
                'location': location,
                'credibility': credibility,
                'is_government': True,
                'image_url': post.url if post.url else None,
            }
            
            posts.append(post_data)
            print(f"   ✅ {caption[:60]}..." if caption else f"   ✅ Post from {name}")
            
    except Exception as e:
        print(f"   ❌ Error fetching {handle}: {str(e)[:50]}")
    
    return posts

def fetch_all_instagram():
    """Fetch from all Instagram accounts"""
    print("📸 Gulf Watch Instagram Scraper")
    print("=" * 60)
    print(f"⏰ {datetime.now(timezone.utc).isoformat()} UTC")
    print()
    
    all_posts = []
    
    for country, accounts in INSTAGRAM_ACCOUNTS.items():
        print(f"\n🏛️ {country.upper()}")
        print("-" * 40)
        
        for account in accounts:
            print(f"📡 @{account['handle']}...")
            posts = fetch_instagram_posts(
                account['handle'],
                account['name'],
                account['country'],
                account['credibility']
            )
            all_posts.extend(posts)
            if posts:
                print(f"   Found {len(posts)} security-related posts")
    
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
        'source': 'instagram',
        'incidents': unique
    }
    
    # Write to JSON
    os.makedirs('public', exist_ok=True)
    with open('public/instagram_incidents.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print()
    print("=" * 60)
    print(f"✅ Generated {len(unique)} unique incidents from Instagram")
    print(f"📁 Saved to public/instagram_incidents.json")

if __name__ == '__main__':
    fetch_all_instagram()
