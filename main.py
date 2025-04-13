# main.py

from flask import Flask, jsonify, request
import requests
from datetime import datetime, time
from zoneinfo import ZoneInfo

app = Flask(__name__)

API_KEY = 'YOUR_TWELVE_DATA_API_KEY'  # Replace with actual key
TRADING_START = time(9, 0)
TRADING_END = time(17, 0)

EXCHANGE_REGIONS = {
    'BCBA': 'Americas', 'Bovespa': 'Americas', 'TSX': 'Americas', 'TSXV': 'Americas',
    'NYSE': 'Americas', 'NASDAQ': 'Americas', 'CBOE': 'Americas', 'IEX': 'Americas',
    'LSE': 'Europe', 'Euronext': 'Europe', 'FSX': 'Europe', 'XETR': 'Europe', 'BME': 'Europe',
    'ASX': 'Asia-Pacific', 'HKEX': 'Asia-Pacific', 'NSE': 'Asia-Pacific', 'JPX': 'Asia-Pacific',
    # add more as needed
}

INDEX_SYMBOLS = {
    'NASDAQ': ('IXIC', 'NASDAQ'),
    'NYSE': ('NYA', 'NYSE'),
    'S&P 500': ('INX', 'S&P 500')
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
            code = ex.get('code')
            local_time = now_utc.astimezone(ZoneInfo(tz))
            region = EXCHANGE_REGIONS.get(code, "Other")

            if region not in region_stats:
                region_stats[region] = {
                    "open": 0,
                    "closed": 0,
                    "exchanges": []
                }

            is_open = (
                local_time.weekday() < 5 and
                TRADING_START <= local_time.time() <= TRADING_END
            )

            index_status = ""
            if code in INDEX_SYMBOLS:
                symbol, display = INDEX_SYMBOLS[code]
                index_status = f" — {fetch_index(symbol, display)}"

            status_line = f"{'✅' if is_open else '❌'} {name} ({country}) – {'Open' if is_open else 'Closed'}{index_status}"
            if is_open:
                region_stats[region]["open"] += 1
            else:
                region_stats[region]["closed"] += 1
            region_stats[region]["exchanges"].append(status_line)
        except Exception:
            continue

    total_open = sum(r["open"] for r in region_stats.values())
    total_closed = sum(r["closed"] for r in region_stats.values())

    header = [
        "📊 Daily Global Exchange Status",
        "",
        f"Date: {datetime.now().strftime('%m/%d/%y %I:%M%p')}",
        "",
        f"✅ Open Exchanges: {total_open}",
        f"❌ Closed Exchanges: {total_closed}",
        ""
    ]

    lines = header
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
