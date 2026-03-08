#!/usr/bin/env python3
"""
Gulf Watch RSS.app Scraper
Fetches from RSS.app feeds (Twitter/X via RSS)
"""
import json
import os
import re
import feedparser
from datetime import datetime, timezone, timedelta
from typing import List, Dict

# RSS.app feeds from Twitter/X government accounts
# IMPORTANT: Use the .xml URLs, not the dashboard URLs

RSS_APP_FEEDS = {
    # UAE (8 accounts)
    'moiuae': {'url': 'https://rss.app/feeds/oPyw4FJ41usBjG0c.xml', 'name': 'UAE Ministry of Interior', 'country': 'UAE', 'credibility': 100},
    'moduae': {'url': 'https://rss.app/feeds/5DzID481Msg3w5Go.xml', 'name': 'UAE Ministry of Defence', 'country': 'UAE', 'credibility': 100},
    'ncemauae': {'url': 'https://rss.app/feeds/t0JvfszuALDyg4uh.xml', 'name': 'UAE National Emergency', 'country': 'UAE', 'credibility': 100},
    'uaengc': {'url': 'https://rss.app/feeds/oqxMcPt6uwJ10D0K.xml', 'name': 'UAE National Guard', 'country': 'UAE', 'credibility': 100},
    'uaemediaoffice': {'url': 'https://rss.app/feeds/DKefnWqLQ6ipghtp.xml', 'name': 'UAE Government Media', 'country': 'UAE', 'credibility': 100},
    'wamnews': {'url': 'https://rss.app/feeds/yWxDexVK5P5WlnV9.xml', 'name': 'WAM News Agency', 'country': 'UAE', 'credibility': 95},
    'dxbmediaoffice': {'url': 'https://rss.app/feeds/OTlOJkkZ297qnQNn.xml', 'name': 'Dubai Media Office', 'country': 'UAE', 'credibility': 95},
    'civildefencead': {'url': 'https://rss.app/feeds/Da5ZvV4gQsJYMJja.xml', 'name': 'Abu Dhabi Civil Defence', 'country': 'UAE', 'credibility': 100},
    
    # Saudi Arabia (2 accounts)
    'moisaudiarabia': {'url': 'https://rss.app/feeds/8Qxm8tjO1nBYaMhl.xml', 'name': 'Saudi Ministry of Interior', 'country': 'Saudi Arabia', 'credibility': 100},
    'saudidcd': {'url': 'https://rss.app/feeds/53nS4uUWlgrreFsJ.xml', 'name': 'Saudi Civil Defense', 'country': 'Saudi Arabia', 'credibility': 100},
    
    # Qatar (4 accounts)
    'moiqataren': {'url': 'https://rss.app/feeds/RyXjTtNHU7MscSDx.xml', 'name': 'Qatar Ministry of Interior', 'country': 'Qatar', 'credibility': 100},
    'civildefenceqa': {'url': 'https://rss.app/feeds/Gv74vCuEmr7jMI8S.xml', 'name': 'Qatar Civil Defence', 'country': 'Qatar', 'credibility': 100},
    'modqatar': {'url': 'https://rss.app/feeds/J9LSu9US4gNAoWuG.xml', 'name': 'Qatar Ministry of Defence', 'country': 'Qatar', 'credibility': 100},
    'qatarnewsagency': {'url': 'https://rss.app/feeds/MbUvCNXci4r8R6tT.xml', 'name': 'Qatar News Agency', 'country': 'Qatar', 'credibility': 95},
    
    # Bahrain (1 account)
    'moibahrain': {'url': 'https://rss.app/feeds/RGESjvd3KiLouQ1Q.xml', 'name': 'Bahrain Ministry of Interior', 'country': 'Bahrain', 'credibility': 100},
    
    # Kuwait (2 accounts)
    'kffkw': {'url': 'https://rss.app/feeds/WzsZIKALXFycSVCA.xml', 'name': 'Kuwait Fire Force', 'country': 'Kuwait', 'credibility': 100},
    'kunaen': {'url': 'https://rss.app/feeds/pMqH90ylFHYmpPF2.xml', 'name': 'Kuwait News Agency', 'country': 'Kuwait', 'credibility': 95},
    
    # Oman (1 account)
    'royalomanpolice': {'url': 'https://rss.app/feeds/YHfnfinoL5JV1J7T.xml', 'name': 'Royal Oman Police', 'country': 'Oman', 'credibility': 100},
    
    # Israel (2 accounts)
    'israelmod': {'url': 'https://rss.app/feeds/ONFaZNztIulPvZDc.xml', 'name': 'Israel Ministry of Defense', 'country': 'Israel', 'credibility': 95},
    'mdais': {'url': 'https://rss.app/feeds/ySovRTttsScjix9r.xml', 'name': 'Magen David Adom', 'country': 'Israel', 'credibility': 95},
    
    # Iran (2 accounts)
    'mehrnews': {'url': 'https://rss.app/feeds/iBfZthMj9m7d99uN.xml', 'name': 'Mehr News Agency', 'country': 'Iran', 'credibility': 85},
    'farsnews': {'url': 'https://rss.app/feeds/9X7fSoVOaiZHtOr6.xml', 'name': 'Fars News Agency', 'country': 'Iran', 'credibility': 85},
}

