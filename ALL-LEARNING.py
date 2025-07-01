import json
import urllib.request
import streamlit as st
import pandas as pd
import datetime

# Streamlit app title and styling
st.set_page_config(page_title="FKN CURRENCY CONVERTER", layout="wide")
st.markdown("""
    <style>
    input {
        color: black !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("💱 FKN CURRENCY CONVERTER")

# --- Currency List (you can expand this if needed) ---
currency_list = [
    "USD", "KES", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "ZAR", "INR", 
    "CNY", "NZD", "SGD", "NGN", "GHS", "TZS", "UGX", "RUB", "BRL", "MXN"
]

# --- UI: Currency dropdowns and amount ---
col1, col2, col3 = st.columns(3)
with col1:
    base_currency = st.selectbox("Base currency:", currency_list, index=0)
with col2:
    target_currency = st.selectbox("Target currency:", currency_list, index=1)
with col3:
    amount = st.number_input("Amount to convert:", value=1.0)

# --- API for live conversion ---
if st.button("Convert"):
    api_url = f"https://v6.exchangerate-api.com/v6/caa4b53d5c599f5dd44a0700/latest/{base_currency}"

    try:
        with urllib.request.urlopen(api_url) as response:
            data = json.loads(response.read())

            if data["result"] == "success":
                rate = data["conversion_rates"].get(target_currency)
                if rate:
                    converted = round(amount * rate, 2)
                    st.success(f"✅ {amount} {base_currency} = {converted} {target_currency}")
                else:
                    st.error(f"❌ Target currency '{target_currency}' not found.")
            else:
                st.error("❌ API Error: " + str(data.get("error-type", "Unknown error")))
    except Exception as e:
        st.error(f"❌ Error: {e}")

# --- Sidebar for Historical Data and Stats ---
with st.sidebar:
    st.header("📉 Historical Insights")

    # Date range: Past 1 year
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=365)
    
    # Corrected historical data API URL
    hist_url = f"http://api.exchangerate.host/timeframe?access_key=957c96b16d2a683a8592b2340d59afd0&source={base_currency}&currencies={target_currency}&start_date={start_date}&end_date={end_date}"
    
    try:
        with urllib.request.urlopen(hist_url) as response:
            hist_data = json.loads(response.read())
            
            if hist_data.get("success"):
                rates = hist_data["quotes"]
                
                # Convert to pandas DataFrame
                df = pd.DataFrame.from_dict(rates, orient='index')
                df.index = pd.to_datetime(df.index)
                column_name = f"{base_currency}{target_currency}"
                df.columns = [target_currency]
                df.sort_index(inplace=True)

                # Highest & lowest
                highest_rate = df[target_currency].max()
                highest_date = df[target_currency].idxmax().date()

                lowest_rate = df[target_currency].min()
                lowest_date = df[target_currency].idxmin().date()

                # Percentage changes
                latest = df[target_currency].iloc[-1]
                day_ago = df[target_currency].iloc[-2] if len(df) > 1 else latest
                week_ago = df[target_currency].iloc[-6] if len(df) > 6 else latest
                month_ago = df[target_currency].iloc[-30] if len(df) > 30 else latest
                year_ago = df[target_currency].iloc[0]

                percent_day = ((latest - day_ago) / day_ago) * 100 if day_ago != 0 else 0
                percent_week = ((latest - week_ago) / week_ago) * 100 if week_ago != 0 else 0
                percent_month = ((latest - month_ago) / month_ago) * 100 if month_ago != 0 else 0
                percent_year = ((latest - year_ago) / year_ago) * 100 if year_ago != 0 else 0

                # Display stats
                st.subheader(f"💹 {base_currency} → {target_currency}")
                st.markdown(f"**Highest:** {highest_rate:.2f} on `{highest_date}`")
                st.markdown(f"**Lowest:** {lowest_rate:.2f} on `{lowest_date}`")

                st.subheader("📊 % Change")
                st.markdown(f"**Today:** {percent_day:.2f}%")
                st.markdown(f"**This Week:** {percent_week:.2f}%")
                st.markdown(f"**This Month:** {percent_month:.2f}%")
                st.markdown(f"**This Year:** {percent_year:.2f}%")

                # Optional: Display chart
                st.subheader("📈 1-Year Chart")
                st.line_chart(df)

            else:
                st.warning(f"⚠️ Could not load historical data. Error: {hist_data.get('error', {}).get('info', 'Unknown error')}")
    except Exception as e:
        st.error(f"❌ Error loading historical data: {e}")