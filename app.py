import streamlit as st
import pandas as pd
import requests
import urllib.parse
import time
from datetime import datetime
import pytz
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Apex Institutional Desk | Nifty 50",
    page_icon="⚡",
    layout="wide"
)

# --- APEX INSTITUTIONAL FINTECH UI STYLING ---
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

    /* Global Theme */
    .stApp {
        background: radial-gradient(circle at 50% -20%, #1e1b4b 0%, #090a0f 60%, #030407 100%);
        color: #f1f5f9;
        font-family: 'Outfit', sans-serif;
    }
    
    /* Hide default streamlit chrome */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Executive Header Container */
    .exec-header {
        background: linear-gradient(135deg, rgba(20, 24, 38, 0.85) 0%, rgba(10, 13, 20, 0.95) 100%);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 20px;
        padding: 28px 36px;
        box-shadow: 0 24px 50px rgba(0, 0, 0, 0.7), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        margin-bottom: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* Status Pill with Pulsing Indicator */
    .status-pill {
        display: inline-flex;
        align-items: center;
        background: rgba(16, 185, 129, 0.08);
        border: 1px solid rgba(16, 185, 129, 0.3);
        color: #34d399;
        padding: 7px 16px;
        border-radius: 30px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        gap: 8px;
        box-shadow: 0 0 20px rgba(16, 185, 129, 0.15);
    }
    .pulse-dot {
        width: 8px;
        height: 8px;
        background-color: #34d399;
        border-radius: 50%;
        box-shadow: 0 0 10px #34d399;
        animation: pulse 1.8s infinite ease-in-out;
    }
    @keyframes pulse {
        0% { transform: scale(0.95); opacity: 0.8; }
        50% { transform: scale(1.4); opacity: 0.3; }
        100% { transform: scale(0.95); opacity: 0.8; }
    }

    /* Executive Metric Card */
    .exec-card {
        background: linear-gradient(145deg, rgba(18, 22, 33, 0.8) 0%, rgba(11, 14, 22, 0.9) 100%);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 22px 26px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .exec-card:hover {
        transform: translateY(-3px);
        border-color: rgba(99, 102, 241, 0.4);
        box-shadow: 0 15px 35px rgba(99, 102, 241, 0.15);
    }

    /* Section Container for Visual Balance */
    .section-container {
        background: linear-gradient(145deg, rgba(18, 22, 33, 0.6) 0%, rgba(11, 14, 22, 0.7) 100%);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 12px 40px rgba(0,0,0,0.5);
        height: 100%;
    }

    /* Compact Table Wrapper Styling */
    div[data-testid="stDataFrame"] {
        background: rgba(13, 17, 26, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 6px;
        backdrop-filter: blur(16px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.6);
    }
    
    /* Terminal Footer */
    .terminal-footer {
        text-align: center;
        color: #64748b;
        font-size: 0.8rem;
        margin-top: 24px;
        font-weight: 500;
        letter-spacing: 0.03em;
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

# --- EXECUTIVE HEADER ---
st.markdown("""
<div class="exec-header">
    <div>
        <div style="font-size: 0.75rem; font-weight: 700; color: #818cf8; text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 4px;">Apex Institutional Desk</div>
        <h1 style="margin: 0; font-size: 2rem; font-weight: 800; background: linear-gradient(90deg, #ffffff, #94a3b8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Nifty 50 Telemetry Matrix</h1>
        <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 0.9rem;">Real-time index intelligence, institutional asset flow, and constituent depth stream.</p>
    </div>
    <div>
        <div class="status-pill">
            <div class="pulse-dot"></div>
            Live Synchronized
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- AUTO-REFRESHING LIVE FRAGMENT ---
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
    nifty_net = nifty_quote.get('net_change', 0.0) if nifty_quote else 0.0
    nifty_ltp = nifty_quote.get('last_price', 0.0) if nifty_quote else 0.0
    nifty_pct = nifty_quote.get('net_change_percentage', 0.0) if nifty_quote else 0.0
    
    # 2. Build Stock Rows & Calculate Contributions
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
            
        # Estimated point contribution to Nifty
        est_contrib = round((pct_change / 100.0) * weight * (nifty_ltp / 100.0) * 0.15, 2) if nifty_ltp > 0 else 0.0
            
        rows.append({
            "Symbol": sym,
            "Instrument Key": key,
            "Weight (%)": weight,
            "LTP (₹)": ltp,
            "Prev Close (₹)": close,
            "Change (%)": pct_change,
            "Contribution": est_contrib
        })
        
    df_result = pd.DataFrame(rows)

    # --- TOP METRICS GRID ---
    m1, m2, m3 = st.columns(3)
    
    with m1:
        if nifty_quote:
            color_hex = "#34d399" if nifty_net >= 0 else "#f87171"
            sign_str = "+" if nifty_net >= 0 else ""
            st.markdown(f"""
            <div class="exec-card">
                <div style="font-size: 0.75rem; color: #94a3b8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">📊 Nifty 50 Index</div>
                <div style="font-size: 1.85rem; font-weight: 800; color: #ffffff; margin-top: 6px; letter-spacing: -0.02em;">{nifty_ltp:,.2f}</div>
                <div style="font-size: 0.85rem; font-weight: 700; color: {color_hex}; margin-top: 4px;">{sign_str}{nifty_net:,.2f} ({sign_str}{nifty_pct:.2f}%)</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="exec-card">
                <div style="font-size: 0.75rem; color: #94a3b8; font-weight: 700; text-transform: uppercase;">📊 Nifty 50 Index</div>
                <div style="font-size: 1.4rem; font-weight: 700; color: #f87171; margin-top: 6px;">Unavailable</div>
            </div>
            """, unsafe_allow_html=True)
            
    with m2:
        st.markdown(f"""
        <div class="exec-card">
            <div style="font-size: 0.75rem; color: #94a3b8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">🚀 Market Gainers</div>
            <div style="font-size: 1.85rem; font-weight: 800; color: #34d399; margin-top: 6px; letter-spacing: -0.02em;">{gainers_count} <span style="font-size: 1rem; color: #94a3b8; font-weight: 500;">Stocks</span></div>
            <div style="font-size: 0.85rem; font-weight: 700; color: #34d399; margin-top: 4px;">Positive Breadth Flow</div>
        </div>
        """, unsafe_allow_html=True)
        
    with m3:
        st.markdown(f"""
        <div class="exec-card">
            <div style="font-size: 0.75rem; color: #94a3b8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">🔻 Market Losers</div>
            <div style="font-size: 1.85rem; font-weight: 800; color: #f87171; margin-top: 6px; letter-spacing: -0.02em;">{losers_count} <span style="font-size: 1rem; color: #94a3b8; font-weight: 500;">Stocks</span></div>
            <div style="font-size: 0.85rem; font-weight: 700; color: #f87171; margin-top: 4px;">Negative Pressure</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- TWO-COLUMN LAYOUT: DONUT CHART & PLACEHOLDER ---
    col_chart, col_placeholder = st.columns([1, 1], gap="medium")

    with col_chart:
        st.markdown("<div class='section-container'>", unsafe_allow_html=True)
        st.markdown("<h3 style='font-size: 1.1rem; font-weight: 700; color: #f1f5f9; margin-bottom: 4px;'>🎯 Index Points Contribution</h3>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 0.8rem; color: #94a3b8; margin-bottom: 12px;'>Constituent impact breakdown on Nifty 50 movement</p>", unsafe_allow_html=True)

        # Prepare Data for Donut Chart
        df_sorted = df_result.sort_values(by="Contribution", key=abs, ascending=False)
        top_n = 8
        top_stocks = df_sorted.head(top_n).copy()
        others_contrib = df_sorted.iloc[top_n:]["Contribution"].sum()

        chart_labels = list(top_stocks["Symbol"]) + ["OTHERS"]
        chart_values = list(top_stocks["Contribution"].abs()) + [abs(others_contrib)]
        
        # Colors: Green for positive contribution, Red for negative contribution
        chart_colors = [
            "#34d399" if c >= 0 else "#f87171" 
            for c in list(top_stocks["Contribution"]) + [others_contrib]
        ]
        
        # Custom hover/text labels
        custom_text = [
            f"{row['Symbol']}: {row['Contribution']:+.2f}" for _, row in top_stocks.iterrows()
        ] + [f"OTHERS: {others_contrib:+.2f}"]

        fig = go.Figure(data=[go.Pie(
            labels=chart_labels,
            values=chart_values,
            hole=0.62,
            marker=dict(colors=chart_colors, line=dict(color='#0b0e16', width=2)),
            textinfo='label+percent',
            textfont=dict(color='#f1f5f9', family='Outfit', size=11),
            hoverinfo='text',
            hovertext=custom_text
        )])

        sign_char = "+" if nifty_net >= 0 else ""
        center_color = "#34d399" if nifty_net >= 0 else "#f87171"

        fig.update_layout(
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=10, b=10, l=10, r=10),
            height=320,
            annotations=[dict(
                text=f"<b>NIFTY 50</b><br><span style='color:{center_color}; font-size:14px;'>{sign_char}{nifty_net:.2f} pts</span>",
                x=0.5, y=0.5,
                font=dict(size=13, color='#ffffff', family='Outfit'),
                showarrow=False
            )]
        )

        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)

    with col_placeholder:
        st.markdown("<div class='section-container' style='display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; min-height: 380px;'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size: 2.5rem; margin-bottom: 12px;'>🔮</div>", unsafe_allow_html=True)
        st.markdown("<h3 style='font-size: 1.2rem; font-weight: 700; color: #f1f5f9; margin-bottom: 6px;'>Reserved Analytics Module</h3>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 0.85rem; color: #94a3b8; max-width: 280px;'>This panel is locked and ready. Tell me what widget, chart, or metrics table you want placed here next!</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- DATAFRAME VIEW ---
    st.markdown("<h3 style='font-size: 1.2rem; font-weight: 700; color: #f1f5f9; margin-bottom: 12px;'>📋 Constituents Live Telemetry</h3>", unsafe_allow_html=True)
    
    def style_change(val):
        color = "#34d399" if val > 0 else "#f87171" if val < 0 else "#94a3b8"
        bg_color = "rgba(52, 211, 153, 0.08)" if val > 0 else "rgba(248, 113, 113, 0.08)" if val < 0 else "rgba(148, 163, 184, 0.08)"
        return f"color: {color}; font-weight: 700; background-color: {bg_color}; border-radius: 4px; padding: 2px 6px;"

    display_df = df_result[["Symbol", "Instrument Key", "Weight (%)", "LTP (₹)", "Prev Close (₹)", "Change (%)", "Contribution"]]
    styled_df = display_df.style.format({
        "Weight (%)": "{:.2f}%",
        "LTP (₹)": "₹{:,.2f}",
        "Prev Close (₹)": "₹{:,.2f}",
        "Change (%)": "{:+.2f}%",
        "Contribution": "{:+.2f}"
    }).map(style_change, subset=["Change (%)"])

    st.dataframe(styled_df, use_container_width=True, height=380)
    
    # India Standard Time (IST) Timestamp
    ist_zone = pytz.timezone('Asia/Kolkata')
    ist_time = datetime.now(ist_zone).strftime('%d-%m-%Y | %I:%M:%S %p IST')
    
    st.markdown(f"""
        <div class="terminal-footer">
            ⚡ Synchronized live at {ist_time} &nbsp;&bull;&nbsp; Auto-refreshes silently every 10 seconds
        </div>
    """, unsafe_allow_html=True)

# Execute the live fragment loop
render_live_market_data()
