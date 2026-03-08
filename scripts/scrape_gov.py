#!/usr/bin/env python3
"""
Gulf Watch Government Site Scraper
Reads config/sites.yaml and scrapes official government websites
Outputs structured data for verified sources
"""
import json
import yaml
import hashlib
import re
from datetime import datetime, timezone
from urllib.parse import urljoin
import urllib.request
from html.parser import HTMLParser

class SimpleScraper:
    """Lightweight scraper using regex and HTMLParser (no heavy deps)"""
    
    def __init__(self):
        self.results = []
    
    def fetch_html(self, url):
        """Fetch HTML from URL"""
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            with urllib.request.urlopen(req, timeout=15) as response:
                return response.read().decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"   ❌ Fetch error: {e}")
            return None
    
    def extract_with_regex(self, html, selectors):
        """Extract data using regex patterns based on CSS selectors"""
        items = []
        
        # Split selectors by comma and try each
        container_selectors = [s.strip() for s in selectors['container'].split(',')]
        
        for container_sel in container_selectors:
            # Convert CSS class selector to regex pattern
            if container_sel.startswith('.'):
                class_name = container_sel[1:]
                # Match <div class="...class_name..."> or <article class="...class_name...">
                pattern = rf'<(?:div|article|section|li)[^>]*class="[^"]*{class_name}[^"]*"[^>]*>(.*?)</(?:div|article|section|li)>'
            else:
                # Match tag directly
                pattern = rf'<{container_sel}[^>]*>(.*?)</{container_sel}>'
            
            matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
            
            for match in matches[:10]:  # Limit to 10 items
                item = self.parse_item(match, selectors)
                if item:
                    items.append(item)
        
        return items
    
    def parse_item(self, html_fragment, selectors):
        """Parse a single item from HTML fragment"""
        item = {}
        
        # Extract title
        title_selectors = [s.strip() for s in selectors['title'].split(',')]
        for title_sel in title_selectors:
            if title_sel.startswith('.'):
                class_name = title_sel[1:]
                match = re.search(rf'<[^>]*class="[^"]*{class_name}[^"]*"[^>]*>(.*?)</[^>]+>', html_fragment, re.DOTALL | re.IGNORECASE)
            else:
                match = re.search(rf'<{title_sel}[^>]*>(.*?)</{title_sel}>', html_fragment, re.DOTALL | re.IGNORECASE)
            
            if match:
                title = re.sub(r'<[^>]+>', '', match.group(1)).strip()
                if title:
                    item['title'] = title
                    break
        
        if 'title' not in item:
            return None
        
        # Extract link
        link_match = re.search(r'href="([^"]+)"', html_fragment)
        if link_match:
            item['link'] = link_match.group(1)
        else:
            item['link'] = ''
        
        # Extract date if available
        date_selectors = [s.strip() for s in selectors['date'].split(',')]
        for date_sel in date_selectors:
            if date_sel.startswith('.'):
                class_name = date_sel[1:]
                match = re.search(rf'<[^>]*class="[^"]*{class_name}[^"]*"[^>]*>(.*?)</[^>]+>', html_fragment, re.DOTALL | re.IGNORECASE)
            elif date_sel == 'time':
                match = re.search(r'<time[^>]*>(.*?)</time>', html_fragment, re.DOTALL | re.IGNORECASE)
            else:
                match = re.search(rf'<{date_sel}[^>]*>(.*?)</{date_sel}>', html_fragment, re.DOTALL | re.IGNORECASE)
            
            if match:
                date_str = re.sub(r'<[^>]+>', '', match.group(1)).strip()
                if date_str:
                    item['date'] = date_str
                    break
        
        return item
    
    def scrape_site(self, site_config):
        """Scrape a single site"""
        print(f"\n📡 Scraping {site_config['name']}...")
        print(f"   URL: {site_config['url']}")
        
        html = self.fetch_html(site_config['url'])
        if not html:
            return []
        
        items = self.extract_with_regex(html, site_config['selectors'])
        print(f"   Found {len(items)} items")
        
        return items

