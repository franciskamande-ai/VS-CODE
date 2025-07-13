import MetaTrader5 as mt5
import pandas as pd
import talib

# Connect to MT5
if not mt5.initialize():
    print("MT5 init failed")
    quit()

symbol = "USDJPY"
timeframe = mt5.TIMEFRAME_M15
bars = 100
lot = 0.1
magic_number = 123456

# Get OHLCV
rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
df = pd.DataFrame(rates)
df['time'] = pd.to_datetime(df['time'], unit='s')

# Calculate EMAs
close = df['close'].values
df['ema20'] = talib.EMA(close, timeperiod=20)
df['ema50'] = talib.EMA(close, timeperiod=50)

# Generate latest signal
last_ema20 = df['ema20'].iloc[-1]
last_ema50 = df['ema50'].iloc[-1]
signal = 1 if last_ema20 > last_ema50 else -1  # 1 = BUY, -1 = SELL

# Get current open position for this symbol
positions = mt5.positions_get(symbol=symbol)

def close_position(position):
    price = mt5.symbol_info_tick(symbol).bid if position.type == mt5.POSITION_TYPE_BUY else mt5.symbol_info_tick(symbol).ask
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": position.volume,
        "type": mt5.ORDER_TYPE_SELL if position.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY,
        "price": price,
        "position": position.ticket,
        "deviation": 10,
        "magic": magic_number,
        "comment": "Exit on EMA Crossover",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    print("Closed position:", result)

def open_order(order_type):
    price = mt5.symbol_info_tick(symbol).ask if order_type == "buy" else mt5.symbol_info_tick(symbol).bid
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": mt5.ORDER_TYPE_BUY if order_type == "buy" else mt5.ORDER_TYPE_SELL,
        "price": price,
        "deviation": 10,
        "magic": magic_number,
        "comment": "EMA Entry",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    print("Opened", order_type.upper(), "order:", result)

# Decision logic
if positions:
    position = positions[0]
    if signal == 1 and position.type == mt5.POSITION_TYPE_SELL:
        close_position(position)
        open_order("buy")
    elif signal == -1 and position.type == mt5.POSITION_TYPE_BUY:
        close_position(position)
        open_order("sell")
    else:
        print("Position exists, no action.")
else:
    if signal == 1:
        open_order("buy")
    elif signal == -1:
        open_order("sell")

# Done
mt5.shutdown()
