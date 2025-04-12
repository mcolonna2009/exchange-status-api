from flask import Flask, jsonify
import requests
from datetime import datetime, time
from zoneinfo import ZoneInfo

app = Flask(__name__)

API_KEY = 'dc9e776dd069479b906c09fbd9dcc9ba'  # ⬅️ Replace this!

TRADING_START = time(9, 0)
TRADING_END = time(17, 0)

@app.route('/')
def market_status():
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
            if local_time.weekday() < 5 and TRADING_START <= local_time.time() <= TRADING_END:
                open_list.append(f"✅ {name} ({country}) – Open")
            else:
                closed_list.append(f"❌ {name} ({country}) – Closed")
        except:
            continue

    return jsonify({
        "open_count": len(open_list),
        "closed_count": len(closed_list),
        "summary": "\n".join(open_list + closed_list)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
