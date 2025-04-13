from flask import Flask, jsonify, request
import requests
from datetime import datetime, time
from zoneinfo import ZoneInfo

app = Flask(__name__)

API_KEY = 'dc9e776dd069479b906c09fbd9dcc9ba'
TRADING_START = time(9, 0)
TRADING_END = time(17, 0)

REGIONS = {
    "Americas": [
        "United States", "Canada", "Brazil", "Argentina", "Mexico", "Chile", "Colombia", "Peru", "Jamaica", "Venezuela"
    ],
    "Europe": [
        "Germany", "France", "United Kingdom", "Switzerland", "Sweden", "Spain", "Italy", "Portugal", "Austria",
        "Belgium", "Denmark", "Finland", "Greece", "Hungary", "Iceland", "Ireland", "Netherlands", "Norway", "Poland",
        "Romania", "Russia", "Czech Republic", "Estonia", "Latvia", "Lithuania"
    ],
    "Asia-Pacific": [
        "China", "Japan", "Hong Kong", "India", "Australia", "New Zealand", "Singapore", "South Korea", "Taiwan",
        "Thailand", "Indonesia", "Malaysia", "Philippines", "Pakistan", "Israel"
    ],
    "Other": [
        "South Africa", "Turkey", "Egypt", "Saudi Arabia", "United Arab Emirates", "Botswana", "Qatar", "Kuwait"
    ]
}

def get_region(country: str) -> str:
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
    exchanges = r.json().get('data', [])

    # Deduplicate exchanges
    seen = set()
    unique = []
    for ex in exchanges:
        key = (ex.get('name'), ex.get('country'))
        if key not in seen:
            seen.add(key)
            unique.append(ex)
        else:
            print(f"🟡 Skipping duplicate: {key}")

    now_utc = datetime.utcnow().replace(second=0, microsecond=0)
    open_list, closed_list = [], []

    for ex in unique:
        try:
            name = ex.get('name')
            country = ex.get('country')
            tz = ex.get('timezone')
            if not all([name, country, tz]):
                continue
            now_local = now_utc.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo(tz)).timetz()
            is_open = TRADING_START <= now_local <= TRADING_END
            region = get_region(country)
            status_line = f"{'✅' if is_open else '❌'} {name} ({country}) – {'Open' if is_open else 'Closed'}"
            if name in ["NASDAQ", "NYSE"]:
                symbol = "IXIC" if name == "NASDAQ" else "NYA"
                index_info = fetch_index(symbol, name)
                status_line += f" — {index_info}"
            (open_list if is_open else closed_list).append((region, status_line))
        except Exception as e:
            print("⚠️ Error:", e)

    # Group by region
    def group_by_region(entries):
        grouped = {}
        for region, line in entries:
            grouped.setdefault(region, []).append(line)
        return grouped

    grouped_open = group_by_region(open_list)
    grouped_closed = group_by_region(closed_list)

    def format_grouped(grouped):
        result = []
        for region in sorted(grouped):
            region_list = grouped[region]
            result.append(f"\n🌍 {region} — Open: {sum('✅' in l for l in region_list)} | Closed: {sum('❌' in l for l in region_list)}\n")
            result.extend(region_list)
        return "\n".join(result)

    summary = (
        f"📊 <b>Daily Global Exchange Status</b>\n\n"
        f"<b>Date:</b> {datetime.utcnow().strftime('%m/%d/%y %I:%M%p')}\n\n"
        f"✅ <b>Open Exchanges:</b> {len(open_list)}\n"
        f"❌ <b>Closed Exchanges:</b> {len(closed_list)}\n"
        f"{format_grouped(group_by_region(open_list + closed_list))}"
    )

    return jsonify({
        "open_count": len(open_list),
        "closed_count": len(closed_list),
        "summary": summary
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
