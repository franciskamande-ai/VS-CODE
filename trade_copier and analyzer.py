import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("📁 Rider's Trade Log Analyzer")
st.subheader("Upload your trade history to view and analyze it.")

# 1. Upload the CSV file
uploaded_file = st.file_uploader("Upload your trade history CSV", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # 2. Display the raw data
    st.success("✅ File uploaded successfully!")
    st.dataframe(df)

    # 3. Calculate profits
    def calculate_profit(row):
        if row['direction'].lower() == 'buy':
            return (row['exit'] - row['entry']) * row['lot'] * 10000
        else:
            return (row['entry'] - row['exit']) * row['lot'] * 10000

    df['profit'] = df.apply(calculate_profit, axis=1)

    # 4. Filter section
    st.sidebar.header("📊 Filter Your Trades")
    symbols = df['symbol'].unique().tolist()
    directions = df['direction'].unique().tolist()

    selected_symbol = st.sidebar.selectbox("Symbol", ["All"] + symbols)
    selected_direction = st.sidebar.selectbox("Direction", ["All"] + directions)

    # 5. Apply filters
    filtered_df = df.copy()
    if selected_symbol != "All":
        filtered_df = filtered_df[filtered_df['symbol'] == selected_symbol]
    if selected_direction != "All":
        filtered_df = filtered_df[filtered_df['direction'] == selected_direction]

    st.subheader("📈 Filtered Trade Data")
    st.dataframe(filtered_df)

    # 6. Plotting Profit Over Time
    if 'date' in df.columns:
        filtered_df['date'] = pd.to_datetime(filtered_df['date'])
        profit_by_date = filtered_df.groupby('date')['profit'].sum()

        st.subheader("💹 Profit Over Time")
        fig, ax = plt.subplots()
        profit_by_date.plot(kind='line', marker='o', ax=ax)
        ax.set_ylabel("Profit ($)")
        ax.set_xlabel("Date")
        ax.set_title("Profit Timeline")
        st.pyplot(fig)

    # 7. Total Profit
    total_profit = filtered_df['profit'].sum()
    st.success(f"📊 Total Profit in Filtered Data: ${total_profit:.2f}")
