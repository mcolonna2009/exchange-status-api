from flask import Flask, jsonify, request
import requests
from datetime import datetime, time
from zoneinfo import ZoneInfo

app = Flask(__name__)

API_KEY = 'dc9e776dd069479b906c09fbd9dcc9ba'  # Replace with your TwelveData API key
TRADING_START = time(9, 0)
TRADING_END = time(17, 0)

# Basic region mapping for grouping
REGION_MAP = {
    "Argentina": "Americas",
    "Brazil": "Americas",
    "Canada": "Americas",
    "Mexico": "Americas",
    "United States": "Americas",
    "Chile": "Americas",
    "Colombia": "Americas",
    "Jamaica": "Americas",
    "Venezuela": "Americas",

    "Austria": "Europe",
    "Belgium": "Europe",
    "France": "Europe",
    "Germany": "Europe",
    "Italy": "Europe",
    "Netherlands": "Europe",
    "Portugal": "Europe",
    "Spain": "Europe",
    "Sweden": "Europe",
    "Switzerland": "Europe",
    "United Kingdom": "Europe",
    "Czech Republic": "Europe",
    "Denmark": "Europe",
    "Estonia": "Europe",
    "Finland": "Europe",
    "Greece": "Europe",
    "Hungary": "Europe",
    "Iceland": "Europe",
    "Ireland": "Europe",
    "Latvia": "Europe",
    "Lithuania": "Europe",
    "Norway": "Europe",
    "Poland": "Europe",
    "Romania": "Europe",
    "Russia": "Europe",

    "Australia": "Asia-Pacific",
    "China": "Asia-Pacific",
    "Hong Kong": "Asia-Pacific",
    "India": "Asia-Pacific",
    "Indonesia": "Asia-Pacific",
    "Israel": "Asia-Pacific",
    "Japan": "Asia-Pacific",
    "Kuwait": "Asia-Pacific",
    "Malaysia": "Asia-Pacific",
    "New Zealand": "Asia-Pacific",
    "Pakistan": "Asia-Pacific",
    "Philippines": "Asia-Pacific",
    "Singapore": "Asia-Pacific",
    "South Korea": "Asia-Pacific",
    "Taiwan": "Asia-Pacific",
    "Thailand": "Asia-Pacific",

    "Botswana": "Other",
    "Egypt": "Other",
    "Qatar": "Other",
    "Saudi Arabia": "Other",
    "South Africa": "Other",
    "Turkey": "Other",
    "United Arab Emirates": "Other",
}

