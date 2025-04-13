from flask import Flask, jsonify, request
import requests
from datetime import datetime, time
from zoneinfo import ZoneInfo

app = Flask(__name__)

API_KEY = 'dc9e776dd069479b906c09fbd9dcc9ba'  # Replace this with your actual Twelve Data API key
TRADING_START = time(9, 0)
TRADING_END = time(17, 0)

@app.route('/')
def market_status():
    if request.args.get('key') != 'SECRET123':
        return jsonify({"error": "Unauthorized"}), 403

    r = requests.get(f'https://api.twelvedata.com/exchanges?apikey={API_KEY}')
    data = r.json().get('data', [])

    now_utc = datetime.utcnow().replace(second=0, microsecond=0)
    open_list, closed_list = [], []

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
            status_line = f"{'✅' if is_open else '❌'} {name} ({country}) – {'Open' if is_open else 'Closed'}"
            (open_list if is_open else closed_list).append(status_line)
        except Exception:
            continue

    def group_by_region(open_items, closed_items):
        regions = {
            "Americas": {"open": [], "closed": []},
            "Europe": {"open": [], "closed": []},
            "Asia-Pacific": {"open": [], "closed": []},
            "Other": {"open": [], "closed": []}
        }

        def detect_region(line):
            if any(ctry in line for ctry in ['USA', 'United States', 'Canada', 'Mexico', 'Brazil', 'Argentina']):
                return "Americas"
            elif any(ctry in line for ctry in ['UK', 'France', 'Germany', 'Switzerland', 'Sweden', 'Italy', 'Spain', 'Belgium', 'Netherlands']):
                return "Europe"
            elif any(ctry in line for ctry in ['Japan', 'China', 'Hong Kong', 'Singapore', 'Australia', 'India', 'South Korea', 'Taiwan']):
                return "Asia-Pacific"
            else:
                return "Other"

        for line in open_items:
            regions[detect_region(line)]["open"].append(line)
        for line in closed_items:
            regions[detect_region(line)]["closed"].append(line)

        return regions

    def format_regions(regions):
        output = []
        for region, data in regions.items():
            if data["open"] or data["closed"]:
                output.append(f"\n🌍 {region} — Open: {len(data['open'])} | Closed: {len(data['closed'])}")
                output.extend(data["open"] + data["closed"])
        return "\n".join(output)

    grouped = group_by_region(open_list, closed_list)
    summary_formatted = format_regions(grouped)

    return jsonify({
        "open_count": len(open_list),
        "closed_count": len(closed_list),
        "summary": summary_formatted.strip()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)

