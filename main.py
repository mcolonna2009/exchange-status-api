from flask import Flask, jsonify, request
import requests
from datetime import datetime, time
from zoneinfo import ZoneInfo

app = Flask(__name__)

API_KEY = 'dc9e776dd069479b906c09fbd9dcc9ba'
TRADING_START = time(9, 0)
TRADING_END = time(17, 0)

REGIONS = {
    "Americas": ["United States", "Canada", "Brazil", "Mexico", "Argentina", "Chile", "Colombia", "Peru", "Jamaica", "Venezuela"],
    "Europe": ["Austria", "Belgium", "France", "Germany", "Italy", "Netherlands", "Portugal", "Spain", "Sweden", "Switzerland", "United Kingdom", "Czech Republic", "Denmark", "Estonia", "Finland", "Greece", "Hungary", "Iceland", "Ireland", "Latvia", "Lithuania", "Norway", "Poland", "Romania", "Russia"],
    "Asia-Pacific": ["Australia", "China", "Hong Kong", "India", "Indonesia", "Israel", "Japan", "Malaysia", "New Zealand", "Pakistan", "Philippines", "Singapore", "South Korea", "Taiwan", "Thailand"],
    "Other": []
}

def get_region(country):
    for region, countries in REGIONS.items():
        if country in countries:
            return region
    return "Other"

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

@app.route('/')
def market_status():
    if request.args.get('key') != 'SECRET123':
        return jsonify({"error": "Unauthorized"}), 403

    r = requests.get(f'https://api.twelvedata.com/exchanges?apikey={API_KEY}')
    data = r.json().get('data', [])

    now_utc = datetime.utcnow().replace(second=0, microsecond=0)
    open_list, closed_list = [], []
    region_stats = {}

    for ex in data:
        try:
            name = ex.get("name")
            country = ex.get("country")
            tz = ex.get("timezone")
            if not all([name, country, tz]):
                continue
            local_time = now_utc.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo(tz)).timetz()
            is_open = TRADING_START <= local_time <= TRADING_END

            region = get_region(country)
            region_stats.setdefault(region, {"open": 0, "closed": 0, "exchanges": []})

            status_line = f"{'✅' if is_open else '❌'} {name} ({country}) – {'Open' if is_open else 'Closed'}"
            if "NASDAQ" in name or "NYSE" in name:
                index_name = "NASDAQ" if "NASDAQ" in name else "NYSE"
                status_line += f" — {fetch_index(index_name, index_name)}"

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
        "<strong>📊 Daily Global Exchange Status</strong><br><br>",
        f"<strong>Date:</strong> {now_utc.strftime('%m/%d/%y %I:%M%p')}<br><br>",
        f"✅ <strong>Open Exchanges:</strong> {total_open}<br>❌ <strong>Closed Exchanges:</strong> {total_closed}<br><br>"
    ]

    for region, stats in region_stats.items():
        lines.append(f"🌍 <strong>{region}</strong> — Open: {stats['open']} | Closed: {stats['closed']}<br>")
        for exch in stats["exchanges"]:
            lines.append(f"{exch}<br>")
        lines.append("<br>")

    return jsonify({
        "open_count": total_open,
        "closed_count": total_closed,
        "summary": "".join(lines)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
