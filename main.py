from flask import Flask, request, jsonify
import requests
from datetime import datetime, time
from zoneinfo import ZoneInfo

app = Flask(__name__)
API_KEY = 'dc9e776dd069479b906c09fbd9dcc9ba'
TRADING_START = time(9, 0)
TRADING_END = time(17, 0)

# Map countries to regions
REGIONS = {
    "Americas": ["United States", "Canada", "Mexico", "Brazil", "Argentina", "Chile", "Colombia", "Peru", "Jamaica", "Venezuela"],
    "Europe": ["Germany", "France", "United Kingdom", "Italy", "Spain", "Portugal", "Sweden", "Austria", "Belgium", "Denmark", "Finland", "Greece", "Ireland", "Netherlands", "Norway", "Poland", "Russia", "Switzerland", "Czech Republic", "Hungary", "Estonia", "Latvia", "Lithuania", "Romania"],
    "Asia-Pacific": ["Japan", "China", "Hong Kong", "Australia", "New Zealand", "India", "South Korea", "Singapore", "Taiwan", "Thailand", "Malaysia", "Indonesia", "Pakistan", "Philippines"],
    "Other": []
}

INDEX_SYMBOLS = {
    "NASDAQ": "IXIC",
    "NYSE": "NYA"
}

def fetch_index(symbol, name):
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
    data = r.json().get("data", [])

    now_utc = datetime.utcnow().replace(second=0, microsecond=0)
    open_exchanges, closed_exchanges = [], []

    for ex in data:
        try:
            name = ex["name"]
            code = ex["code"]
            country = ex["country"]
            tz = ZoneInfo(ex["timezone"])
            now_local = now_utc.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)

            is_open = TRADING_START <= now_local.time() <= TRADING_END
            info = {
                "label": f"{name} ({country})",
                "region": next((r for r, c in REGIONS.items() if country in c), "Other"),
                "index": INDEX_SYMBOLS.get(name),
                "status": "Open" if is_open else "Closed"
            }
            (open_exchanges if is_open else closed_exchanges).append(info)
        except:
            continue

    # Group by region
    all_exchanges = open_exchanges + closed_exchanges
    grouped = {}
    for ex in all_exchanges:
        region = ex["region"]
        grouped.setdefault(region, []).append(ex)

    # Build formatted HTML output
    timestamp = datetime.utcnow().strftime("%m/%d/%y %I:%M%p")
    lines = [
        f"<h2>📊 Daily Global Exchange Status</h2>",
        f"<p><strong>Date:</strong> {timestamp}</p>",
        f"<p>✅ <strong>Open Exchanges:</strong> {len(open_exchanges)}<br>❌ <strong>Closed Exchanges:</strong> {len(closed_exchanges)}</p>",
        "<hr>"
    ]

    for region, items in grouped.items():
        open_count = sum(1 for ex in items if ex["status"] == "Open")
        closed_count = sum(1 for ex in items if ex["status"] == "Closed")
        lines.append(f"<h3>🌍 {region} — Open: {open_count} | Closed: {closed_count}</h3>")
        for ex in items:
            label = ex["label"]
            status = ex["status"]
            idx = fetch_index(ex["index"], ex["index"]) if ex.get("index") else ""
            prefix = "✅" if status == "Open" else "❌"
            lines.append(f"{prefix} {label} – {status}{f' — {idx}' if idx else ''}<br>")

    return jsonify({"summary": "".join(lines)})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3000)
