from flask import Flask, jsonify, request
import requests
from datetime import datetime, time
from zoneinfo import ZoneInfo

app = Flask(__name__)

API_KEY = 'dc9e776dd069479b906c09fbd9dcc9ba'  # Replace with your own TwelveData API key
TRADING_START = time(9, 0)
TRADING_END = time(17, 0)
AUTHORIZED_KEY = 'SECRET123'

# Region mapping for grouping
REGIONS = {
    "United States": "Americas",
    "Canada": "Americas",
    "Brazil": "Americas",
    "Mexico": "Americas",
    "Argentina": "Americas",
    "United Kingdom": "Europe",
    "Germany": "Europe",
    "France": "Europe",
    "Italy": "Europe",
    "Portugal": "Europe",
    "Netherlands": "Europe",
    "Spain": "Europe",
    "Belgium": "Europe",
    "Austria": "Europe",
    "Sweden": "Europe",
    "Switzerland": "Europe",
    "Russia": "Europe",
    "Poland": "Europe",
    "Turkey": "Europe",
    "Australia": "Asia-Pacific",
    "New Zealand": "Asia-Pacific",
    "Japan": "Asia-Pacific",
    "China": "Asia-Pacific",
    "India": "Asia-Pacific",
    "Hong Kong": "Asia-Pacific",
    "Singapore": "Asia-Pacific",
    "South Korea": "Asia-Pacific",
    "Taiwan": "Asia-Pacific",
    "Malaysia": "Asia-Pacific",
    "Indonesia": "Asia-Pacific",
    "Thailand": "Asia-Pacific",
    "United Arab Emirates": "Other",
    "Saudi Arabia": "Other",
    "South Africa": "Other",
}

INDEX_SYMBOLS = {
    "NYSE": "DJI",
    "NASDAQ": "IXIC",
    "TSX": "TSX",
    "LSE": "UKX",
}

def fetch_index(symbol: str):
    url = f"https://api.twelvedata.com/quote?symbol={symbol}&apikey={API_KEY}"
    try:
        r = requests.get(url)
        data = r.json()
        price = float(data['close'])
        change = float(data['percent_change'])
        arrow = "▲" if change >= 0 else "▼"
        return f"{price:,.2f} {arrow} {change:+.2f}%"
    except:
        return "N/A"

@app.route('/')
def index():
    if request.args.get('key') != AUTHORIZED_KEY:
        return jsonify({"error": "Unauthorized"}), 403

    r = requests.get(f'https://api.twelvedata.com/exchanges?apikey={API_KEY}')
    data = r.json().get('data', [])

    now_utc = datetime.utcnow()
    region_stats = {}

    for ex in data:
        try:
            name = ex['name']
            country = ex['country']
            tz = ex['timezone']
            region = REGIONS.get(country, 'Other')

            local_time = now_utc.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo(tz)).time()
            is_open = TRADING_START <= local_time <= TRADING_END

            # fetch index only for tracked exchanges
            index_note = ""
            for k, symbol in INDEX_SYMBOLS.items():
                if k in name:
                    index_note = f" — {k}: {fetch_index(symbol)}"

            line = f"{'✅' if is_open else '❌'} {name} ({country}) – {'Open' if is_open else 'Closed'}{index_note}"

            if region not in region_stats:
                region_stats[region] = {"open": 0, "closed": 0, "exchanges": []}
            region_stats[region]["open" if is_open else "closed"] += 1
            region_stats[region]["exchanges"].append(line)

        except Exception:
            continue

    total_open = sum(r["open"] for r in region_stats.values())
    total_closed = sum(r["closed"] for r in region_stats.values())

    lines = [
        "📊 <strong>Daily Global Exchange Status</strong>",
        f"<strong>Date:</strong> {datetime.now().strftime('%m/%d/%y %I:%M%p')}",
        f"✅ <strong>Open Exchanges:</strong> {total_open}",
        f"❌ <strong>Closed Exchanges:</strong> {total_closed}",
        "<hr>"
    ]

    for region, stats in region_stats.items():
        lines.append(f"<strong>🌍 {region}</strong> — Open: {stats['open']} | Closed: {stats['closed']}")
        lines.extend(stats["exchanges"])
        lines.append("")

    return jsonify({
        "open_count": total_open,
        "closed_count": total_closed,
        "summary": "\n".join(lines)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
