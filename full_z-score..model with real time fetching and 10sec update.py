import MetaTrader5 as mt5
from datetime import datetime
import time

# Initialize MT5
if not mt5.initialize():
    print("Failed to connect to MT5:", mt5.last_error())
    quit()

symbol = "EURUSD"
timeframe = mt5.TIMEFRAME_D1
price_bars = 5

while True:
    try:
        # 1. Fetch the last 5 daily bars
        now = datetime.now()
        rates = mt5.copy_rates_from(symbol, timeframe, now, price_bars)
        if rates is None or len(rates) < price_bars:
            print("Not enough price data.")
            time.sleep(10)
            continue

        # 2. Get closing prices
        prices = [bar['close'] for bar in rates]

        # 3. Get current price from live tick
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            print("Tick data unavailable.")
            time.sleep(10)
            continue
        current_price = tick.ask  # or use (ask + bid)/2
        #DECIDED TO ADD TREND DIRECTION JUST NOT TO GET CAUGHT ON THE OPPOSITE SIDE OF THE TREND
        prev_price = prices[-2]  # last closing price from the fetched bars

        #determine trend direction
        if current_price > prev_price:
            trend = "Bullish"
        elif current_price < prev_price:
            trend = "Bearish"
        else:
            trend = "Sideways"

        # 4. Calculate Z-Score
        mean = sum(prices) / len(prices)
        variance = sum((x - mean)**2 for x in prices) / len(prices)
        std_dev = variance ** 0.5
        z_score = (current_price - mean) / std_dev

        print(f"\nCurrent Price: {current_price:.5f}")
        print(f"Z-Score: {z_score:.2f}")
        print(f"Trend Direction: {trend}")

        # 5. Entry signal logic
        if z_score <= -2:
            print("📈 BUY NOW — Oversold zone")
        elif z_score >= 2:
            print("📉 SELL NOW — Overbought zone")
        else:
            print("⏳ No signal — Wait")

        # 6. Exit signal logic (for existing BUY)
        if z_score <= -1:
            print("❌ Exit BUY position")

        time.sleep(10)  # Wait 10 seconds before checking again

    except Exception as e:
        print("Error:", e)
        time.sleep(10)

# Shutdown MT5 when done
mt5.shutdown()
