from flask import Flask, jsonify, request
import requests
from datetime import datetime, time
from zoneinfo import ZoneInfo

app = Flask(__name__)

API_KEY = 'dc9e776dd069479b906c09fbd9dcc9ba'
TRADING_START = time(9, 0)
TRADING_END = time(17, 0)

REGIONS = {
    "Americas": ["United States", "Canada", "Brazil", "Mexico", "Argentina"],
    "Europe": ["Germany", "France", "United Kingdom", "Italy", "Spain", "Sweden", "Switzerland", "Belgium", "Portugal", "Netherlands", "Austria"],
    "Asia-Pacific": ["Japan", "China", "India", "Australia", "South Korea", "Taiwan", "Singapore", "Hong Kong"],
}

# Exchange name → (index symbol, label)
INDEX_SYMBOLS = {
    "New York Stock Exchange, Inc.": ("DJI", "Dow Jones"),
    "NASDAQ": ("IXIC", "NASDAQ"),
    "London Stock Exchange": ("FTSE", "FTSE 100"),
    "JPX (Japan)": ("N225", "Nikkei 225")
}

def get_region(country):
    for region, countries in REGIONS.items():
        if country in countries:
            return region
    return "Other"

def fetch_index(symbol: str, name: str):
    try:
        r = requests.get(f'https://api.twelvedata.com/quote?symbol={symbol}&apikey={API_KEY}')
        data = r.json()
        price = float(data['close'])
        change = float(data['percent_change'])
        arrow = "▲" if change >= 0 else "▼"
        return f"{name}: {price:,.2f} {arrow} {change:+.2f}%"
    except:
        return f"{name}: N/A"

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

            print("Exchange name:", name)  # debug log

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

            enriched = ""
            if name in INDEX_SYMBOLS:
                sym, label = INDEX_SYMBOLS[name]
                enriched = f" — {fetch_index(sym, label)}"

            status_line = f"{'✅' if is_open else '❌'} {name} ({country}) – {'Open' if is_open else 'Closed'}{enriched}"
            if is_open:
                region_stats[region]["open"] += 1
            else:
                region_stats[region]["closed"] += 1
            region_stats[region]["exchanges"].append(status_line)

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
