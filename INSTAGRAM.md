# Gulf Watch Instagram Scraper

Scrapes Instagram posts from government accounts every 30 minutes.

## Setup

1. **Add Instagram credentials to GitHub Secrets:**
   - Go to: Settings → Secrets and variables → Actions
   - Add `INSTAGRAM_USER` - Your Instagram username
   - Add `INSTAGRAM_PASS` - Your Instagram password

2. **First run will create session file:**
   - Script logs in once
   - Saves session to `.instaloader_session`
   - Future runs use saved session

## Accounts Monitored

### UAE (8 accounts)
- @moiuae - Ministry of Interior
- @modgovae - Ministry of Defence
- @NCEMAUAE - National Emergency
- @Uaengc - National Guard
- @UAEmediaoffice - Government Media
- @wamnews - WAM News Agency
- @DXBMediaOffice - Dubai Media Office
- @CivilDefenceAD - Abu Dhabi Civil Defence

### Saudi Arabia (4 accounts)
- @MOISaudiArabia - Ministry of Interior
- @SaudiDCD - Civil Defense
- @MOD_Saudi - Ministry of Defence
- @SPAregions - Saudi Press Agency

### Qatar (4 accounts)
- @MOI_QatarEn - Ministry of Interior
- @civildefenceqa - Civil Defence
- @MOD_Qatar - Ministry of Defence
- @QatarNewsAgency - Qatar News Agency

### Bahrain (3 accounts)
- @moi_bahrain - Ministry of Interior
- @bahraindefence - Defence Force
- @bna_bh - News Agency

### Kuwait (3 accounts)
- @moi_kuw_en - Ministry of Interior
- @kff_kw - Fire Force
- @KUNA_en - News Agency

### Oman (3 accounts)
- @RoyalOmanPolice - Police
- @MoDOman - Ministry of Defence
- @ONA_Oman - News Agency

### Israel (3 accounts)
- @IDF - Defense Forces
- @Israel_MOD - Ministry of Defense
- @Mdais - Magen David Adom

## Output

`public/instagram_incidents.json` contains:
- All security-related posts from last 48 hours
- Formatted same as other incident sources
- Includes: title, source, URL, date, location, credibility

## Notes

- Only fetches posts from last 48 hours
- Filters for security-related keywords only
- Deduplicates by content similarity
- Runs every 30 minutes
