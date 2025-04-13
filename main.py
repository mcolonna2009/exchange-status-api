from flask import Flask, jsonify, request
import requests
from datetime import datetime, time
from zoneinfo import ZoneInfo

app = Flask(__name__)

API_KEY = 'dc9e776dd069479b906c09fbd9dcc9ba'
TRADING_START = time(9, 0)
TRADING_END = time(17, 0)

REGION_MAP = {
    "Argentina": "Americas", "Brazil": "Americas", "Canada": "Americas", "Mexico": "Americas",
    "United States": "Americas", "Venezuela": "Americas",
    "Belgium": "Europe", "France": "Europe", "Germany": "Europe", "Italy": "Europe",
    "Netherlands": "Europe", "Portugal": "Europe", "Spain": "Europe", "Sweden": "Europe",
    "Switzerland": "Europe", "United Kingdom": "Europe", "Austria": "Europe",
    "Australia": "Asia-Pacific", "China": "Asia-Pacific", "Hong Kong": "Asia-Pacific",
    "India": "Asia-Pacific", "Japan": "Asia-Pacific", "Singapore": "Asia-Pacific",
    "South Korea": "Asia-Pacific", "Taiwan": "Asia-Pacific",
}

def fetch_index(symbol: str):
    url = f'https://api.twelvedata.com/quote?symbol={symbol}&apikey={API_KEY}'
    try:
        r = requests.get(url)
        data = r.json()
        price = float(data['close'])
        change = float(data['percent_change'])
        arrow = "▲" if change >= 0 else "▼"
        return f"{price:,.2f} {arrow} {change:+.2f}%"
    except Exception:
        return "N/A"

@app.route('/')
def market_status():
    if request.args.get('key') != 'SECRET123':
        return jsonify({"error": "Unauthorized"}), 403

    r = requests.get(f'https://api.twelvedata.com/exchanges?apikey={API_KEY}')
    data = r.json().get('data', [])

    now_utc = datetime.utcnow().replace(second=0, microsecond=0)
    region_stats = {}
    shown_indexes = set()

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

            region = REGION_MAP.get(country, "Other")
            if region not in region_stats:
                region_stats[region] = {"open": 0, "closed": 0, "exchanges": []}

            if is_open:
                region_stats[region]["open"] += 1
            else:
                region_stats[region]["closed"] += 1

            status_line = f"{'✅' if is_open else '❌'} {name} ({country}) – {'Open' if is_open else 'Closed'}"

            if name in ("NASDAQ", "NYSE") and name not in shown_indexes:
                index = fetch_index(name)
                status_line += f" — {name}: {index}"
                shown_indexes.add(name)

            region_stats[region]["exchanges"].append(status_line)

        except Exception:
            continue

    total_open = sum(r["open"] for r in region_stats.values())
    total_closed = sum(r["closed"] for r in region_stats.values())

    lines = [
        "📊 Daily Global Exchange Status",
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
