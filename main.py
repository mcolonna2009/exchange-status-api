from flask import Flask, jsonify, request
import requests
from datetime import datetime, time
from zoneinfo import ZoneInfo

app = Flask(__name__)

API_KEY = 'dc9e776dd069479b906c09fbd9dcc9ba'
TRADING_START = time(9, 0)
TRADING_END = time(17, 0)

INDEX_SYMBOLS = {
    "NYSE": "NYSE",
    "NASDAQ": "NDX",
}

def fetch_index(symbol: str, name: str):
    url = f'https://api.twelvedata.com/quote?symbol={symbol}&apikey={API_KEY}'
    try:
        r = requests.get(url)
        data = r.json()
        price = float(data['close'])
        change = float(data['percent_change'])
        arrow = "▲" if change >= 0 else "▼"
        return f"{name}: {price:,.2f} {arrow} {change:+.2f}%"
    except Exception:
        return f"{name}: N/A"

def get_region(country):
    regions = {
        "Americas": ["United States", "Canada", "Brazil", "Argentina", "Mexico", "Chile", "Colombia", "Peru", "Jamaica", "Venezuela"],
        "Europe": ["United Kingdom", "Germany", "France", "Italy", "Spain", "Portugal", "Netherlands", "Belgium", "Sweden", "Austria", "Finland", "Denmark", "Ireland", "Greece", "Hungary", "Poland", "Switzerland", "Czech Republic", "Estonia", "Lithuania", "Latvia", "Norway", "Russia", "Romania"],
        "Asia-Pacific": ["Japan", "China", "India", "Hong Kong", "Australia", "Singapore", "South Korea", "Indonesia", "Malaysia", "Thailand", "Taiwan", "New Zealand", "Philippines", "Pakistan"],
        "Other": ["South Africa", "Saudi Arabia", "United Arab Emirates", "Egypt", "Botswana", "Turkey", "Qatar", "Kuwait", "Israel", "Iceland"]
    }
    for region, countries in regions.items():
        if country in countries:
            return region
    return "Other"

@app.route('/')
def market_status():
    if request.args.get('key') != 'SECRET123':
        return jsonify({"error": "Unauthorized"}), 403

    now_utc = datetime.utcnow().replace(second=0, microsecond=0)

    r = requests.get(f'https://api.twelvedata.com/exchanges?apikey={API_KEY}')
    exchanges = r.json().get("data", [])

    region_stats = {}

    for ex in exchanges:
        try:
            name = ex.get("name")
            country = ex.get("country")
            timezone = ex.get("timezone")
            code = ex.get("code")

            if not (name and country and timezone):
                continue

            region = get_region(country)
            if region not in region_stats:
                region_stats[region] = {"open": 0, "closed": 0, "exchanges": []}

            tz = ZoneInfo(timezone)
            local_time = now_utc.astimezone(tz).time()
            is_open = TRADING_START <= local_time <= TRADING_END

            status_icon = "✅" if is_open else "❌"
            status = "Open" if is_open else "Closed"

            line = f"{status_icon} {name} ({country}) – {status}"

            if not is_open and code in INDEX_SYMBOLS:
                line += f" — {fetch_index(INDEX_SYMBOLS[code], code)}"

            region_stats[region]["open" if is_open else "closed"] += 1
            region_stats[region]["exchanges"].append(line)
        except Exception:
            continue

    total_open = sum(r["open"] for r in region_stats.values())
    total_closed = sum(r["closed"] for r in region_stats.values())

    lines =
