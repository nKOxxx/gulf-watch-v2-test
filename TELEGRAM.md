# Gulf Watch Telegram Scraper

Fetches messages from government Telegram channels every 30 minutes.

## Setup

### Step 1: Get Telegram API Credentials

1. Go to https://my.telegram.org/apps
2. Log in with your phone number
3. Click "API development tools"
4. Fill in:
   - App title: `GulfWatch`
   - Short name: `gulfwatch`
   - URL: `https://github.com/nKOxxx/gulf-watch-v2-test`
   - Platform: `Desktop`
   - Description: `Government news monitoring`
5. Click "Create application"
6. You'll get:
   - **api_id** (numbers)
   - **api_hash** (letters/numbers)

### Step 2: Generate Session String

On your computer, run:

```bash
pip install telethon
python -c "
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

api_id = YOUR_API_ID  # Replace with your api_id
api_hash = 'YOUR_API_HASH'  # Replace with your api_hash

with TelegramClient(StringSession(), api_id, api_hash) as client:
    print('Session string (save this):')
    print(client.session.save())
"
```

Enter your phone number when prompted, then the code sent to your Telegram.

Copy the long string it outputs - this is your session.

### Step 3: Add GitHub Secrets

Go to: https://github.com/nKOxxx/gulf-watch-v2-test/settings/secrets/actions

Add three secrets:

1. **TELEGRAM_API_ID** = your api_id (numbers only)
2. **TELEGRAM_API_HASH** = your api_hash
3. **TELEGRAM_SESSION** = the long string from step 2

### Step 4: Test

Run manually:
```bash
export TELEGRAM_API_ID=your_api_id
export TELEGRAM_API_HASH=your_api_hash
export TELEGRAM_SESSION=your_session_string
python scripts/fetch_telegram.py
```

## Channels Monitored

### UAE (4 channels)
- @moiuae - Ministry of Interior
- @NCEMAUAE - National Emergency
- @modgovae - Ministry of Defence
- @wamnews - WAM News Agency

### Saudi Arabia (3 channels)
- @saudimoi - Ministry of Interior
- @SaudiDCD - Civil Defense
- @SPAregions - Saudi Press Agency

### Qatar (3 channels)
- @MOI_Qatar - Ministry of Interior
- @civildefenceqa - Civil Defence
- @QatarNewsAgency - Qatar News Agency

### Bahrain (2 channels)
- @moi_bahrain - Ministry of Interior
- @bahraindefence - Defence Force

### Kuwait (2 channels)
- @moi_kuwait - Ministry of Interior
- @kff_kw - Fire Force

### Israel (2 channels)
- @idfhebrew - IDF Hebrew
- @IDFarabic - IDF Arabic

## Output

`public/telegram_incidents.json` contains:
- All security-related messages from last 48 hours
- Formatted same as other incident sources
- Includes: title, source, URL, date, location, credibility

## Adding More Channels

Edit `scripts/fetch_telegram.py` and add to `TELEGRAM_CHANNELS`:

```python
'country': [
    {'channel': 'channelname', 'name': 'Channel Name', 'country': 'Country', 'credibility': 95},
],
```

## Notes

- Runs every 30 minutes via GitHub Actions
- Only fetches messages from last 48 hours
- Filters for security-related keywords only
- Deduplicates by content similarity
- Free GitHub tier: 2,000 minutes/month (enough for this)
- Telegram API is free and official

## Troubleshooting

**"Not authorized" error:**
- Session string expired (regenerate)
- Phone number banned (use different number)

**"Cannot access channel" error:**
- Channel doesn't exist or is private
- Check channel name is correct

**"Missing Telegram API credentials":**
- Check GitHub Secrets are set correctly
- TELEGRAM_API_ID should be numbers only (no quotes)
