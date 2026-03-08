# Gulf Watch Instagram Scraper

Scrapes Instagram posts from government accounts every 30 minutes.

## Setup Options

### Option 1: Session File (Recommended)

**Step 1: Export Session from Your Computer**

On your local machine (Mac/PC) with the Instagram account logged in:

```bash
# Install instaloader locally
pip install instaloader

# Login and save session
python -c "
import instaloader
L = instaloader.Instaloader()
L.login('GulfWatch', 'Folly.4Ape')
L.save_session_to_file()
"
```

This creates a file called `.instaloader_session` in your current directory.

**Step 2: Convert Session to Base64**

```bash
# On Mac/Linux
base64 .instaloader_session | pbcopy  # Copies to clipboard

# On Windows (PowerShell)
[Convert]::ToBase64String([IO.File]::ReadAllBytes('.instaloader_session')) | Set-Clipboard
```

**Step 3: Add to GitHub Secrets**

1. Go to: https://github.com/nKOxxx/gulf-watch-v2-test/settings/secrets/actions
2. Click "New repository secret"
3. Name: `INSTAGRAM_SESSION_B64`
4. Value: Paste the base64 string from clipboard
5. Click "Add secret"

**Step 4: Also add username**

Add another secret:
- Name: `INSTAGRAM_USER`
- Value: `GulfWatch`

Done! The scraper will use the session file and won't need to login.

---

### Option 2: Username/Password (Less Reliable)

**Add GitHub Secrets:**
1. `INSTAGRAM_USER` = `GulfWatch`
2. `INSTAGRAM_PASS` = `Folly.4Ape`

**Note:** Instagram may block logins from unknown locations (GitHub servers). You'll need to approve the login from your phone/browser when prompted.

---

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

## How to Add Your 13 Following Accounts

Edit `scripts/fetch_instagram.py` and add to `INSTAGRAM_ACCOUNTS`:

```python
'custom': [
    {'handle': 'account1', 'name': 'Account 1', 'country': 'UAE', 'credibility': 95},
    {'handle': 'account2', 'name': 'Account 2', 'country': 'Saudi Arabia', 'credibility': 95},
    # ... add your 13 accounts here
],
```

## Testing

Run manually to test:
```bash
# Set environment variables
export INSTAGRAM_USER=GulfWatch
export INSTAGRAM_PASS=Folly.4Ape
# OR
export INSTAGRAM_SESSION_B64=<base64_string>

# Run scraper
python scripts/fetch_instagram.py
```

## Troubleshooting

**"Checkpoint required" error:**
- Instagram detected unusual login
- Approve login from your phone/browser
- Export session file (Option 1) to avoid this

**"Wrong password" error:**
- Check credentials in GitHub Secrets
- Instagram may require password reset

**"Login error" after session setup:**
- Session may have expired (lasts ~1 month)
- Re-export and update INSTAGRAM_SESSION_B64

## Notes

- Runs every 30 minutes via GitHub Actions
- Only fetches posts from last 48 hours
- Filters for security-related keywords
- Deduplicates by content similarity
- Free GitHub tier: 2,000 minutes/month (enough for this)