# Security keywords
SECURITY_KEYWORDS = [
    'missile', 'rocket', 'drone', 'uav', 'air defense', 'interceptor',
    'attack', 'strike', 'explosion', 'bomb', 'threat', 'hostile',
    'enemy', 'military', 'defense', 'security', 'alert', 'warning',
    'siren', 'evacuation', 'interception', 'casualties', 'killed',
    'wounded', 'houthi', 'hamas', 'hezbollah', 'gaza', 'idf',
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
        'beirut': ('Beirut', 'Lebanon'),
    }
    
    text_lower = text.lower()
    for city_key, (city_name, city_country) in cities.items():
        if city_key in text_lower:
            return {'name': city_name, 'country': city_country}
    
    return {'name': 'Unknown', 'country': country}

def fetch_rss_feed(feed_id: str, feed_config: dict) -> List[Dict]:
    """Fetch posts from an RSS.app feed"""
    posts = []
    
    try:
        print(f"📡 Fetching {feed_config['name']}...")
        feed = feedparser.parse(feed_config['url'])
        
        if hasattr(feed, 'bozo_exception'):
            print(f"   ⚠️ Feed warning: {feed.bozo_exception}")
        
        # Process entries
        for entry in feed.entries[:20]:  # Last 20 entries
            title = entry.get('title', '')
            
            # Skip if not security-related
            if not is_security_related(title):
                continue
            
            # Parse date
            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
            
            if not published:
                published = datetime.now(timezone.utc)
            
            # Skip if older than 48 hours
            if datetime.now(timezone.utc) - published > timedelta(hours=48):
                continue
            
            # Extract location
            location = extract_location(title, feed_config['country'])
            
            post_data = {
                'id': f"rss_{feed_id}_{hash(title) % 1000000000}",
                'title': title[:200],
                'source': f"Twitter - {feed_config['name']}",
                'source_url': entry.get('link', ''),
                'published': published.isoformat(),
                'type': classify_incident(title),
                'status': 'confirmed',
                'location': location,
                'credibility': feed_config['credibility'],
                'is_government': True,
            }
            
            posts.append(post_data)
            print(f"   ✅ {title[:60]}...")
        
        print(f"   Found {len(posts)} security-related posts")
        
    except Exception as e:
        print(f"   ❌ Error fetching {feed_config['name']}: {str(e)[:50]}")
    
    return posts

def fetch_all_rss():
    """Fetch from all RSS feeds"""
    print("📱 Gulf Watch RSS.app Scraper")
    print("=" * 60)
    print(f"⏰ {datetime.now(timezone.utc).isoformat()} UTC")
    print()
    
    all_posts = []
    
    for feed_id, feed_config in RSS_APP_FEEDS.items():
        posts = fetch_rss_feed(feed_id, feed_config)
        all_posts.extend(posts)
    
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
        'source': 'rss_app',
        'incidents': unique
    }
    
    # Write to JSON
    os.makedirs('public', exist_ok=True)
    with open('public/rss_incidents.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print()
    print("=" * 60)
    print(f"✅ Generated {len(unique)} unique incidents from RSS")
    print(f"📁 Saved to public/rss_incidents.json")

if __name__ == '__main__':
    fetch_all_rss()
