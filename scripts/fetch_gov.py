#!/usr/bin/env python3
"""
Gulf Watch v2 Test - Direct Government RSS Feeds
Fetches from official government sources only (no Nitter)
"""
import feedparser
import json
import re
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional

# GOVERNMENT RSS FEEDS ONLY (Direct from official sources)
GOV_FEEDS = [
    # UAE - Official Government Sources
    {"name": "WAM - Emirates News Agency", "url": "https://wam.ae/en/rss", "country": "UAE", "credibility": 95},
    {"name": "UAE Government Portal", "url": "https://u.ae/en/about-the-uae/news.rss", "country": "UAE", "credibility": 100},
    
    # Saudi Arabia - Official Government Sources
    {"name": "Saudi Press Agency (SPA)", "url": "http://www.spa.gov.sa/rss.xml", "country": "Saudi Arabia", "credibility": 95},
    
    # Qatar - Official Government Sources
    # QNA RSS URL to be determined
]

# Security/threat keywords
KEYWORDS = [
    'missile', 'rocket', 'drone', 'uav', 'air defense', 'interceptor',
    'attack', 'strike', 'explosion', 'blast', 'bomb', 'shelling',
    'siren', 'alert', 'warning', 'evacuation', 'shelter',
    'hostile', 'enemy', 'threat', 'incursion', 'infiltration',
    'casualties', 'killed', 'wounded', 'injured', 'dead',
    'idf', 'gaza', 'hamas', 'hezbollah', 'houthi',
    'iran', 'israel', 'palestine', 'lebanon', 'syria',
    'gulf', 'uae', 'saudi', 'qatar', 'bahrain', 'kuwait', 'oman',
    'yemen', 'iraq', 'jordan', 'egypt', 'turkey',
]

# Location extraction
CITIES = {
    'dubai': ('Dubai', 'UAE', 25.2048, 55.2708),
    'abu dhabi': ('Abu Dhabi', 'UAE', 24.4539, 54.3773),
    'riyadh': ('Riyadh', 'Saudi Arabia', 24.7136, 46.6753),
    'jeddah': ('Jeddah', 'Saudi Arabia', 21.4858, 39.1925),
    'doha': ('Doha', 'Qatar', 25.2854, 51.5310),
    'manama': ('Manama', 'Bahrain', 26.2285, 50.5860),
    'kuwait city': ('Kuwait City', 'Kuwait', 29.3759, 47.9774),
    'muscat': ('Muscat', 'Oman', 23.5880, 58.3829),
    'tel aviv': ('Tel Aviv', 'Israel', 32.0853, 34.7818),
    'jerusalem': ('Jerusalem', 'Israel', 31.7683, 35.2137),
    'gaza': ('Gaza', 'Palestine', 31.5017, 34.4668),
    'beirut': ('Beirut', 'Lebanon', 33.8938, 35.5018),
    'damascus': ('Damascus', 'Syria', 33.5138, 36.2765),
    'baghdad': ('Baghdad', 'Iraq', 33.3152, 44.3661),
    'cairo': ('Cairo', 'Egypt', 30.0444, 31.2357),
    'amman': ('Amman', 'Jordan', 31.9454, 35.9284),
    'tehran': ('Tehran', 'Iran', 35.6892, 51.3890),
    'sanaa': ('Sanaa', 'Yemen', 15.3694, 44.1910),
}

def extract_location(text: str) -> Optional[Dict]:
    """Extract location from text"""
    text_lower = text.lower()
    
    for city_key, (city_name, country, lat, lng) in CITIES.items():
        if city_key in text_lower:
            return {'name': city_name, 'country': country, 'lat': lat, 'lng': lng}
    
    # Check for country names
    countries = {
        'uae': ('Unknown City', 'UAE', 23.4241, 53.8478),
        'united arab emirates': ('Unknown City', 'UAE', 23.4241, 53.8478),
        'saudi': ('Unknown City', 'Saudi Arabia', 23.8859, 45.0792),
        'qatar': ('Unknown City', 'Qatar', 25.3548, 51.1839),
    }
    
    for country_key, (city_name, country, lat, lng) in countries.items():
        if country_key in text_lower:
            return {'name': city_name, 'country': country, 'lat': lat, 'lng': lng}
    
    return None

