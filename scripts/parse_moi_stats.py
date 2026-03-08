#!/usr/bin/env python3
"""
UAE Missile Stats Parser
Extracts interception statistics from @moiuae RSS feed
"""
import feedparser
import json
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

# RSS feed URL
MOI_UAE_FEED = 'https://rss.app/feeds/oPyw4FJ41usBjG0c.xml'

def extract_numbers_from_text(text: str) -> Dict[str, int]:
    """Extract missile/drone counts from tweet text - UAE MoI specific format"""
    stats = {
        'ballistic_detected': 0,
        'ballistic_intercepted': 0,
        'cruise_detected': 0,
        'cruise_intercepted': 0,
        'drones_detected': 0,
        'drones_intercepted': 0,
        'impacted': 0,
        'killed': 0,
        'injured': 0
    }
    
    # UAE MoI format analysis:
    # "رصدت ... 17 صاروخ باليستي ... تم تدمير 16 صاروخ باليستي ... سقط 1 صاروخ"
    # "تم رصد 117 طائرة مسيرة ... تم اعتراض 113 طائرة مسيرة ... سقطت 4"
    
    # Strategy: Split text by keywords to isolate sections
    
    # Ballistic missiles
    # Detection section: between "رصدت" and "تم تدمير"
    if 'رصدت' in text and 'تم تدمير' in text:
        try:
            detection_part = text.split('رصدت')[1].split('تم تدمير')[0]
            detected = re.findall(r'(\d+)\s+صاروخ\s+باليستي', detection_part)
            if detected:
                stats['ballistic_detected'] = int(detected[0])
        except:
            pass
    
    # Interception section: after "تم تدمير"
    if 'تم تدمير' in text:
        try:
            interception_part = text.split('تم تدمير')[1]
            intercepted = re.findall(r'(\d+)\s+صاروخ\s+باليستي', interception_part)
            if intercepted:
                stats['ballistic_intercepted'] = int(intercepted[0])
        except:
            pass
    
    # Drones
    # Detection section: after "تم رصد" and before "تم اعتراض"
    if 'تم رصد' in text and 'تم اعتراض' in text:
        try:
            # Find the part with "تم رصد" that comes before "تم اعتراض"
            r_parts = text.split('تم رصد')
            for part in r_parts[1:]:
                if 'طائرة' in part and 'تم اعتراض' in text:
                    detection_part = part.split('تم اعتراض')[0]
                    detected = re.findall(r'(\d+)\s+طائرة(?:\s+مسيرة)?', detection_part)
                    if detected:
                        stats['drones_detected'] = int(detected[0])
                        break
        except:
            pass
    
    # Interception section: after "تم اعتراض"
    if 'تم اعتراض' in text:
        try:
            interception_part = text.split('تم اعتراض')[1]
            intercepted = re.findall(r'(\d+)\s+طائرة', interception_part)
            if intercepted:
                stats['drones_intercepted'] = int(intercepted[0])
        except:
            pass
    
    # Fallback: look for "تتعامل مع X صاروخ" format at the start (summary numbers)
    deal_ballistic = re.findall(r'تتعامل مع\s+(\d+)\s+صاروخ\s+باليستي', text)
    deal_drones = re.findall(r'تتعامل مع\s+(\d+)\s+طائرة\s+مسيرة', text)
    
    # Use "deal" numbers as fallback
    if stats['ballistic_detected'] == 0 and deal_ballistic:
        stats['ballistic_detected'] = int(deal_ballistic[0])
    if stats['ballistic_intercepted'] == 0 and deal_ballistic:
        stats['ballistic_intercepted'] = int(deal_ballistic[0])
    if stats['drones_detected'] == 0 and deal_drones:
        stats['drones_detected'] = int(deal_drones[0])
    if stats['drones_intercepted'] == 0 and deal_drones:
        stats['drones_intercepted'] = int(deal_drones[0])
    
    # Calculate impacted (fell on land or sea but not intercepted)
    total_detected = stats['ballistic_detected'] + stats['drones_detected']
    total_intercepted = stats['ballistic_intercepted'] + stats['drones_intercepted']
    if total_detected > total_intercepted:
        stats['impacted'] = total_detected - total_intercepted
    
    return stats

