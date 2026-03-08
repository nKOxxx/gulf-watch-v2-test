#!/usr/bin/env python3
"""
Cross-Source Verification Engine
Matches incidents across multiple sources and assigns confidence scores
"""
import json
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher

class CrossSourceVerifier:
    def __init__(self):
        self.sources = {
            # Government Ministries (highest trust)
            'moi_uae': {'weight': 1.0, 'type': 'government', 'name': 'UAE Ministry of Interior'},
            'mod_uae': {'weight': 1.0, 'type': 'government', 'name': 'UAE Ministry of Defence'},
            'saudi_moi': {'weight': 1.0, 'type': 'government', 'name': 'Saudi Ministry of Interior'},
            'saudi_mod': {'weight': 1.0, 'type': 'government', 'name': 'Saudi Ministry of Defence'},
            'qatar_moi': {'weight': 1.0, 'type': 'government', 'name': 'Qatar Ministry of Interior'},
            'qatar_mod': {'weight': 1.0, 'type': 'government', 'name': 'Qatar Ministry of Defence'},
            'bahrain_moi': {'weight': 1.0, 'type': 'government', 'name': 'Bahrain Ministry of Interior'},
            'kuwait_moi': {'weight': 1.0, 'type': 'government', 'name': 'Kuwait Ministry of Interior'},
            'israel_mod': {'weight': 0.95, 'type': 'government', 'name': 'Israel Ministry of Defense'},
            
            # Government Agencies
            'civil_defence': {'weight': 1.0, 'type': 'government', 'name': 'Civil Defence'},
            'national_guard': {'weight': 1.0, 'type': 'government', 'name': 'National Guard'},
            'police': {'weight': 1.0, 'type': 'government', 'name': 'Police'},
            'magen_david_adom': {'weight': 0.95, 'type': 'government', 'name': 'Magen David Adom'},
            
            # State News Agencies
            'wam': {'weight': 0.95, 'type': 'government_news', 'name': 'WAM News Agency'},
            'kuna': {'weight': 0.9, 'type': 'government_news', 'name': 'Kuwait News Agency'},
            'qna': {'weight': 0.9, 'type': 'government_news', 'name': 'Qatar News Agency'},
            'ona': {'weight': 0.9, 'type': 'government_news', 'name': 'Oman News Agency'},
            
            # International News
            'reuters': {'weight': 0.85, 'type': 'news', 'name': 'Reuters'},
            'bbc': {'weight': 0.85, 'type': 'news', 'name': 'BBC'},
            'al_jazeera': {'weight': 0.8, 'type': 'news', 'name': 'Al Jazeera'},
            
            # Iranian State Media
            'mehr_news': {'weight': 0.75, 'type': 'state_media', 'name': 'Mehr News Agency'},
            'fars_news': {'weight': 0.75, 'type': 'state_media', 'name': 'Fars News Agency'},
            
            # Other Sources
            'telegram': {'weight': 0.6, 'type': 'social', 'name': 'Telegram Channels'},
            'newsdata': {'weight': 0.7, 'type': 'news_api', 'name': 'NewsData.io'},
            'unknown': {'weight': 0.5, 'type': 'unknown', 'name': 'Unknown Source'},
        }
        
        # Matching thresholds
        self.TITLE_SIMILARITY_THRESHOLD = 0.6
        self.TIME_WINDOW_MINUTES = 60
        
    def normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        # Lowercase, remove extra spaces, remove punctuation
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def extract_keywords(self, text: str) -> set:
        """Extract key terms from text"""
        # Security-related keywords
        keywords = {
            'missile', 'rocket', 'drone', 'uav', 'air', 'defense', 'interceptor',
            'attack', 'strike', 'explosion', 'bomb', 'threat', 'hostile',
            'uae', 'dubai', 'abu dhabi', 'saudi', 'riyadh', 'qatar', 'doha',
            'iran', 'israel', 'gaza', 'hamas', 'hezbollah', 'houthi',
            'ballistic', 'cruise', 'intercept', 'destroyed'
        }
        
        text_lower = self.normalize_text(text)
        words = set(text_lower.split())
        return words.intersection(keywords)
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, self.normalize_text(text1), self.normalize_text(text2)).ratio()
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats"""
        formats = [
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%S.%f%z',
            '%Y-%m-%dT%H:%M:%S',
            '%a, %d %b %Y %H:%M:%S %Z',
            '%Y-%m-%d %H:%M:%S',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue
        return None
    
    def is_same_incident(self, inc1: Dict, inc2: Dict) -> Tuple[bool, float]:
        """Check if two incidents are the same event"""
        # Check time proximity
        date1 = self.parse_date(inc1.get('published', ''))
        date2 = self.parse_date(inc2.get('published', ''))
        
        if date1 and date2:
            time_diff = abs((date1 - date2).total_seconds()) / 60  # minutes
            if time_diff > self.TIME_WINDOW_MINUTES:
                return False, 0.0
        
        # Check location similarity
        loc1 = inc1.get('location', {})
        loc2 = inc2.get('location', {})
        
        country_match = loc1.get('country', '') == loc2.get('country', '')
        city_match = loc1.get('name', '') == loc2.get('name', '')
        
        if not country_match and not city_match:
            return False, 0.0
        
        # Check title similarity
        title_sim = self.calculate_similarity(inc1.get('title', ''), inc2.get('title', ''))
        
        # Check keyword overlap
        keywords1 = self.extract_keywords(inc1.get('title', ''))
        keywords2 = self.extract_keywords(inc2.get('title', ''))
        
        if keywords1 and keywords2:
            keyword_overlap = len(keywords1.intersection(keywords2)) / max(len(keywords1), len(keywords2))
        else:
            keyword_overlap = 0.0
        
        # Combined score
        combined_score = (title_sim * 0.5) + (keyword_overlap * 0.3) + (0.2 if country_match else 0)
        
        is_match = combined_score > self.TITLE_SIMILARITY_THRESHOLD
        return is_match, combined_score
    
    def calculate_confidence(self, incident_group: List[Dict]) -> Dict:
        """Calculate confidence score for a group of matched incidents"""
        sources = set()
        source_weights = []
        government_sources = 0
        news_sources = 0
        
        for inc in incident_group:
            source_key = inc.get('source_key', 'unknown')
            source_info = self.sources.get(source_key, {'weight': 0.5, 'type': 'unknown'})
            
            sources.add(source_key)
            source_weights.append(source_info['weight'])
            
            if source_info['type'] == 'government':
                government_sources += 1
            elif source_info['type'] in ['news', 'government_news']:
                news_sources += 1
        
        # Base confidence from source weights
        avg_weight = sum(source_weights) / len(source_weights) if source_weights else 0.5
        
        # Bonus for multiple sources
        source_count_bonus = min(len(sources) * 0.1, 0.3)  # Max 0.3 bonus for 3+ sources
        
        # Bonus for government confirmation
        gov_bonus = min(government_sources * 0.15, 0.3)
        
        # Calculate final confidence
        confidence = min(avg_weight + source_count_bonus + gov_bonus, 1.0)
        
        # Determine status
        if confidence >= 0.9:
            status = 'Verified'
        elif confidence >= 0.7:
            status = 'Likely True'
        elif confidence >= 0.5:
            status = 'Partially Verified'
        elif confidence >= 0.3:
            status = 'Unconfirmed'
        else:
            status = 'Questionable'
        
        return {
            'confidence': round(confidence * 100),
            'status': status,
            'source_count': len(sources),
            'government_sources': government_sources,
            'news_sources': news_sources,
            'sources': list(sources)
        }
    
    def deduplicate_and_verify(self, incidents: List[Dict]) -> List[Dict]:
        """Deduplicate incidents and calculate verification scores"""
        # Sort by date (newest first)
        incidents = sorted(incidents, key=lambda x: x.get('published', ''), reverse=True)
        
        # Group similar incidents
        groups = []
        used = set()
        
        for i, inc1 in enumerate(incidents):
            if i in used:
                continue
            
            group = [inc1]
            used.add(i)
            
            for j, inc2 in enumerate(incidents[i+1:], start=i+1):
                if j in used:
                    continue
                
                is_match, score = self.is_same_incident(inc1, inc2)
                if is_match:
                    group.append(inc2)
                    used.add(j)
            
            groups.append(group)
        
        # Create merged incidents with verification data
        verified_incidents = []
        
        for group in groups:
            # Use the most credible source as primary
            primary = max(group, key=lambda x: self.sources.get(x.get('source_key', 'unknown'), {}).get('weight', 0.5))
            
            # Calculate verification
            verification = self.calculate_confidence(group)
            
            # Create merged incident
            merged = primary.copy()
            merged['verification'] = verification
            merged['source_variants'] = [
                {
                    'source': inc.get('source', 'Unknown'),
                    'title': inc.get('title', ''),
                    'published': inc.get('published', ''),
                    'url': inc.get('source_url', ''),
                    'source_key': inc.get('source_key', 'unknown')
                }
                for inc in group
            ]
            
            verified_incidents.append(merged)
        
        return verified_incidents
    
    def load_source_data(self) -> List[Dict]:
        """Load data from all v2-test sources"""
        all_incidents = []
        
        # Load RSS.app incidents
        try:
            with open('public/rss_incidents.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                for inc in data.get('incidents', []):
                    inc['source_key'] = self._map_source_to_key(inc.get('source', ''))
                    all_incidents.append(inc)
        except Exception as e:
            print(f"Error loading RSS incidents: {e}")
        
        # Load Telegram incidents
        try:
            with open('public/telegram_incidents.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                for inc in data.get('incidents', []):
                    inc['source_key'] = 'telegram'
                    all_incidents.append(inc)
        except Exception as e:
            print(f"Error loading Telegram incidents: {e}")
        
        # Load NewsData incidents (if available)
        try:
            with open('public/newsdata_incidents.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                for inc in data.get('incidents', []):
                    inc['source_key'] = 'newsdata'
                    all_incidents.append(inc)
        except Exception as e:
            print(f"Error loading NewsData incidents: {e}")
        
        return all_incidents
    
    def _map_source_to_key(self, source_name: str) -> str:
        """Map source name to source key"""
        source_lower = source_name.lower()
        
        # Handle "Twitter - X" format from RSS.app
        if source_lower.startswith('twitter - '):
            source_lower = source_lower[10:]  # Remove "twitter - " prefix
        
        if 'ministry of interior' in source_lower or 'moi' in source_lower:
            if 'uae' in source_lower:
                return 'moi_uae'
            elif 'saudi' in source_lower:
                return 'saudi_moi'
            elif 'qatar' in source_lower:
                return 'qatar_moi'
            elif 'bahrain' in source_lower:
                return 'bahrain_moi'
            elif 'kuwait' in source_lower:
                return 'kuwait_moi'
        
        if 'ministry of defence' in source_lower or 'ministry of defense' in source_lower or 'mod' in source_lower:
            if 'uae' in source_lower:
                return 'mod_uae'
            elif 'qatar' in source_lower:
                return 'qatar_mod'
            elif 'israel' in source_lower:
                return 'israel_mod'
        
        if 'wam' in source_lower:
            return 'wam'
        
        if 'reuters' in source_lower:
            return 'reuters'
        
        if 'bbc' in source_lower:
            return 'bbc'
        
        if 'jazeera' in source_lower or 'aljazeera' in source_lower:
            return 'al_jazeera'
        
        if 'civil defence' in source_lower or 'civil defense' in source_lower:
            return 'civil_defence'
        
        if 'national guard' in source_lower:
            return 'national_guard'
        
        if 'police' in source_lower:
            return 'police'
        
        if 'news agency' in source_lower:
            if 'kuwait' in source_lower or 'kuna' in source_lower:
                return 'kuna'
            if 'qatar' in source_lower:
                return 'qna'
            if 'oman' in source_lower:
                return 'ona'
        
        if 'mehr news' in source_lower:
            return 'mehr_news'
        
        if 'fars news' in source_lower:
            return 'fars_news'
        
        if 'magen david' in source_lower or 'mda' in source_lower or 'mada' in source_lower:
            return 'magen_david_adom'
        
        return 'unknown'
    
    def process(self) -> Dict:
        """Main processing pipeline"""
        # Load all data
        raw_incidents = self.load_source_data()
        
        print(f"Loaded {len(raw_incidents)} raw incidents")
        
        # Deduplicate and verify
        verified = self.deduplicate_and_verify(raw_incidents)
        
        print(f"Produced {len(verified)} verified incidents")
        
        # Count by status
        status_counts = {}
        for inc in verified:
            status = inc.get('verification', {}).get('status', 'Unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print(f"Status breakdown: {status_counts}")
        
        return {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'total_raw': len(raw_incidents),
            'total_verified': len(verified),
            'status_breakdown': status_counts,
            'incidents': verified
        }

if __name__ == '__main__':
    verifier = CrossSourceVerifier()
    result = verifier.process()
    
    # Save output
    with open('public/verified_incidents.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved to public/verified_incidents.json")
    print(f"Total verified: {result['total_verified']}")
