from flask import Flask, jsonify, request
import requests
from datetime import datetime, time
from zoneinfo import ZoneInfo

app = Flask(__name__)

API_KEY = 'dc9e776dd069479b906c09fbd9dcc9ba'  # Replace with your actual TwelveData API key
SECRET_KEY = 'SECRET123'
TRADING_START = time(9, 0)
TRADING_END = time(17, 0)

INDEX_SYMBOLS = {
    'NASDAQ': 'IXIC',
    'NYSE': 'NYA'
}

REGIONS = {
    "Americas": ["Argentina", "Brazil", "Canada", "Chile", "Colombia", "Jamaica", "Mexico", "Peru", "United States", "Venezuela"],
    "Europe": ["Austria", "Belgium", "Czech Republic", "Denmark", "Estonia", "Finland", "France", "Germany", "Greece", "Hungary", "Iceland", "Ireland", "Italy", "Latvia", "Lithuania", "Netherlands", "Norway", "Poland", "Portugal", "Romania", "Russia", "Spain", "Sweden", "Switzerland", "United Kingdom"],
    "Asia-Pacific": ["Australia", "China", "Hong Kong", "India", "Indonesia", "Israel", "Japan", "Malaysia", "New Zealand", "Pakistan", "Philippines", "Singapore", "South Korea", "Taiwan", "Thailand"],
    "Other": []
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

@app.route('/')
def market_status():
    if request.args.get('key') != SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 403

    r = requests.get(f'https://api.twelvedata.com/exchanges?apikey={API_KEY}')
    data = r.json().get('data', [])
    
    seen = set()
    grouped = {region: {"open": [], "closed": []} for region in REGIONS}
    now_utc = datetime.utcnow()

    for ex in data:
        name = ex.get('name')
        country = ex.get('country')
        tz = ex.get('timezone')
        code = ex.get('code')

        key = f"{name}|{country}"
        if key in seen:
            continue
        seen.add(key)

        try:
            local_now = now_utc.replace(tzinfo=ZoneInfo('UTC')).astimezone(ZoneInfo(tz)).timetz()
            is_open = TRADING_START <= local_now <= TRADING_END
        except Exception:
            is_open = False

        status = "✅" if is_open else "❌"
        region = next((r for r, c_list in REGIONS.items() if country in c_list), "Other")
        if is_open:
            grouped[region]["open"].append(f"{status} {name} ({country}) – Open")
        else:
            suffix = ""
            if name in INDEX_SYMBOLS:
                suffix = f" — {fetch_index(INDEX_SYMBOLS[name], name)}"
            grouped[region]["closed"].append(f"{status} {name} ({country}) – Closed{suffix}")

    html = "<div style='font-family:Arial, sans-serif;'>"
    html += "<h2>📊 Daily Global Exchange Status</h2>"
    html += f"<p><strong>Date:</strong> {datetime.now().strftime('%m/%d/%y %I:%M%p')}</p>"

    all_open = sum(len(g["open"]) for g in grouped.values())
    all_closed = sum(len(g["closed"]) for g in grouped.values())
    html += f"<p>✅ <strong>Open Exchanges:</strong> {all_open}<br>"
    html += f"❌ <strong>Closed Exchanges:</strong> {all_closed}</p>"

    for region, lists in grouped.items():
        html += f"<h3>🌍 {region} — Open: {len(lists['open'])} | Closed: {len(lists['closed'])}</h3>"
        for line in lists['open'] + lists['closed']:
            html += f"<p>{line}</p>"

    html += "</div>"

    return jsonify({
        "open_count": all_open,
        "closed_count": all_closed,
        "summary": html
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
