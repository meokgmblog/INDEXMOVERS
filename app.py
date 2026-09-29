import streamlit as st
import requests
import urllib.parse
import time

st.set_page_config(page_title="Upstox Raw Response Inspector", layout="wide")

st.title("🔍 Upstox Raw JSON Response Inspector")

UPSTOX_TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI2M0FZSEUiLCJqdGkiOiI2YWJiODQyMTkzOTc2ZDBhZTE1YzE0YzciLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6ZmFsc2UsImlhdCI6MTc5MDY3Mzk1MywiaXNzIjoidWRhcGktZ2F0ZXdheS1zZXJ2aWNlIiwiZXhwIjoxNzkwNzE5MjAwfQ.gqcFP5ZUOTNbKDHmP_o32a3s4YI8QEyqYMShV4xoU9k"

if st.button("Inspect Raw Response for HDFCBANK"):
    test_key = "NSE_EQ|INE040A01034"
    headers = {'Accept': 'application/json', 'Authorization': f'Bearer {UPSTOX_TOKEN}'}
    
    # Try both pipe and colon variations
    keys_to_test = [test_key, test_key.replace('|', ':')]
    
    for k in keys_to_test:
        url = f"https://api.upstox.com/v2/market-quote/quotes?instrument_key={urllib.parse.quote(k)}&_t={int(time.time())}"
        st.write(f"Testing URL: `{url}`")
        try:
            res = requests.get(url, headers=headers, timeout=5)
            st.write(f"Status Code: `{res.status_code}`")
            st.json(res.json())
        except Exception as e:
            st.error(f"Error: {e}")
