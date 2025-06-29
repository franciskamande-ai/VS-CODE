import MetaTrader5 as mt5
import pandas as pd
import time
from datetime import datetime
import requests
import pytz
import os

# === CONFIGURATION === #
EMA_FAST = 9
EMA_SLOW = 26
SL_PIPS = 20
BE_TRIGGER_PIPS = 10
CONFIRMATION_PIPS = 3
MIN_LOT = 0.01
MAX_RISK_PER_TRADE = 0.02  # Example: 2%

SYMBOL = "EURUSD"
TIMEFRAME = mt5.TIMEFRAME_M1
MAGIC = 987654
BOT_TOKEN = "8036850178:AAHZuvkQ_tJrsT08kNu3R_Ep1n1OLY3mLSM"
CHAT_ID = "-4980111550"

# === MT5 INITIALIZATION === #
if not mt5.initialize():
    raise RuntimeError(f"MT5 init failed: {mt5.last_error()}")

account_info = mt5.account_info()
if account_info is None:
    raise RuntimeError("Failed to get account info")

balance = account_info.balance
equity = account_info.equity

# === CSV LOGGING SETUP === #
log_file = "trades.csv"
if not os.path.exists(log_file):
    with open(log_file, 'w') as f:
        f.write("Time,Action,Price,Lot,Balance,Trend,9EMA,26EMA,Reason\n")

# === TELEGRAM ALERT === #
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg}
    try:
        requests.post(url, data=payload)
    except:
        pass

# === CALCULATE LOT SIZE === #
def calculate_lot_size(balance, stop_loss_pips):
    risk_amount = balance * MAX_RISK_PER_TRADE
    pip_value = 10  # Adjust for other pairs
    lot = round(risk_amount / (stop_loss_pips * pip_value), 2)
    return lot if lot >= MIN_LOT else MIN_LOT

# === TREND DETECTOR === #
def detect_trend():
    rates = mt5.copy_rates_from_pos(SYMBOL, mt5.TIMEFRAME_H1, 0, 100)
    df = pd.DataFrame(rates)
    df['ema_fast'] = df['close'].ewm(span=9).mean()
    df['ema_slow'] = df['close'].ewm(span=26).mean()
    if df['ema_fast'].iloc[-1] > df['ema_slow'].iloc[-1]:
        return "UPTREND"
    elif df['ema_fast'].iloc[-1] < df['ema_slow'].iloc[-1]:
        return "DOWNTREND"
    else:
        return "SIDEWAYS"

# === ORDER EXECUTION === #
def place_order(order_type, lot, price, sl, comment):
    deviation = 20
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": SYMBOL,
        "volume": lot,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": 0,
        "deviation": deviation,
        "magic": MAGIC,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC
    }
    result = mt5.order_send(request)
    return result

# === LOGGING === #
def log_trade(action, price, lot, reason, ema9, ema26, trend):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = f"{now},{action},{price},{lot},{balance},{trend},{ema9},{ema26},{reason}\n"
    with open(log_file, 'a') as f:
        f.write(row)

# === MAIN LOOP === #
def run_bot():
    in_position = False
    trade_type = None
    entry_price = None

    while True:
        rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 100)
        if rates is None:
            send_telegram("Error: Unable to fetch data.")
            time.sleep(10)
            continue

        df = pd.DataFrame(rates)
        df['ema9'] = df['close'].ewm(span=EMA_FAST).mean()
        df['ema26'] = df['close'].ewm(span=EMA_SLOW).mean()
        ema9_now = df['ema9'].iloc[-1]
        ema26_now = df['ema26'].iloc[-1]
        ema9_prev = df['ema9'].iloc[-2]
        ema26_prev = df['ema26'].iloc[-2]
        price = df['close'].iloc[-1]
        trend = detect_trend()

        # Check crossover
        crossover_up = ema9_prev < ema26_prev and ema9_now > ema26_now
        crossover_down = ema9_prev > ema26_prev and ema9_now < ema26_now

        # Check for entry
        if not in_position:
            if crossover_up and (price > ema9_now + 0.0003):
                lot = calculate_lot_size(balance, SL_PIPS)
                sl = price - (SL_PIPS * 0.0001)
                result = place_order(mt5.ORDER_TYPE_BUY, lot, price, sl, "Buy Signal")
                if result.retcode == 10009:
                    in_position = True
                    trade_type = "BUY"
                    entry_price = price
                    send_telegram(f"✅ BUY @ {price} | Lot: {lot} | Trend: {trend}")
                    log_trade("BUY", price, lot, "9 EMA > 26 EMA", ema9_now, ema26_now, trend)
            elif crossover_down and (price < ema9_now - 0.0003):
                lot = calculate_lot_size(balance, SL_PIPS)
                sl = price + (SL_PIPS * 0.0001)
                result = place_order(mt5.ORDER_TYPE_SELL, lot, price, sl, "Sell Signal")
                if result.retcode == 10009:
                    in_position = True
                    trade_type = "SELL"
                    entry_price = price
                    send_telegram(f"🔻 SELL @ {price} | Lot: {lot} | Trend: {trend}")
                    log_trade("SELL", price, lot, "9 EMA < 26 EMA", ema9_now, ema26_now, trend)

        # Check for exit
        elif in_position:
            if trade_type == "BUY":
                profit_pips = (price - entry_price) / 0.0001
                if profit_pips >= BE_TRIGGER_PIPS:
                    # Move SL to BE — not modifying here for simplicity
                    pass
                if crossover_down and (price < ema9_now - 0.0003):
                    result = place_order(mt5.ORDER_TYPE_SELL, lot, price, price - (SL_PIPS * 0.0001), "TP crossover exit")
                    if result.retcode == 10009:
                        send_telegram(f"📤 BUY CLOSED @ {price} | Reason: Reverse MA Crossover")
                        log_trade("CLOSE_BUY", price, lot, "TP on reverse crossover", ema9_now, ema26_now, trend)
                        in_position = False
            elif trade_type == "SELL":
                profit_pips = (entry_price - price) / 0.0001
                if profit_pips >= BE_TRIGGER_PIPS:
                    # Move SL to BE — not modifying here for simplicity
                    pass
                if crossover_up and (price > ema9_now + 0.0003):
                    result = place_order(mt5.ORDER_TYPE_BUY, lot, price, price + (SL_PIPS * 0.0001), "TP crossover exit")
                    if result.retcode == 10009:
                        send_telegram(f"📤 SELL CLOSED @ {price} | Reason: Reverse MA Crossover")
                        log_trade("CLOSE_SELL", price, lot, "TP on reverse crossover", ema9_now, ema26_now, trend)
                        in_position = False

        time.sleep(10)

# === RUN === #
run_bot()
# Cleanup