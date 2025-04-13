from flask import Flask, jsonify, request
import requests
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)

API_KEY = "dc9e776dd069479b906c09fbd9dcc9ba"
INDEX_SYMBOLS = {
    "NASDAQ": "IXIC",
    "NYSE": "NYA"
}
REGION_GROUPS = {
    "Americas": ["United States", "Canada", "Brazil", "Mexico", "Argentina", "Chile", "Colombia", "Peru", "Venezuela", "Jamaica"],
    "Europe": ["United Kingdom", "Germany", "France", "Italy", "Spain", "Switzerland", "Austria", "Belgium", "Czech Republic", "Denmark", "Estonia", "Finland", "Greece", "Hungary", "Iceland", "Ireland", "Latvia", "Lithuania", "Netherlands", "Norway", "Poland", "Portugal", "Romania", "Russia", "Sweden"],
    "Asia-Pacific": ["Japan", "China", "Australia", "Hong Kong", "India", "Singapore", "South Korea", "Taiwan", "Thailand", "Malaysia", "Indonesia", "New Zealand", "Philippines", "Pakistan", "Israel"],
    "Other": []  # Catch-all
}


def fetch_index(symbol: str, name: str) -> str:
    url = f"https://api.twelvedata.com/quote?symbol={symbol}&apikey={API_KEY}"
    try:
        r = requests.get(url)
        data = r.json()
        price = float(data["close"])
        change = float(data["percent_change"])
        arrow = "▲" if change >= 0 else "▼"
        return f"{name}: {price:,.2f} {arrow} {change:+.2f}%"
    except Exception:
        return f"{name}: N/A"


@app.route("/")
def market_status():
    if request.args.get("key") != "SECRET123":
        return jsonify({"error": "Unauthorized"}), 403

    r = requests.get(f"https://api.twelvedata.com/exchanges?apikey={API_KEY}")
    exchanges = r.json().get("data", [])
    now = datetime.utcnow().strftime("%m/%d/%y %I:%M%p")

    open_ex, closed_ex = [], []

    for ex in exchanges:
        name = ex.get("name")
        country = ex.get("country")
        is_open = ex.get("status") == "open"

        label = f"{'✅' if is_open else '❌'} {name} ({country}) – {'Open' if is_open else 'Closed'}"

        # Inject index stat if available
        if name in INDEX_SYMBOLS and not is_open:
            idx = fetch_index(INDEX_SYMBOLS[name], name)
            label += f" — {idx}"

        if is_open:
            open_ex.append((country, label))
        else:
            closed_ex.append((country, label))

    # Group by region
    def region_for(country: str) -> str:
        for region, countries in REGION_GROUPS.items():
            if country in countries:
                return region
        return "Other"

    region_data = defaultdict(lambda: {"open": 0, "closed": 0, "lines": []})
    for country, label in open_ex:
        region = region_for(country)
        region_data[region]["open"] += 1
        region_data[region]["lines"].append(label)

    for country, label in closed_ex:
        region = region_for(country)
        region_data[region]["closed"] += 1
        region_data[region]["lines"].append(label)

    # Format output in HTML
    lines = [
        "<div style='font-family:Arial,sans-serif;font-size:15px;color:#111;'>",
        "<h2>📊 Daily Global Exchange Status</h2>",
        f"<p><strong>Date:</strong> {now}</p>",
        f"<p>✅ <strong>Open Exchanges:</strong> {len(open_ex)}<br>❌ <strong>Closed Exchanges:</strong> {len(closed_ex)}</p>",
        "<hr style='border:none;border-top:1px solid #ddd;margin:20px 0;'>"
    ]

    for region in ["Americas", "Europe", "Asia-Pacific", "Other"]:
        data = region_data.get(region)
        if not data:
            continue
        lines.append(f"<p><strong>🌍 {region}</strong> — Open: {data['open']} | Closed: {data['closed']}</p>")
        for entry in data["lines"]:
            lines.append(f"<p style='margin:0;'>{entry}</p>")

    lines.append("</div>")

    return jsonify({
        "summary": "\n".join(line.replace("<p", "\n<p") for line in lines),  # plain text fallback
        "html": "\n".join(lines)
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
