#!/usr/bin/env python3
"""
NewsData.io API Fetcher
Fetches MENA security news from NewsData.io API
"""
import json
import os
import requests
from datetime import datetime, timezone
from typing import List, Dict

API_KEY = os.environ.get('NEWSDATA_API_KEY')
if not API_KEY:
    print("Error: NEWSDATA_API_KEY not set")
    exit(1)

# Gulf/Middle East countries to monitor
COUNTRIES = [
    'ae',  # UAE
    'sa',  # Saudi Arabia
    'qa',  # Qatar
    'kw',  # Kuwait
    'bh',  # Bahrain
    'om',  # Oman
    'iq',  # Iraq
    'jo',  # Jordan
    'lb',  # Lebanon
    'eg',  # Egypt
    'tr',  # Turkey
    'ir',  # Iran
]

# Security keywords
KEYWORDS = [
    'missile', 'rocket', 'drone', 'uav', 'air defense', 'interceptor',
    'attack', 'strike', 'explosion', 'bomb', 'threat', 'hostile',
    'military', 'defense', 'security', 'alert', 'warning',
    'iran', 'israel', 'gaza', 'hamas', 'hezbollah', 'houthi'
]

def fetch_newsdata(country: str) -> List[Dict]:
    """Fetch news from NewsData.io for a specific country"""
    url = 'https://newsdata.io/api/1/news'
    
    params = {
        'apikey': API_KEY,
        'country': country,
        'language': 'en',
        'category': 'world',
        'q': ' OR '.join(KEYWORDS[:5]),  # Use top 5 keywords
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') != 'success':
            print(f"Error for {country}: {data.get('results', {}).get('message', 'Unknown error')}")
            return []
        
        return data.get('results', [])
        
    except Exception as e:
        print(f"Error fetching {country}: {e}")
        return []

def convert_to_incident(article: Dict, country_code: str) -> Dict:
    """Convert NewsData article to Gulf Watch incident format"""
    
    # Map country code to name
    country_names = {
        'ae': ('UAE', 25.2048, 55.2708),
        'sa': ('Saudi Arabia', 24.7136, 46.6753),
        'qa': ('Qatar', 25.2854, 51.5310),
        'kw': ('Kuwait', 29.3759, 47.9774),
        'bh': ('Bahrain', 26.2285, 50.5860),
        'om': ('Oman', 23.5880, 58.3829),
        'iq': ('Iraq', 33.3152, 44.3661),
        'jo': ('Jordan', 31.9454, 35.9284),
        'lb': ('Lebanon', 33.8938, 35.5018),
        'eg': ('Egypt', 30.0444, 31.2357),
        'tr': ('Turkey', 38.9637, 35.2433),
        'ir': ('Iran', 32.4279, 53.6880),
    }
    
    country_name, lat, lng = country_names.get(country_code, ('Unknown', 0, 0))
    
    # Parse date
    pub_date = article.get('pubDate', '')
    try:
        published = datetime.strptime(pub_date, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc).isoformat()
    except:
        published = datetime.now(timezone.utc).isoformat()
    
    # Determine type based on keywords
    title_lower = article.get('title', '').lower()
    if any(k in title_lower for k in ['missile', 'rocket', 'drone']):
        incident_type = 'missile'
    elif any(k in title_lower for k in ['attack', 'strike', 'explosion']):
        incident_type = 'attack'
    else:
        incident_type = 'security'
    
    return {
        'id': f"newsdata_{article.get('article_id', '')}",
        'title': article.get('title', ''),
        'source': f"NewsData.io - {article.get('source_name', 'Unknown')}",
        'source_url': article.get('link', ''),
        'published': published,
        'type': incident_type,
        'status': 'reported',
        'location': {
            'name': country_name,
            'country': country_name,
            'lat': lat,
            'lng': lng
        },
        'credibility': 70,  # News API sources
        'is_government': False,
        'source_key': 'newsdata'
    }

def main():
    all_incidents = []
    
    for country in COUNTRIES:
        print(f"Fetching news for {country}...")
        articles = fetch_newsdata(country)
        
        for article in articles:
            incident = convert_to_incident(article, country)
            all_incidents.append(incident)
        
        print(f"  Found {len(articles)} articles")
    
    # Sort by date
    all_incidents.sort(key=lambda x: x['published'], reverse=True)
    
    # Save output
    output = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'total_incidents': len(all_incidents),
        'incidents': all_incidents
    }
    
    with open('public/newsdata_incidents.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\nTotal: {len(all_incidents)} incidents saved")

if __name__ == '__main__':
    main()
