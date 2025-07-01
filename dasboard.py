import streamlit as st

# Configure page
st.set_page_config(
    page_title="FKN Trader Control",
    layout="centered",
    page_icon="📊"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .stSlider .thumb {
        background-color: #FF4B4B !important;
    }
    .st-bb {
        background-color: transparent;
    }
    .st-at {
        background-color: #0e1117;
    }
    .stToggle button {
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# Header Section
st.title("📊 FKN Heights Trading Dashboard")
st.markdown("Control panel for your auto trading bot")

# --- Main Control Panel ---
col1, col2 = st.columns(2)

with col1:
    # --- Start/Stop Toggle ---
    start_trading = st.toggle(
        "🚀 Start Trading",
        value=False,
        help="Activate/deactivate the trading bot"
    )
    
    # --- Risk Slider ---
    risk_percent = st.slider(
        "💥 Risk per Trade (%)", 
        min_value=0.1, 
        max_value=10.0, 
        value=2.0, 
        step=0.1,
        help="Percentage of capital to risk per trade"
    )

with col2:
    # --- Symbol Selector ---
    symbols = st.multiselect(
        "💱 Trading Pairs",
        ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "BTCUSD", "ETHUSD", "US30", "NAS100"],
        default=["EURUSD"],
        help="Select currency pairs to trade"
    )
    
    # --- News Filter Toggle ---
    news_filter = st.checkbox(
        "📰 Enable News Filter", 
        value=True,
        help="Avoid trading during high-impact news events"
    )

# --- Strategy Selection ---
strategy = st.selectbox(
    "🎯 Trading Strategy",
    ["Trend Following", "Mean Reversion", "Breakout", "Scalping"],
    index=0,
    help="Select the trading strategy to use"
)

# --- Output Section ---
st.markdown("---")
st.subheader("🔧 Active Configuration")

# Status indicators
status_cols = st.columns(4)
with status_cols[0]:
    st.metric("Trading Status", "ACTIVE" if start_trading else "STANDBY", delta_color="off")
with status_cols[1]:
    st.metric("Risk per Trade", f"{risk_percent}%")
with status_cols[2]:
    st.metric("Trading Pairs", len(symbols))
with status_cols[3]:
    st.metric("News Filter", "ON" if news_filter else "OFF")

# Detailed settings
with st.expander("📋 Detailed Settings"):
    st.write(f"**Selected Strategy:** {strategy}")
    st.write(f"**Trading Pairs:** {', '.join(symbols)}")
    st.write(f"**Risk Management:** {risk_percent}% per trade, News Filter {'enabled' if news_filter else 'disabled'}")
    
    if start_trading:
        st.success("Bot is currently active and trading according to your settings.")
    else:
        st.warning("Bot is in standby mode. Enable trading to start operations.")

# Footer
st.markdown("---")
st.caption("© 2023 FKN Heights Trading | Version 1.0.0")