#!/usr/bin/env python3
"""Fetches market data and writes data.json for the website."""

import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
import pytz

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False

def market_status():
    et = pytz.timezone("America/New_York")
    now = datetime.now(et)
    if now.weekday() >= 5:
        return "Friday close — market closed"
    open_t  = now.replace(hour=9,  minute=30, second=0, microsecond=0)
    close_t = now.replace(hour=16, minute=0,  second=0, microsecond=0)
    if open_t <= now <= close_t:
        return f"Live — as of {now.strftime('%H:%M ET')}"
    return "Prior close — market closed"

def fetch_stocks():
    if not HAS_YFINANCE:
        return {}
    tickers = {"S&P 500":"^GSPC","Nasdaq":"^IXIC","Dow Jones":"^DJI","Russell 2000":"^RUT"}
    out = {}
    for name, sym in tickers.items():
        try:
            t = yf.Ticker(sym)
            i = t.fast_info
            pct = ((i.last_price - i.previous_close) / i.previous_close) * 100
            out[name] = {"price": round(i.last_price, 2), "change_pct": round(pct, 2)}
        except: pass
    return out

def fetch_commodities():
    if not HAS_YFINANCE:
        return {}
    tickers = {"Gold":"GC=F","Oil (WTI)":"CL=F","Silver":"SI=F"}
    out = {}
    for name, sym in tickers.items():
        try:
            t = yf.Ticker(sym)
            i = t.fast_info
            pct = ((i.last_price - i.previous_close) / i.previous_close) * 100
            out[name] = {"price": round(i.last_price, 2), "change_pct": round(pct, 2)}
        except: pass
    return out

def fetch_crypto():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,binancecoin&vs_currencies=usd&include_24hr_change=true"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "pm-ai-os/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        mapping = {"bitcoin":"BTC","ethereum":"ETH","solana":"SOL","binancecoin":"BNB"}
        return {sym: {"price": data[cid]["usd"], "change_pct": round(data[cid].get("usd_24h_change",0),2)}
                for cid, sym in mapping.items() if cid in data}
    except:
        return {}

def fetch_headlines():
    feeds = [
        ("CNBC", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114"),
        ("Reuters", "https://feeds.reuters.com/reuters/businessNews"),
        ("MarketWatch", "https://feeds.marketwatch.com/marketwatch/topstories/"),
    ]
    headlines = []
    for source, url in feeds:
        if len(headlines) >= 5: break
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "pm-ai-os/1.0"})
            with urllib.request.urlopen(req, timeout=8) as r:
                tree = ET.parse(r)
            for item in tree.findall(".//item")[:2]:
                t = item.find("title")
                if t is not None and t.text:
                    headlines.append({"source": source, "title": t.text.strip()})
                    if len(headlines) >= 5: break
        except: pass
    return headlines

pt = pytz.timezone("America/Los_Angeles")
data = {
    "generated_at": datetime.now(pt).strftime("%A, %B %d %Y  %H:%M PT"),
    "market_status": market_status(),
    "stocks": fetch_stocks(),
    "commodities": fetch_commodities(),
    "crypto": fetch_crypto(),
    "headlines": fetch_headlines(),
}

with open("data.json", "w") as f:
    json.dump(data, f, indent=2)

print(f"data.json written — {len(data['stocks'])} stocks, {len(data['crypto'])} crypto, {len(data['headlines'])} headlines")
