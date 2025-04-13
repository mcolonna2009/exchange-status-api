from flask import Flask, jsonify, request
import requests
from datetime import datetime, time
from zoneinfo import ZoneInfo

app = Flask(__name__)

API_KEY = 'dc9e776dd069479b906c09fbd9dcc9ba'  # ← replace this with your actual API key
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

    r = requests.get(f'https://api.twelvedata.com/exchanges?apikey={API_KEY}')
    data = r.json().get('data', [])

    now_utc = datetime.utcnow().replace(second=0, microsecond=0)
    open_list, closed_list = [], []

    for ex in data:
        try:
            name = ex.get


