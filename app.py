import streamlit as st
import pandas as pd
import requests
import urllib.parse
import time

st.set_page_config(page_title="Nifty Index & Constituents LTP Verification", layout="wide")

st.title("🔍 Nifty Index & Constituents LTP Verification")
st.markdown("Enter your fresh Upstox Access Token below to securely fetch live market data for the Nifty 50 Index and all its components.")

# --- INTERACTIVE TOKEN INPUT FIELD ---
user_token = st.text_input("Upstox Access Token", type="password", value="")

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
            else:
                st.error(f"API Error [{res.status_code}]: {res.text}")
        except Exception as e:
            st.error(f"Connection Exception: {e}")
    return combined

if st.button("🔄 Fetch Live Index & Stock LTP"):
    if not user_token.strip():
        st.warning("Please enter your Upstox Access Token above.")
    else:
        # Correct unique index key for Nifty 50
        index_keys = ["NSE_INDEX|Nifty 50"]
        keys_list = index_keys + [item[1] for item in RAW_DATA]
        
        api_response = fetch_market_data(keys_list, user_token.strip())
        
        if not api_response:
            st.error("Failed to retrieve data. Please check your token.")
        else:
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
            
            if nifty_quote:
                n_ltp = nifty_quote.get('last_price', 0.0)
                n_net = nifty_quote.get('net_change', 0.0)
                n_pct = nifty_quote.get('net_change_percentage', 0.0)
                st.metric(label="NIFTY 50 Index (Live)", value=f"{n_ltp:,.2f}", delta=f"{n_net:+.2f} ({n_pct:+.2f}%)")
            else:
                st.warning("Could not locate Nifty 50 Index quote directly via 'NSE_INDEX|Nifty 50'.")

            # 2. Build Stock Rows & calculate cumulative metrics
            rows = []
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
                
                rows.append({
                    "Symbol": sym,
                    "Instrument Key": key,
                    "Weight (%)": weight,
                    "LTP (₹)": ltp,
                    "Prev Close (₹)": close,
                    "Change (%)": pct_change
                })
                
            df_result = pd.DataFrame(rows)
            st.success(f"Successfully fetched live data for Nifty Index and {len(df_result)} constituent stocks!")
            st.dataframe(df_result, use_container_width=True)