def is_security_related(text, keywords):
    """Check if text contains security keywords"""
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)

def classify_incident(text):
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
    if any(k in text_lower for k in ['siren', 'alert', 'warning', 'تحذير', 'إنذار']):
        return 'alert'
    if any(k in text_lower for k in ['attack', 'strike', 'هجوم', 'قصف']):
        return 'attack'
    
    return 'security'

def extract_location(text):
    """Extract location from text"""
    cities = {
        'dubai': ('Dubai', 'UAE', 25.2048, 55.2708),
        'abu dhabi': ('Abu Dhabi', 'UAE', 24.4539, 54.3773),
        'riyadh': ('Riyadh', 'Saudi Arabia', 24.7136, 46.6753),
        'jeddah': ('Jeddah', 'Saudi Arabia', 21.4858, 39.1925),
        'doha': ('Doha', 'Qatar', 25.2854, 51.5310),
        'manama': ('Manama', 'Bahrain', 26.2285, 50.5860),
        'kuwait city': ('Kuwait City', 'Kuwait', 29.3759, 47.9774),
        'muscat': ('Muscat', 'Oman', 23.5880, 58.3829),
    }
    
    text_lower = text.lower()
    for city_key, (city_name, country, lat, lng) in cities.items():
        if city_key in text_lower:
            return {'name': city_name, 'country': country, 'lat': lat, 'lng': lng}
    
    # Check countries
    countries = {
        'uae': ('Unknown City', 'UAE', 23.4241, 53.8478),
        'emirates': ('Unknown City', 'UAE', 23.4241, 53.8478),
        'saudi': ('Unknown City', 'Saudi Arabia', 23.8859, 45.0792),
        'qatar': ('Unknown City', 'Qatar', 25.3548, 51.1839),
    }
    
    for country_key, (city_name, country, lat, lng) in countries.items():
        if country_key in text_lower:
            return {'name': city_name, 'country': country, 'lat': lat, 'lng': lng}
    
    return {'name': 'Unknown', 'country': 'Unknown', 'lat': 25.0, 'lng': 45.0}

def main():
    """Main function"""
    print("🔄 Gulf Watch Government Site Scraper")
    print("=" * 60)
    print(f"⏰ {datetime.now(timezone.utc).isoformat()} UTC")
    print()
    
    # Load config
    with open('config/sites.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    scraper = SimpleScraper()
    all_incidents = []
    
    # Scrape each site
    for site_id, site_config in config['sites'].items():
        items = scraper.scrape_site(site_config)
        
        for item in items:
            # Filter for security-related content
            if not is_security_related(item['title'], config['security_keywords']):
                continue
            
            # Build full URL
            link = item['link']
            if link and not link.startswith('http'):
                link = urljoin(site_config['url'], link)
            
            # Extract location
            location = extract_location(item['title'])
            if site_config['country'] and location['country'] == 'Unknown':
                location['country'] = site_config['country']
            
            incident = {
                'id': hashlib.md5(f"{site_id}_{item['title']}".encode()).hexdigest()[:12],
                'title': item['title'][:200],
                'source': site_config['name'],
                'source_url': link,
                'published': datetime.now(timezone.utc).isoformat(),
                'type': classify_incident(item['title']),
                'status': 'confirmed',
                'location': location,
                'credibility': site_config['credibility'],
                'is_government': True,
            }
            
            all_incidents.append(incident)
            print(f"   ✅ {item['title'][:60]}...")
    
    # Deduplicate
    seen = set()
    unique = []
    for inc in all_incidents:
        key = inc['title'].lower()[:50]
        if key not in seen:
            seen.add(key)
            unique.append(inc)
    
    # Sort by date
    unique.sort(key=lambda x: x['published'], reverse=True)
    
    # Generate output
    output = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'total_incidents': len(unique),
        'incidents': unique
    }
    
    # Write to JSON
    with open('public/incidents.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print()
    print("=" * 60)
    print(f"✅ Generated {len(unique)} unique incidents")
    print(f"📁 Saved to public/incidents.json")

if __name__ == '__main__':
    main()
