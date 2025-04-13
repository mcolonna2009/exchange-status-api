from flask import Flask, jsonify, request
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

app = Flask(__name__)

API_KEY = 'dc9e776dd069479b906c09fbd9dcc9ba'  # Replace with your actual API key

INDEX_SYMBOLS = {
    'NYSE': 'NYA',
    'NASDAQ': 'IXIC'
}

REGIONS = {
    'Americas': [],
    'Europe': [],
    'Asia-Pacific': [],
    'Other': []
}

@app.route("/")
def market_status():
    if request.args.get('key') != 'SECRET123':
        return jsonify({"error": "Unauthorized"}), 403

    r = requests.get(f"https://api.twelvedata.com/exchanges?apikey={API_KEY}")
    data = r.json().get("data", [])

    now_utc = datetime.utcnow().replace(second=0, microsecond=0)

    total_open = 0
    total_closed = 0
    region_stats = {k: {"open": 0, "closed": 0, "exchanges": []} for k in REGIONS}

    seen = set()

    for ex in data:
        try:
            name = ex["name"]
            country = ex["country"]
            region = ex.get("region", "Other")
            symbol = ex.get("code")

            if (name, country) in seen:
                continue
            seen.add((name, country))

            tz = ex.get("timezone")
            if not tz:
                continue

            now_local = now_utc.astimezone(ZoneInfo(tz))
            current_time = now_local.time()

            status = "Closed"
            is_open = False
            if ex.get("open") and ex.get("close"):
                open_time = datetime.strptime(ex["open"], "%H:%M").time()
                close_time = datetime.strptime(ex["close"], "%H:%M").time()
                if open_time <= current_time <= close_time:
                    status = "Open"
                    is_open = True

            index_line = ""
            if symbol in INDEX_SYMBOLS:
                index = INDEX_SYMBOLS[symbol]
                idx_data = requests.get(f"https://api.twelvedata.com/quote?symbol={index}&apikey={API_KEY}").json()
                change = idx_data.get("percent_change")
                arrow = "▲" if change and float(change) >= 0 else "▼"
                index_line = f" — {symbol}: {idx_data.get('close', 'N/A')} {arrow} {float(change):+.2f}%" if change else f" — {symbol}: N/A"

            icon = "✅" if is_open else "❌"
            region = region if region in region_stats else "Other"
            status_line = f"{icon} {name} ({country}) – {status}{index_line}"
            region_stats[region]["open" if is_open else "closed"] += 1
            region_stats[region]["exchanges"].append(status_line)

            total_open += is_open
            total_closed += not is_open

        except Exception:
            continue

    summary = []
    summary.append("<div style='font-family:Arial; font-size:16px;'>")
    summary.append("<h2>📊 Daily Global Exchange Status</h2>")
    summary.append(f"<p><strong>Date:</strong> {now_utc.strftime('%m/%d/%y %I:%M%p')}</p>")
    summary.append(f"<p>✅ <strong>Open Exchanges:</strong> {total_open}<br>❌ <strong>Closed Exchanges:</strong> {total_closed}</p>")

    for region, stats in region_stats.items():
        summary.append(f"<h3>🌍 {region} — Open: {stats['open']} | Closed: {stats['closed']}</h3>")
        for line in stats["exchanges"]:
            summary.append(f"<p>{line}</p>")

    summary.append("</div>")

    return jsonify({
        "open_count": total_open,
        "closed_count": total_closed,
        "summary": "\n".join(summary)
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
