import streamlit as st
import pandas as pd
import requests
import urllib.parse
import time
from datetime import datetime, timezone, timedelta

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Nifty 50 Quantum Terminal",
    page_icon="🔮",
    layout="wide"
)

# --- FRESH HOLOGRAPHIC & ANIMATED FINTECH UI STYLING ---
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    /* Global Theme */
    .stApp {
        background: radial-gradient(circle at 50% 0%, #0f172a 0%, #030712 100%);
        color: #f8fafc;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Hide default streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Holographic Glow Header Container */
    .hero-header {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
        backdrop-filter: blur(24px);
        -webkit-backdrop-filter: blur(24px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 24px;
        padding: 28px 36px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        margin-bottom: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* Live Badge with Radar Wave Animation */
    .live-badge-container {
        display: inline-flex;
        align-items: center;
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.4);
        color: #34d399;
        padding: 8px 16px;
        border-radius: 50px;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        gap: 8px;
        box-shadow: 0 0 25px rgba(16, 185, 129, 0.2);
    }
    .radar-wave {
        width: 10px;
        height: 10px;
        background-color: #34d399;
        border-radius: 50%;
        position: relative;
    }
    .radar-wave::after {
        content: '';
        position: absolute;
        top: -4px; left: -4px; right: -4px; bottom: -4px;
        border: 2px solid #34d399;
        border-radius: 50%;
        animation: radar 2s infinite cubic-bezier(0.09, 0.57, 0.49, 0.9);
    }
    @keyframes radar {
        0% { transform: scale(0.8); opacity: 1; }
        100% { transform: scale(2.4); opacity: 0; }
    }

    /* Floating Mini Metrics Cards */
    .metric-card {
        background: rgba(15, 23, 42, 0.6);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 18px 22px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(59, 130, 246, 0.4);
    }

    /* Compact Table Wrapper Styling */
    div[data-testid="stDataFrame"] {
        background: rgba(15, 23, 42, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 4px;
        backdrop-filter: blur(12px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    
    /* Footer Timestamp */
    .terminal-footer {
        text-align: center;
        color: #64748b;
        font-size: 0.82rem;
        margin-top: 20px;
        font-weight: 500;
        letter-spacing: 0.02em;
    }
</style>
""", unsafe_allow_html=True)

# --- HARDCODED UPSTOX ACCESS TOKEN ---
UPSTOX_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI2M0FZSEUiLCJqdGkiOiI2YWJjYTEyNzZkMzA5YTFlMDZlYjhjNzkiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc5MDc0NjkxOSwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzkwODA1NjAwfQ.iufHPeHdNX3L4q6jcOxvPUw0Gdzjnrle0EnhaQzkL6c"

# --- NIFTY 50 CONSTITUENTS & WEIGHTS ---
RAW_DATA = [
    ("HDFCBANK", "NSE_EQ|INE040A01034", 9.89),
    ("ICICIBANK", "NSE_EQ|INE090A01021", 9.35),
    ("RELIANCE", "NSE_EQ|INE002A01018", 8.02),
    ("BHARTIARTL", "NSE_EQ|INE397D01024", 5.30),
    ("LT", "NSE_EQ|INE018A01030", 4.23),
    ("SBIN", "NSE_EQ|INE062A01020", 3.88),
    ("INFY", "NSE_EQ|INE009A01021", 3.68),
    ("AXISBANK", "NSE_EQ|INE238A01034", 3.28),
    ("KOTAKBANK", "NSE_EQ|INE237A01036", 2.84),
    ("M&M", "NSE_EQ|INE101A01026", 2.64),
    ("BAJFINANCE", "NSE_EQ|INE296A01032", 2.56),
    ("ITC", "NSE_EQ|INE154A01025", 2.33),
    ("TCS", "NSE_EQ|INE467B01029", 2.19),
    ("LTIM", "NSE_EQ|INE214T01019", 2.15),
    ("TITAN", "NSE_EQ|INE280A01028", 1.89),
    ("SUNPHARMA", "NSE_EQ|INE044A01036", 1.85),
    ("HINDUNILVR", "NSE_EQ|INE030A01027", 1.61),
    ("MARUTI", "NSE_EQ|INE585B01010", 1.53),
    ("NTPC", "NSE_EQ|INE733E01010", 1.41),
    ("TATASTEEL", "NSE_EQ|INE081A01020", 1.38),
    ("SHRIRAMFIN", "NSE_EQ|INE721A01047", 1.35),
    ("BEL", "NSE_EQ|INE263A01024", 1.34),
    ("HINDALCO", "NSE_EQ|INE038A01020", 1.33),
    ("HCLTECH", "NSE_EQ|INE860A01027", 1.29),
    ("ULTRACEMCO", "NSE_EQ|INE481G01011", 1.22),
    ("BAJAJ-AUTO", "NSE_EQ|INE917I01010", 1.22),
    ("GRASIM", "NSE_EQ|INE047A01021", 1.13),
    ("JSWSTEEL", "NSE_EQ|INE019A01038", 1.12),
    ("ADANIPORTS", "NSE_EQ|INE742F01042", 1.10),
    ("POWERGRID", "NSE_EQ|INE752E01010", 1.09),
    ("ASIANPAINT", "NSE_EQ|INE021A01026", 1.06),
    ("INDIGO", "NSE_EQ|INE646L01027", 1.04),
    ("BAJAJFINSV", "NSE_EQ|INE918I01026", 1.04),
    ("EICHERMOT", "NSE_EQ|INE066A01021", 1.00),
    ("TECHM", "NSE_EQ|INE669C01036", 0.94),
    ("NESTLEIND", "NSE_EQ|INE239A01024", 0.94),
    ("COALINDIA", "NSE_EQ|INE522F01014", 0.87),
    ("TRENT", "NSE_EQ|INE849A01020", 0.86),
    ("ONGC", "NSE_EQ|INE213A01029", 0.83),
    ("APOLLOHOSP", "NSE_EQ|INE437A01024", 0.82),
    ("ADANIENT", "NSE_EQ|INE423A01024", 0.78),
    ("CIPLA", "NSE_EQ|INE059A01026", 0.73),
    ("SBILIFE", "NSE_EQ|INE123W01016", 0.71),
    ("JIOFIN", "NSE_EQ|INE758E01017", 0.70),
    ("MAXHEALTH", "NSE_EQ|INE027H01010", 0.68),
    ("DRREDDY", "NSE_EQ|INE089A01031", 0.65),
    ("TATACONSUM", "NSE_EQ|INE192A01025", 0.61),
    ("TATAMOTORS", "NSE_EQ|INE155A01022", 0.59),
    ("HDFCLIFE", "NSE_EQ|INE795G01014", 0.53),
    ("WIPRO", "NSE_EQ|INE075A01022", 0.45)
]

def fetch_market_data(keys, token):
    headers = {
        'Accept': 'application/json', 
        'Authorization': f'Bearer {token}',
        'Api-Version': '2.0'
    }
    combined = {}
    ts = int(time.time())
    
    for i in range(0, len(keys), 15):
        chunk = keys[i:i+15]
        encoded_keys = urllib.parse.quote(','.join(chunk))
        url = f"https://api.upstox.com/v2/market-quote/quotes?instrument_key={encoded_keys}&_t={ts}"
        try:
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                res_json = res.json()
                data = res_json.get('data', {})
                if data:
                    combined.update(data)
        except Exception:
            pass
    return combined

# --- STYLISH HERO HEADER ---
st.markdown("""
<div class="hero-header">
    <div>
        <h1 style="margin: 0; font-size: 2.2rem; font-weight: 800; background: linear-gradient(90deg, #ffffff, #94a3b8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Nifty 50 Quantum Terminal</h1>
        <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 0.95rem;">Real-time index intelligence, institutional telemetry, and market depth stream.</p>
    </div>
    <div>
        <div class="live-badge-container">
            <div class="radar-wave"></div>
            Live Synchronized
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- AUTO-REFRESHING LIVE FRAGMENT (Silent background polling every 10 seconds) ---
@st.fragment(run_every=10)
def render_live_market_data():
    index_keys = ["NSE_INDEX|Nifty 50"]
    keys_list = index_keys + [item[1] for item in RAW_DATA]
    
    api_response = fetch_market_data(keys_list, UPSTOX_TOKEN)
    
    if not api_response:
        st.error("⚠️ Failed to establish connection or retrieve market quotes. Please check your network connection.")
        return
        
    lookup_map = {}
    for api_key, quote_obj in api_response.items():
        if isinstance(quote_obj, dict):
            lookup_map[api_key] = quote_obj
            lookup_map[api_key.replace(':', '|')] = quote_obj
            lookup_map[api_key.replace('|', ':')] = quote_obj
            
            inst_token = quote_obj.get('instrument_token')
            if inst_token:
                lookup_map[inst_token] = quote_obj
                
            sym = quote_obj.get('symbol')
            if sym:
                lookup_map[sym.upper()] = quote_obj

    # 1. Extract Nifty Index Quote
    nifty_quote = lookup_map.get("NSE_INDEX|Nifty 50") or lookup_map.get("NSE_INDEX:Nifty 50")
    
    # 2. Build Stock Rows & calculate market breadth
    rows = []
    gainers_count = 0
    losers_count = 0
    
    for sym, key, weight in RAW_DATA:
        quote = (
            lookup_map.get(key) or 
            lookup_map.get(key.replace('|', ':')) or 
            lookup_map.get(key.replace(':', '|')) or 
            lookup_map.get(sym.upper()) or {}
        )
        
        ltp = quote.get('last_price', 0.0)
        net_chg = quote.get('net_change', 0.0)
        
        if net_chg != 0 and ltp > 0:
            close = round(ltp - net_chg, 2)
        else:
            ohlc = quote.get('ohlc', {})
            close = ohlc.get('close', 0.0) or quote.get('prev_close_price', ltp)
        
        pct_change = quote.get('net_change_percentage', 0.0)
        if pct_change == 0.0 and close > 0 and ltp > 0:
            pct_change = round(((ltp - close) / close) * 100, 2)
            
        if pct_change > 0:
            gainers_count += 1
        elif pct_change < 0:
            losers_count += 1
            
        rows.append({
            "Symbol": sym,
            "Instrument Key": key,
            "Weight (%)": weight,
            "LTP (₹)": ltp,
            "Prev Close (₹)": close,
            "Change (%)": pct_change
        })
        
    df_result = pd.DataFrame(rows)

    # --- TOP METRICS GRID ---
    m1, m2, m3 = st.columns(3)
    
    with m1:
        if nifty_quote:
            n_ltp = nifty_quote.get('last_price', 0.0)
            n_net = nifty_quote.get('net_change', 0.0)
            n_pct = nifty_quote.get('net_change_percentage', 0.0)
            st.metric(label="📊 NIFTY 50 Index", value=f"{n_ltp:,.2f}", delta=f"{n_net:+.2f} ({n_pct:+.2f}%)")
        else:
            st.metric(label="📊 NIFTY 50 Index", value="Unavailable")
            
    with m2:
        st.metric(label="🚀 Market Gainers", value=f"{gainers_count} Stocks", delta="Positive Breadth" if gainers_count >= losers_count else None)
        
    with m3:
        st.metric(label="🔻 Market Losers", value=f"{losers_count} Stocks", delta=f"-{losers_count}" if losers_count > 0 else "0", delta_color="inverse")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- COMPACT & SLEEK DATAFRAME VIEW ---
    st.markdown("<h3 style='font-size: 1.25rem; font-weight: 700; color: #f8fafc; margin-bottom: 8px;'>📋 Constituents Live Telemetry</h3>", unsafe_allow_html=True)
    
    def style_change(val):
        color = "#34d399" if val > 0 else "#f87171" if val < 0 else "#94a3b8"
        return f"color: {color}; font-weight: 700; background-color: rgba({'52, 211, 153' if val > 0 else '248, 113, 113' if val < 0 else '148, 163, 184'}, 0.07); border-radius: 4px; padding: 2px 6px;"

    styled_df = df_result.style.format({
        "Weight (%)": "{:.2f}%",
        "LTP (₹)": "₹{:,.2f}",
        "Prev Close (₹)": "₹{:,.2f}",
        "Change (%)": "{:+.2f}%"
    }).map(style_change, subset=["Change (%)"])

    # Compact height to prevent oversize scrolling
    st.dataframe(styled_df, use_container_width=True, height=380)
    
    # India Standard Time (IST) Timestamp using standard library offsets (+5:30)
    IST = timezone(timedelta(hours=5, minutes=30))
    ist_time = datetime.now(IST).strftime('%d-%m-%Y | %I:%M:%S %p IST')
    
    st.markdown(f"""
        <div class="terminal-footer">
            ⚡ Synchronized live at {ist_time} &nbsp;&bull;&nbsp; Auto-refreshes silently every 10 seconds
        </div>
    """, unsafe_allow_html=True)

# Execute the live fragment loop
render_live_market_data()
