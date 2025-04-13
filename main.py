# main.py

from flask import Flask, jsonify, request
import requests
from datetime import datetime, time
from zoneinfo import ZoneInfo

app = Flask(__name__)

API_KEY = 'dc9e776dd069479b906c09fbd9dcc9ba'  # replace this with your actual key
TRADING_START = time(9, 0)
TRADING_END = time(17, 0)

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

    try:
        r = requests.get(f'https://api.twelvedata.com/exchanges?apikey={API_KEY}')
        all_exchanges = r.json().get('data', [])
    except Exception:
        return jsonify({"error": "API failure"}), 500

    now_utc = datetime.utcnow().replace(second=0, microsecond=0)
    grouped = {}

    seen = set()

    for ex in all_exchanges:
        name = ex.get('name')
        country = ex.get('country')
        code = ex.get('code')
        region = ex.get('region')
        timezone = ex.get('timezone')

        key = (name, country)
        if key in seen:
            continue
        seen.add(key)

        try:
            local = now_utc.astimezone(ZoneInfo(timezone))
            is_open = TRADING_START <= local.time() <= TRADING_END
        except Exception:
            is_open = False

        icon = "✅" if is_open else "❌"
        index_line = ""

        if name in ["NASDAQ", "NYSE"]:
            index_line = f" — {fetch_index('IXIC' if name == 'NASDAQ' else 'NYA', name)}"

        status_line = f"{icon} {name} ({country}) – {'Open' if is_open else 'Closed'}{index_line}"

        if region not in grouped:
            grouped[region] = {"open": 0, "closed": 0, "exchanges": []}

        grouped[region]["open" if is_open else "closed"] += 1
        grouped[region]["exchanges"].append(status_line)

    total_open = sum(r["open"] for r in grouped.values())
    total_closed = sum(r["closed"] for r in grouped.values())

    lines = [
        "<div style='font-family:Arial, sans-serif;'>",
        "<h2>📊 <strong>Daily Global Exchange Status</strong></h2>",
        f"<p><strong>Date:</strong> {datetime.now().strftime('%m/%d/%y %I:%M%p')}</p>",
        f"<p>✅ <strong>Open Exchanges:</strong> {total_open}<br>❌ <strong>Closed Exchanges:</strong> {total_closed}</p>",
    ]

    for region, stats in grouped.items():
        lines.append(f"<h3>🌍 <strong>{region}</strong> — Open: {stats['open']} | Closed: {stats['closed']}</h3>")
        lines.extend(f"<p>{line}</p>" for line in stats["exchanges"])

    lines.append("</div>")

    return jsonify({
        "open_count": total_open,
        "closed_count": total_closed,
        "summary": "\n".join(lines)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)


