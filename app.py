import os
import streamlit as st
import pandas as pd
import requests
import urllib.parse
import plotly.graph_objects as go
import time


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="NIFTY 50 Index Point Contributors & Breadth",
    page_icon="📈",
    layout="wide"
)


# ============================================================
# DARK THEME CUSTOM STYLING
# ============================================================

st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
        color: #ffffff;
    }

    .stMetric {
        background-color: #161b22;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #30363d;
    }
    </style>
""", unsafe_allow_html=True)


# ============================================================
# UPSTOX API CONFIGURATION
# ============================================================
#
# IMPORTANT:
# Do NOT hard-code your access token here.
#
# For Streamlit Cloud:
#
# [UPSTOX_TOKEN]
# token = "YOUR_NEW_TOKEN"
#
# Or use environment variable:
#
# UPSTOX_TOKEN=YOUR_NEW_TOKEN
#
# ============================================================

try:
    UPSTOX_TOKEN = st.secrets["UPSTOX_TOKEN"]
except Exception:
    UPSTOX_TOKEN = os.getenv("UPSTOX_TOKEN", "")


# ============================================================
# NIFTY 50 CONSTITUENTS
# EXACT STOCK LIST + WEIGHTS FROM ORIGINAL CODE
# ============================================================

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


# ============================================================
# LOAD STOCK METADATA
# ============================================================

def load_instrument_keys():

    mapping = {}

    for sym, key, weight in RAW_DATA:

        mapping[sym] = {
            "key": key,
            "weight": weight
        }

    return mapping


STOCK_META = load_instrument_keys()


# ============================================================
# UPSTOX V3 FULL MARKET QUOTE
# ============================================================
#
# V3 advantages:
#
# 1. Up to 500 instruments in one request
# 2. last_price = current LTP
# 3. prev_close_price = previous trading session close
# 4. net_change = absolute change from previous close
#
# Therefore:
#
#     CHANGE = LTP - PREVIOUS CLOSE
#     %CHANGE = CHANGE / PREVIOUS CLOSE * 100
#
# ============================================================

def fetch_upstox_market_data(keys):

    if not UPSTOX_TOKEN:

        return {}, "UPSTOX_TOKEN is missing."


    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {UPSTOX_TOKEN}"
    }


    # --------------------------------------------------------
    # Remove duplicate keys while preserving order
    # --------------------------------------------------------

    unique_keys = list(dict.fromkeys(keys))


    encoded_keys = urllib.parse.quote(",".join(unique_keys), safe="")


    url = (
        "https://api.upstox.com/v3/market-quote/quotes"
        f"?instrument_key={encoded_keys}"
    )


    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=10
        )


        if response.status_code != 200:

            try:
                error_json = response.json()
            except Exception:
                error_json = response.text

            return {}, (
                f"Upstox HTTP {response.status_code}: "
                f"{error_json}"
            )


        response_json = response.json()


        if response_json.get("status") != "success":

            return {}, (
                f"Upstox returned non-success response: "
                f"{response_json}"
            )


        data = response_json.get("data", {})


        if not isinstance(data, dict):

            return {}, "Invalid Upstox data format."


        return data, None


    except requests.exceptions.Timeout:

        return {}, "Upstox request timed out."


    except requests.exceptions.RequestException as e:

        return {}, f"Upstox request error: {e}"


    except Exception as e:

        return {}, f"Unexpected market-data error: {e}"


# ============================================================
# BUILD ROBUST LOOKUP MAP
# ============================================================

def build_lookup_map(api_raw_data):

    lookup_map = {}


    for api_key, quote_obj in api_raw_data.items():

        if not isinstance(quote_obj, dict):
            continue


        # ----------------------------------------------------
        # Original API key
        # ----------------------------------------------------

        lookup_map[api_key] = quote_obj


        # ----------------------------------------------------
        # Pipe / colon variations
        # ----------------------------------------------------

        lookup_map[
            api_key.replace(":", "|")
        ] = quote_obj


        lookup_map[
            api_key.replace("|", ":")
        ] = quote_obj


        # ----------------------------------------------------
        # Instrument token
        # ----------------------------------------------------

        instrument_token = quote_obj.get(
            "instrument_token"
        )

        if instrument_token:

            lookup_map[
                instrument_token
            ] = quote_obj


            lookup_map[
                instrument_token.replace(":", "|")
            ] = quote_obj


            lookup_map[
                instrument_token.replace("|", ":")
            ] = quote_obj


        # ----------------------------------------------------
        # Trading symbol
        # ----------------------------------------------------

        symbol = (
            quote_obj.get("symbol")
            or quote_obj.get("trading_symbol")
        )


        if symbol:

            lookup_map[
                str(symbol).upper()
            ] = quote_obj


    return lookup_map


# ============================================================
# FIND QUOTE FOR A PARTICULAR STOCK
# ============================================================

def get_stock_quote(
    lookup_map,
    symbol,
    instrument_key
):

    candidates = [

        instrument_key,

        instrument_key.replace("|", ":"),

        instrument_key.replace(":", "|"),

        symbol.upper(),

    ]


    for key in candidates:

        quote = lookup_map.get(key)

        if isinstance(quote, dict):

            return quote


    return None


# ============================================================
# EXTRACT ACCURATE STOCK MARKET DATA
# ============================================================

def extract_stock_data(
    quote,
    symbol,
    weight,
    nifty_ltp
):

    if not isinstance(quote, dict):

        return None


    # --------------------------------------------------------
    # CURRENT LTP
    # --------------------------------------------------------

    try:

        ltp = float(
            quote.get("last_price", 0) or 0
        )

    except Exception:

        ltp = 0.0


    # --------------------------------------------------------
    # PREVIOUS SESSION CLOSE
    #
    # V3 provides this explicitly.
    # --------------------------------------------------------

    try:

        prev_close = float(
            quote.get("prev_close_price", 0) or 0
        )

    except Exception:

        prev_close = 0.0


    # --------------------------------------------------------
    # SECONDARY FALLBACK
    #
    # Only use OHLC close if V3 prev_close_price is
    # unavailable.
    # --------------------------------------------------------

    if prev_close <= 0:

        ohlc = quote.get("ohlc", {})

        if isinstance(ohlc, dict):

            try:

                prev_close = float(
                    ohlc.get("close", 0) or 0
                )

            except Exception:

                prev_close = 0.0


    # --------------------------------------------------------
    # Validate prices
    # --------------------------------------------------------

    if ltp <= 0 or prev_close <= 0:

        return None


    # ========================================================
    # SINGLE SOURCE OF TRUTH
    #
    # GAINER:
    #       LTP > Previous Close
    #
    # LOSER:
    #       LTP < Previous Close
    #
    # UNCHANGED:
    #       LTP == Previous Close
    # ========================================================

    net_change = ltp - prev_close


    pct_change = (
        (net_change / prev_close) * 100
    )


    # --------------------------------------------------------
    # Gainer / Loser
    # --------------------------------------------------------

    if net_change > 0:

        direction = "GAINER"

    elif net_change < 0:

        direction = "LOSER"

    else:

        direction = "UNCHANGED"


    # --------------------------------------------------------
    # NIFTY POINT IMPACT
    #
    # Existing calculation preserved:
    #
    # NIFTY LTP × WEIGHT × %CHANGE / 10000
    # --------------------------------------------------------

    pts_impact = (
        nifty_ltp
        * weight
        * pct_change
        / 10000
    )


    return {

        "symbol": symbol,

        "ltp": ltp,

        "prev_close": prev_close,

        "net_change": net_change,

        "pct": pct_change,

        "weight": weight,

        "impact": pts_impact,

        "direction": direction

    }


# ============================================================
# NIFTY INDEX DATA
# ============================================================

def extract_nifty_data(
    lookup_map,
    index_key
):

    index_quote = None


    # --------------------------------------------------------
    # Direct lookup
    # --------------------------------------------------------

    index_quote = lookup_map.get(index_key)


    # --------------------------------------------------------
    # Colon version
    # --------------------------------------------------------

    if not index_quote:

        index_quote = lookup_map.get(
            index_key.replace("|", ":")
        )


    # --------------------------------------------------------
    # Reverse version
    # --------------------------------------------------------

    if not index_quote:

        index_quote = lookup_map.get(
            index_key.replace(":", "|")
        )


    # --------------------------------------------------------
    # Search by NIFTY
    # --------------------------------------------------------

    if not index_quote:

        for key, value in lookup_map.items():

            if "NIFTY" in str(key).upper():

                if isinstance(value, dict):

                    index_quote = value

                    break


    if not index_quote:

        return None


    # --------------------------------------------------------
    # NIFTY LTP
    # --------------------------------------------------------

    try:

        nifty_ltp = float(
            index_quote.get(
                "last_price",
                0
            ) or 0
        )

    except Exception:

        nifty_ltp = 0.0


    # --------------------------------------------------------
    # Previous close
    # --------------------------------------------------------

    try:

        nifty_prev_close = float(
            index_quote.get(
                "prev_close_price",
                0
            ) or 0
        )

    except Exception:

        nifty_prev_close = 0.0


    # --------------------------------------------------------
    # Fallback to OHLC close
    # --------------------------------------------------------

    if nifty_prev_close <= 0:

        ohlc = index_quote.get(
            "ohlc",
            {}
        )

        if isinstance(ohlc, dict):

            try:

                nifty_prev_close = float(
                    ohlc.get(
                        "close",
                        0
                    ) or 0
                )

            except Exception:

                nifty_prev_close = 0.0


    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    if nifty_ltp <= 0:

        return None


    # --------------------------------------------------------
    # Calculate from actual LTP and previous close
    # --------------------------------------------------------

    if nifty_prev_close > 0:

        nifty_net_change = (
            nifty_ltp
            - nifty_prev_close
        )

        nifty_pct_change = (
            nifty_net_change
            / nifty_prev_close
            * 100
        )

    else:

        nifty_net_change = float(
            index_quote.get(
                "net_change",
                0
            ) or 0
        )

        nifty_pct_change = (
            nifty_net_change
            / nifty_ltp
            * 100
            if nifty_ltp > 0
            else 0
        )


    return {

        "quote": index_quote,

        "ltp": nifty_ltp,

        "prev_close": nifty_prev_close,

        "net_change": nifty_net_change,

        "pct_change": nifty_pct_change

    }


# ============================================================
# LIVE DASHBOARD
# ============================================================

@st.fragment(run_every=10)
def render_live_dashboard():


    # ========================================================
    # TOKEN CHECK
    # ========================================================

    if not UPSTOX_TOKEN:

        st.error(
            "❌ UPSTOX_TOKEN is not configured."
        )

        st.info(
            "Add UPSTOX_TOKEN to Streamlit Secrets "
            "or the environment variables."
        )

        return


    # ========================================================
    # BUILD COMPLETE REQUEST
    #
    # 50 stocks + NIFTY 50
    # ========================================================

    stock_keys = [
        meta["key"]
        for meta in STOCK_META.values()
    ]


    index_key = "NSE_INDEX|Nifty 50"


    all_keys = stock_keys + [index_key]


    # ========================================================
    # FETCH MARKET DATA
    # ========================================================

    api_raw_data, api_error = (
        fetch_upstox_market_data(
            all_keys
        )
    )


    # ========================================================
    # API ERROR
    # ========================================================

    if api_error:

        st.error(
            f"❌ Market data unavailable: {api_error}"
        )

        st.caption(
            "No simulated Gainer/Loser values are being "
            "used. The dashboard waits for real Upstox data."
        )

        return


    if not api_raw_data:

        st.error(
            "❌ Upstox returned no market data."
        )

        return


    # ========================================================
    # LOOKUP MAP
    # ========================================================

    lookup_map = build_lookup_map(
        api_raw_data
    )


    # ========================================================
    # NIFTY DATA
    # ========================================================

    nifty_data = extract_nifty_data(
        lookup_map,
        index_key
    )


    if not nifty_data:

        st.error(
            "❌ NIFTY 50 quote could not be found "
            "in the Upstox response."
        )

        return


    nifty_ltp = nifty_data["ltp"]

    nifty_prev_close = nifty_data["prev_close"]

    nifty_net_change = (
        nifty_data["net_change"]
    )

    nifty_pct_change = (
        nifty_data["pct_change"]
    )


    # ========================================================
    # PROCESS ALL 50 STOCKS
    # ========================================================

    processed_stocks = []

    missing_symbols = []


    for sym, meta in STOCK_META.items():

        quote = get_stock_quote(
            lookup_map,
            sym,
            meta["key"]
        )


        if not quote:

            missing_symbols.append(sym)

            continue


        stock_data = extract_stock_data(
            quote=quote,
            symbol=sym,
            weight=meta["weight"],
            nifty_ltp=nifty_ltp
        )


        if stock_data is None:

            missing_symbols.append(sym)

            continue


        processed_stocks.append(
            stock_data
        )


    # ========================================================
    # GAINER / LOSER COUNT
    #
    # IMPORTANT:
    #
    # We now use the SAME pct sign everywhere.
    #
    # pct > 0 = Gainer
    # pct < 0 = Loser
    # pct == 0 = Unchanged
    #
    # ========================================================

    gainers = [
        s
        for s in processed_stocks
        if s["pct"] > 0
    ]


    losers = [
        s
        for s in processed_stocks
        if s["pct"] < 0
    ]


    unchanged = [
        s
        for s in processed_stocks
        if s["pct"] == 0
    ]


    gainers_count = len(gainers)

    losers_count = len(losers)

    unchanged_count = len(unchanged)


    # ========================================================
    # TOTAL VALID STOCKS
    # ========================================================

    total_stocks = len(
        processed_stocks
    )


    if total_stocks <= 0:

        st.error(
            "❌ No valid constituent quotes received."
        )

        return


    # ========================================================
    # BREADTH BAR
    #
    # For the visual bar:
    #
    # Gainers + Losers
    #
    # Unchanged stocks do not distort the directional ratio.
    # ========================================================

    directional_total = (
        gainers_count
        + losers_count
    )


    if directional_total > 0:

        gainer_pct_width = (
            gainers_count
            / directional_total
            * 100
        )

        loser_pct_width = (
            losers_count
            / directional_total
            * 100
        )

    else:

        gainer_pct_width = 0

        loser_pct_width = 0


    # ========================================================
    # HEADER SECTION
    # ========================================================

    col_top1, col_top2 = st.columns(
        [3, 2]
    )


    # ========================================================
    # LEFT HEADER
    # ========================================================

    with col_top1:

        st.markdown(
            "### NIFTY 50 Index Dashboard"
        )


        color_style = (
            "#2ea043"
            if nifty_net_change >= 0
            else "#f85149"
        )


        arrow = (
            "▲"
            if nifty_net_change >= 0
            else "▼"
        )


        direction_text = (
            "UP"
            if nifty_net_change >= 0
            else "DOWN"
        )


        st.markdown(
            f"""
            #### {nifty_ltp:,.2f}

            <span style="
                color:{color_style};
                font-size:15px;
            ">
                {arrow}
                {direction_text}
                {abs(nifty_net_change):.2f}
                PTS
                ({nifty_pct_change:+.2f}%)
            </span>
            """,
            unsafe_allow_html=True
        )


    # ========================================================
    # RIGHT HEADER - GAINERS / LOSERS
    # ========================================================

    with col_top2:

        st.markdown(
            "**Gainers / Losers**"
        )


        st.markdown(
            f"""
            <div style="
                background-color:#30363d;
                border-radius:6px;
                height:12px;
                width:100%;
                display:flex;
                margin-top:8px;
            ">

                <div style="
                    background-color:#2ea043;
                    width:{gainer_pct_width:.2f}%;
                    border-top-left-radius:6px;
                    border-bottom-left-radius:6px;
                ">
                </div>

                <div style="
                    background-color:#f85149;
                    width:{loser_pct_width:.2f}%;
                    border-top-right-radius:6px;
                    border-bottom-right-radius:6px;
                ">
                </div>

            </div>


            <div style="
                display:flex;
                justify-content:space-between;
                font-size:13px;
                margin-top:6px;
            ">

                <span style="
                    color:#2ea043;
                    font-weight:bold;
                ">
                    ● Gainer : {gainers_count}
                </span>


                <span style="
                    color:#f85149;
                    font-weight:bold;
                ">
                    Losers : {losers_count} ●
                </span>

            </div>


            <div style="
                text-align:center;
                font-size:11px;
                color:#8b949e;
                margin-top:4px;
            ">
                Unchanged : {unchanged_count}
            </div>
            """,
            unsafe_allow_html=True
        )


    st.markdown("---")


    # ========================================================
    # DATA QUALITY INFORMATION
    # ========================================================

    if missing_symbols:

        st.warning(
            f"⚠️ Live quote missing for "
            f"{len(missing_symbols)} stock(s): "
            f"{', '.join(missing_symbols)}"
        )


    # ========================================================
    # MAIN LAYOUT
    # ========================================================

    left_col, right_col = st.columns(
        2
    )


    # ========================================================
    # LEFT COLUMN
    # DONUT CHART
    # ========================================================

    with left_col:

        st.markdown(
            "#### 🍩 Index Point Contributors "
            "(All 50 Movers)"
        )


        st.caption(
            "Ring chart containing all Nifty 50 "
            "constituents sized by point impact"
        )


        df_movers = pd.DataFrame(
            processed_stocks
        )


        if not df_movers.empty:

            df_movers["abs_impact"] = (
                df_movers["impact"].abs()
            )


            df_movers = df_movers.sort_values(
                by="abs_impact",
                ascending=False
            )


            fig = go.Figure(
                data=[
                    go.Pie(

                        labels=df_movers["symbol"],

                        values=df_movers["abs_impact"],

                        hole=0.55,

                        marker=dict(
                            colors=[
                                "#2ea043"
                                if x > 0
                                else "#f85149"
                                for x
                                in df_movers["impact"]
                            ]
                        ),

                        textinfo="label",

                        hovertemplate=(
                            "<b>%{label}</b>"
                            "<br>Impact: %{value:.2f} pts"
                            "<br>Share: %{percent}"
                            "<extra></extra>"
                        )

                    )
                ]
            )


            center_color = (
                "#2ea043"
                if nifty_net_change >= 0
                else "#f85149"
            )


            fig.update_layout(

                showlegend=False,

                paper_bgcolor="rgba(0,0,0,0)",

                plot_bgcolor="rgba(0,0,0,0)",

                font=dict(
                    color="white"
                ),

                margin=dict(
                    t=10,
                    b=10,
                    l=10,
                    r=10
                ),

                annotations=[
                    dict(

                        text=(
                            f"<b>NIFTY 50</b>"
                            f"<br>"
                            f"<span style="
                            f"'color:{center_color};"
                            f"font-size:14px;'>"
                            f"{nifty_net_change:+.2f}"
                            f" pts"
                            f"</span>"
                            f"<br>"
                            f"<span style="
                            f"'color:{center_color};"
                            f"font-size:12px;'>"
                            f"({nifty_pct_change:+.2f}%)"
                            f"</span>"
                        ),

                        x=0.5,

                        y=0.5,

                        font_size=13,

                        showarrow=False,

                        font_color="white"

                    )
                ]

            )


            st.plotly_chart(
                fig,
                use_container_width=True,
                key="donut_chart_pts_v19"
            )


    # ========================================================
    # RIGHT COLUMN
    # MOVERS LIST
    # ========================================================

    with right_col:

        st.markdown(
            "#### 📊 Comparative Movers List "
            "(Complete 50)"
        )


        st.caption(
            "All available Nifty 50 stocks split "
            "between positive and negative movers"
        )


        # ----------------------------------------------------
        # IMPORTANT:
        #
        # Classification is based directly on pct.
        #
        # This is exactly the same logic used above.
        # ----------------------------------------------------

        gainers_sorted = sorted(
            [
                s
                for s in processed_stocks
                if s["pct"] > 0
            ],
            key=lambda x: x["impact"],
            reverse=True
        )


        losers_sorted = sorted(
            [
                s
                for s in processed_stocks
                if s["pct"] < 0
            ],
            key=lambda x: x["impact"]
        )


        max_rows = max(
            len(gainers_sorted),
            len(losers_sorted),
            1
        )


        container = st.container(
            height=520
        )


        with container:

            for i in range(max_rows):

                col_g, col_bar_g, col_bar_l, col_l = (
                    st.columns(
                        [2.5, 3, 3, 2.5]
                    )
                )


                # =================================================
                # GAINER SYMBOL
                # =================================================

                with col_g:

                    if i < len(gainers_sorted):

                        g = gainers_sorted[i]


                        st.markdown(
                            f"""
                            <span style="
                                color:#2ea043;
                                font-weight:600;
                                font-size:12px;
                            ">
                                {g["symbol"]}
                                +{g["impact"]:.2f}
                            </span>
                            """,
                            unsafe_allow_html=True
                        )

                    else:

                        st.markdown("")


                # =================================================
                # GAINER BAR
                # =================================================

                with col_bar_g:

                    if i < len(gainers_sorted):

                        g = gainers_sorted[i]


                        w_val = min(
                            abs(g["impact"]) * 4,
                            100
                        )


                        st.markdown(
                            f"""
                            <div style="
                                display:flex;
                                justify-content:flex-end;
                                align-items:center;
                                height:18px;
                            ">

                                <div style="
                                    background-color:#2ea043;
                                    width:{w_val}%;
                                    height:5px;
                                    border-radius:3px;
                                ">
                                </div>

                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    else:

                        st.markdown("")


                # =================================================
                # LOSER BAR
                # =================================================

                with col_bar_l:

                    if i < len(losers_sorted):

                        l = losers_sorted[i]


                        w_val = min(
                            abs(l["impact"]) * 4,
                            100
                        )


                        st.markdown(
                            f"""
                            <div style="
                                display:flex;
                                justify-content:flex-start;
                                align-items:center;
                                height:18px;
                            ">

                                <div style="
                                    background-color:#f85149;
                                    width:{w_val}%;
                                    height:5px;
                                    border-radius:3px;
                                ">
                                </div>

                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    else:

                        st.markdown("")


                # =================================================
                # LOSER SYMBOL
                # =================================================

                with col_l:

                    if i < len(losers_sorted):

                        l = losers_sorted[i]


                        st.markdown(
                            f"""
                            <span style="
                                color:#f85149;
                                font-weight:600;
                                font-size:12px;
                            ">
                                {l["impact"]:.2f}
                                {l["symbol"]}
                            </span>
                            """,
                            unsafe_allow_html=True
                        )

                    else:

                        st.markdown("")


    # ========================================================
    # FOOTER / DATA STATUS
    # ========================================================

    current_time = pd.Timestamp.now().strftime(
        "%H:%M:%S"
    )


    st.caption(
        f"⚡ Upstox Full Market Quote V3 Active "
        f"| Live quotes: {len(processed_stocks)}/50 "
        f"| Last updated: {current_time}"
    )


    # ========================================================
    # OPTIONAL DEBUG INFORMATION
    # ========================================================
    #
    # This is intentionally collapsed so the main dashboard
    # remains clean.
    #
    # It is extremely useful if Gainers/Losers ever look
    # incorrect again.
    #
    # ========================================================

    with st.expander(
        "🔍 Live Quote Verification"
    ):

        debug_rows = []


        for stock in processed_stocks:

            debug_rows.append({

                "Symbol": stock["symbol"],

                "LTP": round(
                    stock["ltp"],
                    2
                ),

                "Previous Close": round(
                    stock["prev_close"],
                    2
                ),

                "Change": round(
                    stock["net_change"],
                    2
                ),

                "Change %": round(
                    stock["pct"],
                    2
                ),

                "Direction": stock["direction"],

                "Weight": stock["weight"],

                "NIFTY Impact": round(
                    stock["impact"],
                    2
                )

            })


        if debug_rows:

            debug_df = pd.DataFrame(
                debug_rows
            )


            debug_df = debug_df.sort_values(
                by="Change %",
                ascending=False
            )


            st.dataframe(
                debug_df,
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# RUN DASHBOARD
# ============================================================

render_live_dashboard()
