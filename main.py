from flask import Flask, jsonify, request
import requests
from datetime import datetime, time
from zoneinfo import ZoneInfo

app = Flask(__name__)

API_KEY = 'dc9e776dd069479b906c09fbd9dcc9ba'  # Replace with your actual TwelveData API key
TRADING_START = time(9, 0)
TRADING_END = time(17, 0)

REGIONS = {
    "Americas": ["United States", "Canada", "Brazil", "Mexico", "Argentina"],
    "Europe": ["Germany", "France", "United Kingdom", "Italy", "Spain", "Sweden", "Switzerland", "Belgium", "Portugal", "Netherlands", "Austria"],
    "Asia-Pacific": ["Japan", "China", "India", "Australia", "South Korea", "Taiwan", "Singapore", "Hong Kong"],
}

def get_region(country):
    for region, countries in REGIONS.items():
        if country in countries:
            return region
    return "Other"

@app.route('/')
def market_status():
    if request.args.get('key') != 'SECRET123':
        return jsonify({"error": "Unauthorized"}), 403

    r = requests.get(f'https://api.twelvedata.com/exchanges?apikey={API_KEY}')
    data = r.json().get('data', [])
    
    now_utc = datetime.utcnow().replace(second=0, microsecond=0)
    region_stats = {}

    for ex in data:
        try:
            name = ex.get('name')
            country = ex.get('country')
            tz = ex.get('timezone')

            local_time = now_utc.astimezone(ZoneInfo(tz))
            is_open = (
                local_time.weekday() < 5 and
                TRADING_START <= local_time.time() <= TRADING_END
            )

            region = get_region(country)
            if region not in region_stats:
                region_stats[region] = {
                    "open": 0,
                    "closed": 0,
                    "exchanges": []
                }

            if is_open:
                region_stats[region]["open"] += 1
                region_stats[region]["exchanges"].append(f"✅ {name} ({country}) – Open")
            else:
                region_stats[region]["closed"] += 1
                region_stats[region]["exchanges"].append(f"❌ {name} ({country}) – Closed")
        except Exception:
            continue

    total_open = sum(r["open"] for r in region_stats.values())
    total_closed = sum(r["closed"] for r in region_stats.values())

    lines = [
        f"📊 Daily Global Exchange Status",
        "",
        f"Date: {datetime.now().strftime('%m/%d/%y %I:%M%p')}",
        "",
        f"✅ Open Exchanges: {total_open}",
        f"❌ Closed Exchanges: {total_closed}",
        ""
    ]

    for region, stats in region_stats.items():
        lines.append(f"🌍 {region} — Open: {stats['open']} | Closed: {stats['closed']}")
        lines.extend(stats["exchanges"])
        lines.append("")

    return jsonify({
        "open_count": total_open,
        "closed_count": total_closed,
        "summary": "\n".join(lines)
    })
