import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="NIFTY 50 Index Point Contributors & Breadth",
    page_icon="📈",
    layout="wide"
)

# Dark Theme Custom Styling
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stMetric { background-color: #161b22; padding: 10px; border-radius: 8px; border: 1px solid #30363d; }
    </style>
""", unsafe_allow_html=True)

# --- UPSTOX API CONFIGURATION (NEW TOKEN) ---
UPSTOX_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiJIWjYwMzgiLCJqdGkiOiI2YTlhNTdlYmRmZmFlZTE4YjlhZWEwODEiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaXNFeHRlbmRlZCI6dHJ1ZSwiaWF0IjoxNzg4NDk5OTQ3LCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE4MjAwOTUyMDB9.u8MU3qcj4cMAr4xdjM5ogr7Z_pxdkc2h3VU3aQc2jHM"

# --- NIFTY 50 CONSTITUENTS & WEIGHTS ---
RAW_DATA = [
    ("HDFCBANK", 9.89), ("ICICIBANK", 9.35), ("RELIANCE", 8.02), ("BHARTIARTL", 5.30),
    ("LT", 4.23), ("SBIN", 3.88), ("INFY", 3.68), ("AXISBANK", 3.28),
    ("KOTAKBANK", 2.84), ("M&M", 2.64), ("BAJFINANCE", 2.56), ("ITC", 2.33),
    ("TCS", 2.19), ("LTIM", 2.15), ("TITAN", 1.89), ("SUNPHARMA", 1.85),
    ("HINDUNILVR", 1.61), ("MARUTI", 1.53), ("NTPC", 1.41), ("TATASTEEL", 1.38),
    ("SHRIRAMFIN", 1.35), ("BEL", 1.34), ("HINDALCO", 1.33), ("HCLTECH", 1.29),
    ("ULTRACEMCO", 1.22), ("BAJAJ-AUTO", 1.22), ("GRASIM", 1.13), ("JSWSTEEL", 1.12),
    ("ADANIPORTS", 1.10), ("POWERGRID", 1.09), ("ASIANPAINT", 1.06), ("INDIGO", 1.04),
    ("BAJAJFINSV", 1.04), ("EICHERMOT", 1.00), ("TECHM", 0.94), ("NESTLEIND", 0.94),
    ("COALINDIA", 0.87), ("TRENT", 0.86), ("ONGC", 0.83), ("APOLLOHOSP", 0.82),
    ("ADANIENT", 0.78), ("CIPLA", 0.73), ("SBILIFE", 0.71), ("JIOFIN", 0.70),
    ("MAXHEALTH", 0.68), ("DRREDDY", 0.65), ("TATACONSUM", 0.61), ("TATAMOTORS", 0.59),
    ("HDFCLIFE", 0.53), ("WIPRO", 0.45)
]

@st.cache_data(ttl=300)
def load_instrument_keys():
    mapping = {}
    for sym, weight in RAW_DATA:
        mapping[sym] = {"key": f"NSE_EQ|{sym}", "weight": weight}
    return mapping

STOCK_META = load_instrument_keys()

def fetch_upstox_market_data(keys):
    headers = {'Accept': 'application/json', 'Authorization': f'Bearer {UPSTOX_TOKEN}'}
    combined = {}
    for i in range(0, len(keys), 25):
        chunk = keys[i:i+25]
        url = f"https://api.upstox.com/v2/market-quote/quotes?instrument_key={','.join(chunk)}"
        try:
            res = requests.get(url, headers=headers)
            if res.status_code == 200:
                data = res.json().get('data', {})
                if data:
                    combined.update(data)
        except Exception:
            pass
    return combined

# --- LIVE DASHBOARD FRAGMENT ---
@st.fragment(run_every=15)
def render_live_dashboard():
    keys_list = [meta["key"] for meta in STOCK_META.values()]
    index_keys = ["NSE_INDEX|Nifty 50", "NSE_INDEX:Nifty 50"]
    keys_list.extend(index_keys)

    api_data = fetch_upstox_market_data(keys_list)

    processed_stocks = []
    gainers_count = 0
    losers_count = 0

    # Process live stock data from Upstox API
    for sym, meta in STOCK_META.items():
        item_key = meta["key"]
        weight = meta["weight"]
        pts_impact = 0.0
        pct_change = 0.0
        
        if api_data and item_key in api_data:
            quote = api_data[item_key]
            ltp = quote.get('last_price', 0)
            ohlc = quote.get('ohlc', {})
            close = ohlc.get('close', 0)
            if not close:
                net_change = quote.get('net_change', 0)
                close = ltp - net_change if ltp and net_change else 0
            if close and ltp:
                pct_change = round(((ltp - close) / close) * 100, 2)
                pts_impact = round((weight * pct_change) / 10, 2)
        
        if pts_impact >= 0:
            gainers_count += 1
        else:
            losers_count += 1
            
        processed_stocks.append({"symbol": sym, "impact": pts_impact, "pct": pct_change})

    total_stocks = gainers_count + losers_count if (gainers_count + losers_count) > 0 else 50
    gainer_pct_width = int((gainers_count / total_stocks) * 100)
    loser_pct_width = 100 - gainer_pct_width

    # --- LIVE NIFTY 50 INDEX DATA COLLECTION ---
    index_quote = None
    for ik in index_keys:
        if api_data and ik in api_data:
            index_quote = api_data[ik]
            break

    if index_quote:
        nifty_ltp = index_quote.get('last_price', 0)
        ohlc = index_quote.get('ohlc', {})
        close = ohlc.get('close', 0) or index_quote.get('prev_close_price', nifty_ltp)
        if not nifty_ltp:
            net_chg = index_quote.get('net_change', 0)
            nifty_ltp = close + net_chg
        nifty_net_change = round(nifty_ltp - close, 2)
        nifty_pct_change = round((nifty_net_change / close) * 100, 2) if close else 0.0
    else:
        # Fallback calculation summing stock impacts if index quote is missing
        base_close = 22780.75
        nifty_net_change = round(sum(s['impact'] for s in processed_stocks), 2)
        nifty_ltp = round(base_close + nifty_net_change, 2)
        nifty_pct_change = round((nifty_net_change / base_close) * 100, 2)

    # --- HEADER SECTION ---
    col_top1, col_top2 = st.columns([3, 2])
    with col_top1:
        st.markdown("### NIFTY 50 Index Dashboard")
        color_style = "#2ea043" if nifty_net_change >= 0 else "#f85149"
        arrow = "▲" if nifty_net_change >= 0 else "▼"
        direction_text = "UP" if nifty_net_change >= 0 else "DOWN"
        st.markdown(f"#### {nifty_ltp:,.2f} <span style='color:{color_style}; font-size:15px;'>{arrow} {direction_text} {abs(nifty_net_change):.2f} PTS ({nifty_pct_change:+.2f}%)</span>", unsafe_allow_html=True)

    with col_top2:
        st.markdown("**Gainers / Losers**")
        st.markdown(f"""
            <div style="background-color: #30363d; border-radius: 6px; height: 12px; width: 100%; display: flex; margin-top: 8px;">
                <div style="background-color: #2ea043; width: {gainer_pct_width}%; border-top-left-radius: 6px; border-bottom-left-radius: 6px;"></div>
                <div style="background-color: #f85149; width: {loser_pct_width}%; border-top-right-radius: 6px; border-bottom-right-radius: 6px;"></div>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 13px; margin-top: 6px;">
                <span style="color: #2ea043; font-weight: bold;">● Gainer : {gainers_count}</span>
                <span style="color: #f85149; font-weight: bold;">Losers : {losers_count} ●</span>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # --- MAIN LAYOUT: TWO COLUMNS ---
    left_col, right_col = st.columns(2)

    with left_col:
        st.markdown("#### 🍩 Index Point Contributors (All 50 Movers)")
        st.caption("Ring chart containing all Nifty 50 constituents sized by point impact")
        
        df_movers = pd.DataFrame(processed_stocks)
        df_movers['abs_impact'] = df_movers['impact'].abs()
        df_movers = df_movers.sort_values(by='abs_impact', ascending=False)
        
        fig = go.Figure(data=[go.Pie(
            labels=df_movers['symbol'],
            values=df_movers['abs_impact'],
            hole=0.55,
            marker=dict(colors=['#2ea043' if x > 0 else '#f85149' for x in df_movers['impact']]),
            textinfo='label',
            hoverinfo='label+value+percent'
        )])

        center_color = "#2ea043" if nifty_net_change >= 0 else "#f85149"
        fig.update_layout(
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            margin=dict(t=10, b=10, l=10, r=10),
            annotations=[dict(
                text=f'<b>NIFTY 50</b><br><span style="color:{center_color}; font-size:14px;">{nifty_net_change:+.2f} pts</span><br><span style="color:{center_color}; font-size:12px;">({nifty_pct_change:+.2f}%)</span>',
                x=0.5, y=0.5, font_size=13, showarrow=False, font_color='white'
            )]
        )

        st.plotly_chart(fig, use_container_width=True, key="donut_chart_pts_v7")

    with right_col:
        st.markdown("#### 📊 Comparative Movers List (Complete 50)")
        st.caption("All 50 stocks split between positive index contributors and negative detractors")

        gainers = sorted([s for s in processed_stocks if s['impact'] > 0], key=lambda x: x['impact'], reverse=True)
        losers = sorted([s for s in processed_stocks if s['impact'] <= 0], key=lambda x: x['impact'])
        
        max_rows = max(len(gainers), len(losers)) if (len(gainers) > 0 or len(losers) > 0) else 1
        
        container = st.container(height=520)
        with container:
            for i in range(max_rows):
                col_g, col_bar_g, col_bar_l, col_l = st.columns([2.5, 3, 3, 2.5])
                
                with col_g:
                    if i < len(gainers):
                        g = gainers[i]
                        st.markdown(f"<span style='color: #2ea043; font-weight: 600; font-size: 12px;'>{g['symbol']} +{g['impact']:.2f}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown("")
                        
                with col_bar_g:
                    if i < len(gainers):
                        g = gainers[i]
                        w_val = min(abs(g['impact']) * 12, 100)
                        st.markdown(f"""
                            <div style="display: flex; justify-content: flex-end; align-items: center; height: 18px;">
                                <div style="background-color: #2ea043; width: {w_val}%; height: 5px; border-radius: 3px;"></div>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("")

                with col_bar_l:
                    if i < len(losers):
                        l = losers[i]
                        w_val = min(abs(l['impact']) * 4, 100)
                        st.markdown(f"""
                            <div style="display: flex; justify-content: flex-start; align-items: center; height: 18px;">
                                <div style="background-color: #f85149; width: {w_val}%; height: 5px; border-radius: 3px;"></div>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("")

                with col_l:
                    if i < len(losers):
                        l = losers[i]
                        st.markdown(f"<span style='color: #f85149; font-weight: 600; font-size: 12px;'>{l['impact']:.2f} {l['symbol']}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown("")

    st.caption(f"⚡ Live Upstox API sync active (Last updated: {pd.Timestamp.now().strftime('%H:%M:%S')})")

render_live_dashboard()