def classify_incident(text: str) -> str:
    """Classify incident type"""
    text_lower = text.lower()
    
    if any(k in text_lower for k in ['missile', 'rocket']):
        return 'missile'
    if any(k in text_lower for k in ['drone', 'uav']):
        return 'drone'
    if any(k in text_lower for k in ['air defense', 'interceptor']):
        return 'air_defense'
    if any(k in text_lower for k in ['explosion', 'blast', 'bomb']):
        return 'explosion'
    if any(k in text_lower for k in ['siren', 'alert', 'warning']):
        return 'alert'
    if any(k in text_lower for k in ['attack', 'strike']):
        return 'attack'
    
    return 'security'

def determine_status(text: str) -> str:
    """Determine incident status"""
    text_lower = text.lower()
    
    if any(k in text_lower for k in ['confirmed', 'official', 'verify']):
        return 'confirmed'
    if any(k in text_lower for k in ['reported', 'claim', 'alleged']):
        return 'reported'
    
    return 'unconfirmed'

def is_threat_related(text: str) -> bool:
    """Check if article is threat-related"""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in KEYWORDS)

def parse_date(entry) -> Optional[datetime]:
    """Parse date from RSS entry"""
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    if hasattr(entry, 'updated_parsed') and entry.updated_parsed:
        return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
    return None

def time_ago(published) -> str:
    """Convert datetime to relative time"""
    if not published:
        return 'Unknown'
    
    now = datetime.now(timezone.utc)
    diff = now - published
    
    if diff.days > 0:
        return f"{diff.days}d ago"
    elif diff.seconds >= 3600:
        hours = diff.seconds // 3600
        return f"{hours}h ago"
    elif diff.seconds >= 60:
        mins = diff.seconds // 60
        return f"{mins}m ago"
    else:
        return "Just now"

def fetch_feed(feed_info: Dict) -> List[Dict]:
    """Fetch and parse single RSS feed"""
    incidents = []
    
    try:
        print(f"📡 Fetching {feed_info['name']}...")
        feed = feedparser.parse(feed_info['url'])
        
        if hasattr(feed, 'bozo_exception'):
            print(f"   ⚠️ Feed warning: {feed.bozo_exception}")
        
        # Process last 20 entries
        for entry in feed.entries[:20]:
            title = entry.get('title', '')
            
            # Skip if not threat-related
            if not is_threat_related(title):
                continue
            
            # Parse date
            published = parse_date(entry)
            if not published:
                published = datetime.now(timezone.utc)
            
            # Skip if older than 72 hours
            if datetime.now(timezone.utc) - published > timedelta(hours=72):
                continue
            
            # Extract location
            location = extract_location(title)
            if not location:
                location = {
                    'name': 'Unknown',
                    'country': feed_info['country'],
                    'lat': 25.0,
                    'lng': 45.0
                }
            
            # Create incident
            incident = {
                'id': hash(title + feed_info['name']) % 1000000000,
                'title': title,
                'source': feed_info['name'],
                'source_url': entry.get('link', ''),
                'published': published.isoformat(),
                'type': classify_incident(title),
                'status': determine_status(title),
                'location': location,
                'credibility': feed_info['credibility'],
                'is_government': True,
            }
            
            incidents.append(incident)
            print(f"   ✅ {title[:60]}...")
        
        print(f"   Found {len(incidents)} incidents")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    return incidents

def fetch_all():
    """Fetch all feeds and generate output"""
    print("🔄 Gulf Watch v2 Test - Government RSS Fetcher")
    print("=" * 50)
    print(f"⏰ {datetime.now(timezone.utc).isoformat()} UTC")
    print()
    
    all_incidents = []
    
    for feed in GOV_FEEDS:
        incidents = fetch_feed(feed)
        all_incidents.extend(incidents)
    
    # Sort by published date (newest first)
    all_incidents.sort(key=lambda x: x['published'], reverse=True)
    
    # Deduplicate by title similarity
    seen_titles = set()
    unique_incidents = []
    for inc in all_incidents:
        title_key = inc['title'].lower()[:50]
        if title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_incidents.append(inc)
    
    # Generate output
    output = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'total_incidents': len(unique_incidents),
        'incidents': unique_incidents
    }
    
    # Write to JSON
    with open('public/incidents.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print()
    print("=" * 50)
    print(f"✅ Generated {len(unique_incidents)} unique incidents")
    print(f"📁 Saved to public/incidents.json")

if __name__ == '__main__':
    fetch_all()
