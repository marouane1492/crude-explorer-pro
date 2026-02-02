import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import timedelta, date

# 1. PAGE CONFIGURATION
st.set_page_config(
    page_title="The Crude Explorer Pro", 
    layout="wide", 
    page_icon="🛢️",
    initial_sidebar_state="expanded"
)

# 2. THE EVENT DATABASE
EVENTS = [
    {"date": "1980-09-22", "event": "Start of Iran-Iraq War", "type": "Conflict"},
    {"date": "1990-08-02", "event": "Iraq Invades Kuwait", "type": "Conflict"},
    {"date": "1997-07-02", "event": "Asian Financial Crisis", "type": "Economic"},
    {"date": "2001-09-11", "event": "9/11 Terrorist Attacks", "type": "Conflict"},
    {"date": "2003-03-20", "event": "US Invasion of Iraq", "type": "Conflict"},
    {"date": "2008-07-11", "event": "2008 Price Peak", "type": "Economic"},
    {"date": "2011-02-15", "event": "Arab Spring Begins", "type": "Conflict"},
    {"date": "2014-11-27", "event": "OPEC No-Cut Decision", "type": "Policy/OPEC"},
    {"date": "2019-09-14", "event": "Saudi Abqaiq Attack", "type": "Conflict"},
    {"date": "2020-04-20", "event": "WTI Negative Prices", "type": "Economic"},
    {"date": "2022-02-24", "event": "Invasion of Ukraine", "type": "Conflict"},
    {"date": "2023-10-07", "event": "Israel-Hamas War", "type": "Conflict"},
    {"date": "2024-04-13", "event": "Iran-Israel Escalation", "type": "Conflict"},
    {"date": "2025-06-13", "event": "Middle East Crisis 2025", "type": "Conflict"},
    {"date": "2025-12-09", "event": "OPEC+ Extends Cuts to 2026", "type": "Policy/OPEC"},
]

# 3. HELPER FUNCTIONS
@st.cache_data
def load_data(ticker):
    """Fetch data and fix yfinance multi-index issues."""
    df = yf.download(ticker, start="1980-01-01")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

def calculate_market_impact(events_list, price_data):
    """Calculates price change 7 days after a specific date."""
    impact_results = []
    for e in events_list:
        event_date = pd.to_datetime(e['date'])
        
        # Get Event Day Price
        event_day_df = price_data[price_data.index >= event_date].head(1)
        if event_day_df.empty: continue
        
        start_price = event_day_df['Close'].values[0]
        actual_date = event_day_df.index[0]

        # Get Price 7 Days Later
        target_date = actual_date + timedelta(days=7)
        post_event_df = price_data[price_data.index >= target_date].head(1)
        
        if not post_event_df.empty:
            end_price = post_event_df['Close'].values[0]
            pct_change = ((end_price - start_price) / start_price) * 100
            impact_str = f"{pct_change:+.2f}%"
        else:
            impact_str = "N/A"
            pct_change = 0

        impact_results.append({
            "Date": e['date'],
            "Event": e['event'],
            "Type": e['type'],
            "Price (Event)": round(start_price, 2),
            "7-Day Impact": impact_str,
            "RawDelta": pct_change
        })
    return pd.DataFrame(impact_results)

# 4. SIDEBAR UI
st.sidebar.header("📊 Market Controls")
ticker_display = st.sidebar.selectbox("Oil Benchmark", ["WTI Crude", "Brent Crude"])
ticker_map = {"WTI Crude": "CL=F", "Brent Crude": "BZ=F"}

st.sidebar.subheader("Timeframe")
start_input = st.sidebar.date_input("From", date(1990, 1, 1))
end_input = st.sidebar.date_input("To", date.today())

st.sidebar.subheader("Technical Tools")
show_sma50 = st.sidebar.checkbox("50-Day Moving Average")
show_sma200 = st.sidebar.checkbox("200-Day Moving Average")
use_log = st.sidebar.checkbox("Logarithmic Scale")

st.sidebar.subheader("Event Filters")
all_types = list(set(e["type"] for e in EVENTS))
selected_types = st.sidebar.multiselect("Filter by Category", all_types, default=all_types)

# 5. DATA PROCESSING
raw_data = load_data(ticker_map[ticker_display])
# Filter by date and calculate technicals
df = raw_data.loc[str(start_input):str(end_input)].copy()
df['SMA50'] = df['Close'].rolling(window=50).mean()
df['SMA200'] = df['Close'].rolling(window=200).mean()

# Sidebar Statistics
if not df.empty:
    st.sidebar.divider()
    st.sidebar.metric("Period High", f"${df['Close'].max():.2f}")
    st.sidebar.metric("Period Low", f"${df['Close'].min():.2f}")
    st.sidebar.download_button("📩 Export CSV", df.to_csv(), "oil_data.csv", "text/csv")

# 6. MAIN DASHBOARD VISUALS
st.title("🛢️ The Crude Explorer")
st.markdown(f"Currently viewing **{ticker_display}** from {start_input} to {end_input}")

fig = go.Figure()

# Main Price Line
fig.add_trace(go.Scatter(
    x=df.index, y=df['Close'], 
    name='Price', line=dict(color='#00d1b2', width=2),
    hovertemplate="Price: $%{y:.2f}<extra></extra>"
))

# Technical Indicators
if show_sma50:
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], name='50 SMA', line=dict(color='orange', width=1)))
if show_sma200:
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA200'], name='200 SMA', line=dict(color='red', width=1)))

# Event Annotations
filtered_events = [e for e in EVENTS if e["type"] in selected_types]
for e in filtered_events:
    e_date = pd.to_datetime(e['date'])
    if e_date in df.index:
        fig.add_annotation(
            x=e_date, y=df.loc[e_date]['Close'],
            text=e['event'], showarrow=True, arrowhead=1,
            bgcolor="rgba(0,0,0,0.7)", bordercolor="gray"
        )

fig.update_layout(
    template="plotly_dark",
    yaxis_type="log" if use_log else "linear",
    hovermode="x unified",
    height=600,
    margin=dict(l=0, r=0, t=30, b=0)
)

st.plotly_chart(fig, use_container_width=True)

# 7. MARKET IMPACT TABLE
st.header("⚡ Statistical Market Impact")
st.write("Calculates the price movement exactly 7 days after the event baseline.")

impact_df = calculate_market_impact(filtered_events, df)

if not impact_df.empty:
    # Styling for the table
    def style_delta(val):
        if isinstance(val, str) and "%" in val:
            color = 'red' if '-' in val else '#00FF00'
            return f'color: {color}; font-weight: bold'
        return ''

    st.dataframe(
        impact_df.style.applymap(style_delta, subset=['7-Day Impact']),
        use_container_width=True,
        hide_index=True
    )
else:
    st.warning("No events found within the selected date range.")

st.divider()
st.caption("Data: Yahoo Finance | Logic: 7-Day Price Delta Analysis")