def parse_moi_feed(since_date: Optional[str] = None) -> Dict:
    """Parse @moiuae RSS feed and extract missile statistics"""
    
    feed = feedparser.parse(MOI_UAE_FEED)
    
    if since_date:
        since = datetime.strptime(since_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
    else:
        since = datetime.now(timezone.utc) - timedelta(days=7)
    
    # Aggregate statistics
    totals = {
        'ballistic_detected': 0,
        'ballistic_intercepted': 0,
        'cruise_detected': 0,
        'cruise_intercepted': 0,
        'drones_detected': 0,
        'drones_intercepted': 0,
        'total_detected': 0,
        'total_intercepted': 0,
        'impacted': 0,
        'killed': 0,
        'injured': 0
    }
    
    daily_stats = {}
    incidents = []
    processed_tweet_ids = set()  # Deduplicate by tweet ID (status/XXXXXXXX)
    
    for entry in feed.entries:
        # Parse date
        published = entry.get('published', '')
        try:
            entry_date = datetime.strptime(published, '%a, %d %b %Y %H:%M:%S %Z').replace(tzinfo=timezone.utc)
        except:
            continue
        
        # Skip old entries
        if entry_date < since:
            continue
        
        title = entry.get('title', '')
        link = entry.get('link', '')
        
        # Extract tweet ID from URL (e.g., /status/123456789)
        tweet_id_match = re.search(r'/status/(\d+)', link)
        if tweet_id_match:
            tweet_id = tweet_id_match.group(1)
        else:
            tweet_id = link  # Fallback to full URL
        
        # Deduplicate by tweet ID
        if tweet_id in processed_tweet_ids:
            continue
        processed_tweet_ids.add(tweet_id)
        
        # Extract stats from tweet
        stats = extract_numbers_from_text(title)
        
        # Only include if we found relevant data
        if stats['ballistic_detected'] > 0 or stats['drones_detected'] > 0:
            date_str = entry_date.strftime('%Y-%m-%d')
            
            # Aggregate totals
            for key in ['ballistic_detected', 'ballistic_intercepted', 'cruise_detected', 
                       'cruise_intercepted', 'drones_detected', 'drones_intercepted', 'impacted']:
                totals[key] += stats[key]
            
            # Track daily
            if date_str not in daily_stats:
                daily_stats[date_str] = {
                    'date': date_str,
                    'ballistic_detected': 0,
                    'ballistic_intercepted': 0,
                    'cruise_detected': 0,
                    'cruise_intercepted': 0,
                    'drones_detected': 0,
                    'drones_intercepted': 0,
                    'total': 0
                }
            
            for key in ['ballistic_detected', 'ballistic_intercepted', 'cruise_detected', 
                       'cruise_intercepted', 'drones_detected', 'drones_intercepted']:
                daily_stats[date_str][key] += stats[key]
                daily_stats[date_str]['total'] += stats[key]
            
            incidents.append({
                'id': f"moi_{entry_date.timestamp()}",
                'title': title,
                'source': 'UAE Ministry of Interior',
                'source_url': link,
                'published': entry_date.isoformat(),
                'date': date_str,
                'stats': stats,
                'type': 'missile_defense',
                'credibility': 100,
                'is_government': True
            })
    
    # Calculate totals
    totals['total_detected'] = (totals['ballistic_detected'] + totals['cruise_detected'] + 
                                totals['drones_detected'])
    totals['total_intercepted'] = (totals['ballistic_intercepted'] + totals['cruise_intercepted'] + 
                                   totals['drones_intercepted'])
    
    # Get last 24 hours
    last_24h = datetime.now(timezone.utc) - timedelta(hours=24)
    last_24h_stats = {
        'detected': 0,
        'intercepted': 0,
        'impacted': 0
    }
    
    for inc in incidents:
        inc_date = datetime.fromisoformat(inc['published'])
        if inc_date >= last_24h:
            last_24h_stats['detected'] += inc['stats']['ballistic_detected'] + inc['stats']['cruise_detected'] + inc['stats']['drones_detected']
            last_24h_stats['intercepted'] += inc['stats']['ballistic_intercepted'] + inc['stats']['cruise_intercepted'] + inc['stats']['drones_intercepted']
            last_24h_stats['impacted'] += inc['stats']['impacted']
    
    return {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'since_date': since_date or (datetime.now(timezone.utc) - timedelta(days=7)).strftime('%Y-%m-%d'),
        'source': 'UAE Ministry of Interior (@moiuae)',
        'total_incidents': len(incidents),
        'totals': totals,
        'last_24h': last_24h_stats,
        'daily': sorted(daily_stats.values(), key=lambda x: x['date']),
        'incidents': incidents
    }

if __name__ == '__main__':
    # Parse since March 3rd, 2026
    result = parse_moi_feed(since_date='2026-03-03')
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
