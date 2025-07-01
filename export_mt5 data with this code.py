import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

# Connect to MT5
if not mt5.initialize():
    raise RuntimeError("MT5 not initialized")

symbol = "EURUSD"
timeframe = mt5.TIMEFRAME_M1  # Or TIMEFRAME_M1
start = datetime(2022, 4, 1)   # Start date
end = datetime(2023, 6, 1)     # End date

rates = mt5.copy_rates_range(symbol, timeframe, start, end)
df = pd.DataFrame(rates)
df['time'] = pd.to_datetime(df['time'], unit='s')
df = df[['time', 'open', 'high', 'low', 'close', 'tick_volume']]
df.rename(columns={'time': 'datetime', 'tick_volume': 'volume'}, inplace=True)

df.to_csv("EURUSD_M15.csv", index=False)
print("✅ Data exported.")
# Shutdown MT5 connection