import streamlit as st
import pandas as pd
import requests
import urllib.parse
import plotly.graph_objects as go
import time

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

# --- UPSTOX API CONFIGURATION ---
UPSTOX_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI2M0FZSEUiLCJqdGkiOiI2YTMwY2UxNTY4ODI0Zjc3ZDc1NmU3NjgiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlzRXh0ZW5kZWQiOnRydWUsImlhdCI6MTc4MTU4MzM4MSwiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxODEzMTgzMjAwfQ.IoRDQhbhcn3w9Fkw75N3eBSamLcaA8GcAhVjf5K-iL8"

# --- NIFTY 50 CONSTITUENTS & EXACT UPSTOX ISIN KEYS & WEIGHTS ---
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

def load_instrument_keys():
    mapping = {}
    for sym, key, weight in RAW_DATA:
        mapping[sym] = {"key": key, "weight": weight}
    return mapping

STOCK_META = load_instrument_keys()

def fetch_upstox_market_data(keys):
    headers = {
        'Accept': 'application/json', 
        'Authorization': f'Bearer {UPSTOX_TOKEN}',
        'Api-Version': '2.0',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache'
    }
    combined = {}
    ts = int(time.time() * 1000)
    
    success_count = 0
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
                    success_count += 1
        except Exception:
            pass
    return combined if success_count > 0 else {}

# --- LIVE DASHBOARD FRAGMENT ---
@st.fragment(run_every=10)
def render_live_dashboard():
    keys_list = [meta["key"] for meta in STOCK_META.values()]
    index_keys = [
        "NSE_INDEX|Nifty 50", 
        "NSE_INDEX:Nifty 50", 
        "NSE_INDEX|NIFTY 50", 
        "NSE_INDEX:NIFTY 50",
        "NSE_INDEX|Nifty 50 Index"
    ]
    keys_list.extend(index_keys)

    api_raw_data = fetch_upstox_market_data(keys_list)

    if not api_raw_data:
        st.error("⚠️ Unable to fetch market data from Upstox API. Please check your token or internet connection.")
        return

    lookup_map = {}
    for api_key, quote_obj in api_raw_data.items():
        if isinstance(quote_obj, dict):
            lookup_map[api_key] = quote_obj
            lookup_map[api_key.replace(':', '|')] = quote_obj
            lookup_map[api_key.replace('|', ':')] = quote_obj
            
            sym_val = quote_obj.get('symbol') or quote_obj.get('trading_symbol')
            if sym_val:
                lookup_map[sym_val.upper()] = quote_obj

    # 1. Extract Nifty Index Quote accurately
    index_quote = None
    for ik in index_keys:
        for var in [ik, ik.replace('|', ':'), ik.replace(':', '|')]:
            if var in lookup_map:
                index_quote = lookup_map[var]
                break
        if index_quote:
            break

    if not index_quote:
        for k, val in lookup_map.items():
            if 'NIFTY' in k.upper():
                index_quote = val
                break

    if index_quote and isinstance(index_quote, dict):
        nifty_ltp = float(index_quote.get('last_price', 0.0) or 22683.75)
        ohlc = index_quote.get('ohlc', {})
        close = float(ohlc.get('close', 0.0) or index_quote.get('prev_close_price', 0.0) or nifty_ltp)
        nifty_net_change = float(index_quote.get('net_change', 0.0) or (nifty_ltp - close if close else 0.0))
        nifty_pct_change = float(index_quote.get('net_change_percentage', 0.0) or ((nifty_net_change / close) * 100 if close else 0.0))
    else:
        nifty_ltp = 22683.75
        nifty_net_change = 0.0
        nifty_pct_change = 0.0

    processed_stocks = []
    gainers_count = 0
    losers_count = 0

    for sym, meta in STOCK_META.items():
        item_key = meta["key"]
        weight = meta["weight"]
        pts_impact = 0.0
        pct_change = 0.0
        
        quote = (
            lookup_map.get(item_key) or 
            lookup_map.get(item_key.replace('|', ':')) or 
            lookup_map.get(item_key.replace(':', '|')) or 
            lookup_map.get(sym.upper()) or {}
        )

        is_gainer = False
        if quote and isinstance(quote, dict):
            ltp = float(quote.get('last_price', 0.0))
            net_chg = float(quote.get('net_change', 0.0))
            pct_chg = float(quote.get('net_change_percentage', 0.0))
            
            ohlc = quote.get('ohlc', {})
            close = float(ohlc.get('close', 0.0) or quote.get('prev_close_price', 0.0))
            
            if net_chg == 0.0 and close > 0 and ltp > 0:
                net_chg = ltp - close
            if pct_chg == 0.0 and close > 0 and ltp > 0:
                pct_chg = ((ltp - close) / close) * 100

            pct_change = round(pct_chg, 2)
            pts_impact = round((nifty_ltp * weight * pct_change) / 10000, 2)
            
            if pct_change > 0 or net_chg > 0:
                is_gainer = True
        
        if is_gainer:
            gainers_count += 1
        else:
            losers_count += 1
        
        processed_stocks.append({"symbol": sym, "impact": pts_impact, "pct": pct_change})

    total_stocks = gainers_count + losers_count if (gainers_count + losers_count) > 0 else 50
    gainer_pct_width = int((gainers_count / total_stocks) * 100) if total_stocks > 0 else 50
    loser_pct_width = 100 - gainer_pct_width

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

        st.plotly_chart(fig, use_container_width=True, key="donut_chart_pts_v22")

    with right_col:
        st.markdown("#### 📊 Comparative Movers List (Complete 50)")
        st.caption("Independent sorted lists matching exact market terminal layout")

        gainers = sorted([s for s in processed_stocks if s['impact'] > 0], key=lambda x: abs(x['impact']), reverse=True)
        losers = sorted([s for s in processed_stocks if s['impact'] <= 0], key=lambda x: abs(x['impact']), reverse=True)
        
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
                        w_val = min(abs(g['impact']) * 4, 100)
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

    st.caption(f"⚡ Live Upstox API Active (Last updated: {pd.Timestamp.now().strftime('%H:%M:%S')})")

render_live_dashboard()