# Optional: fetch a sample index (if market is closed)
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
    open_exchanges, closed_exchanges = 0, 0
    region_stats = {}

    for ex in data:
        try:
            name = ex.get("name")
            country = ex.get("country")
            timezone = ex.get("timezone")
            symbol = ex.get("code")
            region = REGION_MAP.get(country, "Other")

            if not timezone:
                continue

            local_time = now_utc.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo(timezone)).time()
            is_open = TRADING_START <= local_time <= TRADING_END

            status_line = f"{'✅' if is_open else '❌'} {name} ({country}) – {'Open' if is_open else 'Closed'}"

            if not is_open and symbol in ['NASDAQ', 'NYSE']:
                index_note = fetch_index(symbol, symbol)
                status_line += f" — {index_note}"

            if region not in region_stats:
                region_stats[region] = {"open": 0, "closed": 0, "lines": []}

            if is_open:
                open_exchanges += 1
                region_stats[region]["open"] += 1
            else:
                closed_exchanges += 1
                region_stats[region]["closed"] += 1

            region_stats[region]["lines"].append(status_line)
        except Exception:
            continue

    lines = []
    lines.append("📊 <strong>Daily Global Exchange Status</strong><br>")
    lines.append(f"<br><strong>Date:</strong> {datetime.now().strftime('%m/%d/%y %I:%M%p')}<br>")
    lines.append(f"<br>✅ <strong>Open Exchanges:</strong> {open_exchanges}<br>❌ <strong>Closed Exchanges:</strong> {closed_exchanges}<br>")

    for region, stats in region_stats.items():
        lines.append(f"<br>🌍 <strong>{region}</strong> — Open: {stats['open']} | Closed: {stats['closed']}<br>")
        lines.extend([f"{line}<br>" for line in stats["lines"]])

    return jsonify({
        "open_count": open_exchanges,
        "closed_count": closed_exchanges,
        "summary": "\n".join(lines)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)from flask import Flask, jsonify, request
import requests
from datetime import datetime, time
from zoneinfo import ZoneInfo

app = Flask(__name__)

API_KEY = 'dc9e776dd069479b906c09fbd9dcc9ba'  # Replace with your TwelveData API key
TRADING_START = time(9, 0)
TRADING_END = time(17, 0)

# Basic region mapping for grouping
REGION_MAP = {
    "Argentina": "Americas",
    "Brazil": "Americas",
    "Canada": "Americas",
    "Mexico": "Americas",
    "United States": "Americas",
    "Chile": "Americas",
    "Colombia": "Americas",
    "Jamaica": "Americas",
    "Venezuela": "Americas",

    "Austria": "Europe",
    "Belgium": "Europe",
    "France": "Europe",
    "Germany": "Europe",
    "Italy": "Europe",
    "Netherlands": "Europe",
    "Portugal": "Europe",
    "Spain": "Europe",
    "Sweden": "Europe",
    "Switzerland": "Europe",
    "United Kingdom": "Europe",
    "Czech Republic": "Europe",
    "Denmark": "Europe",
    "Estonia": "Europe",
    "Finland": "Europe",
    "Greece": "Europe",
    "Hungary": "Europe",
    "Iceland": "Europe",
    "Ireland": "Europe",
    "Latvia": "Europe",
    "Lithuania": "Europe",
    "Norway": "Europe",
    "Poland": "Europe",
    "Romania": "Europe",
    "Russia": "Europe",

    "Australia": "Asia-Pacific",
    "China": "Asia-Pacific",
    "Hong Kong": "Asia-Pacific",
    "India": "Asia-Pacific",
    "Indonesia": "Asia-Pacific",
    "Israel": "Asia-Pacific",
    "Japan": "Asia-Pacific",
    "Kuwait": "Asia-Pacific",
    "Malaysia": "Asia-Pacific",
    "New Zealand": "Asia-Pacific",
    "Pakistan": "Asia-Pacific",
    "Philippines": "Asia-Pacific",
    "Singapore": "Asia-Pacific",
    "South Korea": "Asia-Pacific",
    "Taiwan": "Asia-Pacific",
    "Thailand": "Asia-Pacific",

    "Botswana": "Other",
    "Egypt": "Other",
    "Qatar": "Other",
    "Saudi Arabia": "Other",
    "South Africa": "Other",
    "Turkey": "Other",
    "United Arab Emirates": "Other",
}

# Optional: fetch a sample index (if market is closed)
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
    open_exchanges, closed_exchanges = 0, 0
    region_stats = {}

    for ex in data:
        try:
            name = ex.get("name")
            country = ex.get("country")
            timezone = ex.get("timezone")
            symbol = ex.get("code")
            region = REGION_MAP.get(country, "Other")

            if not timezone:
                continue

            local_time = now_utc.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo(timezone)).time()
            is_open = TRADING_START <= local_time <= TRADING_END

            status_line = f"{'✅' if is_open else '❌'} {name} ({country}) – {'Open' if is_open else 'Closed'}"

            if not is_open and symbol in ['NASDAQ', 'NYSE']:
                index_note = fetch_index(symbol, symbol)
                status_line += f" — {index_note}"

            if region not in region_stats:
                region_stats[region] = {"open": 0, "closed": 0, "lines": []}

            if is_open:
                open_exchanges += 1
                region_stats[region]["open"] += 1
            else:
                closed_exchanges += 1
                region_stats[region]["closed"] += 1

            region_stats[region]["lines"].append(status_line)
        except Exception:
            continue

    lines = []
    lines.append("📊 <strong>Daily Global Exchange Status</strong><br>")
    lines.append(f"<br><strong>Date:</strong> {datetime.now().strftime('%m/%d/%y %I:%M%p')}<br>")
    lines.append(f"<br>✅ <strong>Open Exchanges:</strong> {open_exchanges}<br>❌ <strong>Closed Exchanges:</strong> {closed_exchanges}<br>")

    for region, stats in region_stats.items():
        lines.append(f"<br>🌍 <strong>{region}</strong> — Open: {stats['open']} | Closed: {stats['closed']}<br>")
        lines.extend([f"{line}<br>" for line in stats["lines"]])

    return jsonify({
        "open_count": open_exchanges,
        "closed_count": closed_exchanges,
        "summary": "\n".join(lines)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
