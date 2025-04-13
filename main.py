# main.py

from flask import Flask, jsonify, request
import requests
from datetime import datetime, time
from zoneinfo import ZoneInfo

app = Flask(__name__)

API_KEY = 'dc9e776dd069479b906c09fbd9dcc9ba'
TRADING_START = time(9, 0)
TRADING_END = time(17, 0)

REGIONS = {
    "Americas": ["Argentina", "Brazil", "Canada", "Mexico", "United States", "Jamaica", "Chile", "Colombia", "Peru", "Venezuela"],
    "Europe": ["Austria", "Belgium", "France", "Germany", "Italy", "Netherlands", "Portugal", "Spain", "Sweden", "Switzerland", "United Kingdom", "Greece", "Finland", "Denmark", "Estonia", "Lithuania", "Latvia", "Hungary", "Ireland", "Czech Republic", "Poland", "Romania", "Russia", "Iceland", "Norway"],
    "Asia-Pacific": ["Australia", "China", "Hong Kong", "India", "Indonesia", "Israel", "Japan", "South Korea", "Taiwan", "Thailand", "Philippines", "Malaysia", "New Zealand", "Pakistan", "Singapore"],
    "Other": []
}

def classify_region(country):
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
    except Exception:
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
            name = ex['name']
            country = ex['country']
            timezone = ex['timezone']
            tz = ZoneInfo(timezone)
            local_time = now_utc.replace(tzinfo=ZoneInfo('UTC')).astimezone(tz).time()

            is_open = TRADING_START <= local_time <= TRADING_END
            region = classify_region(country)
            status_line = f"{'✅' if is_open else '❌'} {name} ({country}) – {'Open' if is_open else 'Closed'}"

            if name in ["NYSE", "NASDAQ"] and not is_open:
                index_line = fetch_index(name, name)
                status_line += f" — {index_line}"

            if region not in region_stats:
                region_stats[region] = {"open": 0, "closed": 0, "exchanges": []}
            if is_open:
                region_stats[region]["open"] += 1
            else:
                region_stats[region]["closed"] += 1
            region_stats[region]["exchanges"].append(status_line)

        except Exception:
            continue

    total_open = sum(r["open"] for r in region_stats.values())
    total_closed = sum(r["closed"] for r in region_stats.values())

    lines = []
    now_str = datetime.utcnow().strftime("%m/%d/%y %I:%M%p")

    lines.append("<h2>📊 Daily Global Exchange Status</h2>")
    lines.append(f"<p><strong>Date:</strong> {now_str}</p>")
    lines.append(f"<p>✅ <strong>Open Exchanges:</strong> {total_open}<br>❌ <strong>Closed Exchanges:</strong> {total_closed}</p>")
    lines.append("<hr>")

    for region, stats in region_stats.items():
        lines.append(f"<p><strong>🌍 {region} — Open: {stats['open']} | Closed: {stats['closed']}</strong><br>")
        lines.extend(stats["exchanges"])
        lines.append("</p>")

    return jsonify({
        "open_count": total_open,
        "closed_count": total_closed,
        "summary": "\n".join(lines)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
