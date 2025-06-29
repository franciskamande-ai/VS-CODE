# CodeName: EXECUTE v3.0 (Enhanced)
# Features: 
# - Complete entry logic (Z-Score + Kalman Filter)
# - Dynamic position sizing 
# - Volatility-based stops (ATR)
# - Multi-layer error handling
# - Thread-safe architecture

import MetaTrader5 as mt5
from datetime import datetime, timedelta
import time
import requests
import csv
import os
import sys
import numpy as np
import threading
from collections import deque
import signal

# === CONFIGURATION ===
BOT_TOKEN = "8036850178:AAHZuvkQ_tJrsT08kNu3R_Ep1n1OLY3mLSM"
CHAT_ID = "-4980111550"
SYMBOLS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "EURGBP", "EURJPY","BTCUSD", "ETHUSD"]
TIMEFRAME = mt5.TIMEFRAME_M1
BAR_COUNT = 20  # Increased for better signal accuracy
HEARTBEAT_INTERVAL = 3600
ERROR_ALERT_INTERVAL = 1000
EXIT_ALERT_INTERVAL = 500
EXIT_REPEAT_THROTTLE = 500
AUTO_EXECUTE = True
DEFAULT_LOT = 0.1
MAX_LOT = 5.0
MIN_TP_SL = 0.0010
MIN_SL_PIPS = 0.0010
COOLDOWN_AFTER_LOSS = 300
MAX_RECENT_LOSSES = 3
TRAIL_START_PROFIT = 50
TRAIL_OFFSET = 30
Z_SCORE_THRESHOLD = 1.5  # Entry threshold

# === INITIALIZATION ===
class TradingUtils:
    def __init__(self):
        self.price_history = {s: deque(maxlen=100) for s in SYMBOLS}
        self.kalman_states = {s: {"estimate": None, "error": 1.0} for s in SYMBOLS}
        
    def update_history(self, symbol, price):
        self.price_history[symbol].append(price)
        
    def calculate_zscore(self, symbol):
        prices = list(self.price_history[symbol])
        if len(prices) < BAR_COUNT:
            return 0
        mean = np.mean(prices[-BAR_COUNT:])
        std = np.std(prices[-BAR_COUNT:])
        return (prices[-1] - mean)/std if std != 0 else 0
        
    def update_kalman(self, symbol, price):
        # Simplified Kalman Filter
        k = self.kalman_states[symbol]
        if k["estimate"] is None:
            k["estimate"] = price
            return price
        pred_error = k["error"] + 0.1
        kg = pred_error / (pred_error + 0.1)
        k["estimate"] = k["estimate"] + kg * (price - k["estimate"])
        k["error"] = (1 - kg) * pred_error
        return k["estimate"]

utils = TradingUtils()

# === FILE MANAGEMENT ===
log_file = "enhanced_trade_log.csv"
winrate_file = "win_rate.csv"
ml_data_file = "signal_data.csv"

for file_path, headers in [
    (log_file, ["Time", "Symbol", "Action", "Price", "Lot", "SL", "TP", "Z-Score", "Kalman", "Balance"]),
    (winrate_file, ["Symbol", "Wins", "Losses", "WinRate"]),
    (ml_data_file, ["Time", "Symbol", "Price", "Z-Score", "Kalman", "Signal", "TP", "SL", "Result"])
]:
    if not os.path.exists(file_path):
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if file_path == winrate_file:
                for sym in SYMBOLS:
                    writer.writerow([sym, 0, 0, 0])
            else:
                writer.writerow(headers)

# === CORE FUNCTIONS ===
def safe_mt5_execute(func, *args, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            if not mt5.initialize():
                raise ConnectionError("MT5 not connected")
            result = func(*args, **kwargs)
            if result is None or (hasattr(result, 'retcode') and result.retcode != mt5.TRADE_RETCODE_DONE):
                raise mt5.MT5Error("Execution failed")
            return result
        except (mt5.MT5Error, ConnectionError) as e:
            if attempt == max_retries - 1:
                send_telegram(f"🔴 {func.__name__} failed after {max_retries} attempts: {str(e)[:100]}")
                raise
            time.sleep(2)
            mt5.shutdown()

def calculate_atr(symbol, period=14):
    rates = safe_mt5_execute(mt5.copy_rates_from_pos, symbol, mt5.TIMEFRAME_H1, 0, period+1)
    if not rates or len(rates) < period+1:
        return MIN_SL_PIPS
        
    true_ranges = []
    for i in range(1, len(rates)):
        high, low, prev_close = rates[i][2], rates[i][3], rates[i-1][4]
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        true_ranges.append(tr)
    return np.mean(true_ranges)

def calculate_position_size(symbol, price, sl_price):
    acc_info = mt5.account_info()
    if not acc_info or acc_info.balance <= 0:
        return DEFAULT_LOT
        
    risk_amount = acc_info.balance * 0.01  # 1% risk
    point = mt5.symbol_info(symbol).point
    sl_points = abs(price - sl_price) / point
    contract_size = mt5.symbol_info(symbol).trade_contract_size
    lot_size = risk_amount / (sl_points * contract_size * 10)  # Adjusted for FX
    
    return round(np.clip(lot_size, DEFAULT_LOT, MAX_LOT), 2)

def generate_signal(symbol):
    rates = safe_mt5_execute(mt5.copy_rates_from_pos, symbol, TIMEFRAME, 0, BAR_COUNT)
    if not rates or len(rates) < BAR_COUNT:
        return None
        
    current_price = rates[-1][4]
    utils.update_history(symbol, current_price)
    z_score = utils.calculate_zscore(symbol)
    kalman_est = utils.update_kalman(symbol, current_price)
    
    # Entry Logic
    if z_score > Z_SCORE_THRESHOLD and current_price > kalman_est:
        return "SELL", z_score, kalman_est
    elif z_score < -Z_SCORE_THRESHOLD and current_price < kalman_est:
        return "BUY", z_score, kalman_est
    return None, None, None

def place_order(symbol, order_type, price, z_score, kalman_est):
    atr = calculate_atr(symbol)
    if order_type == "BUY":
        sl = price - 1.5 * atr
        tp = price + 2.5 * atr
    else:
        sl = price + 1.5 * atr
        tp = price - 2.5 * atr
    
    lot = calculate_position_size(symbol, price, sl)
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": mt5.ORDER_TYPE_BUY if order_type == "BUY" else mt5.ORDER_TYPE_SELL,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": 234000,
        "comment": f"AUTO_{order_type}_Z{z_score:.1f}",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC
    }
    
    if AUTO_EXECUTE:
        result = safe_mt5_execute(mt5.order_send, request)
        log_trade(symbol, order_type, price, lot, sl, tp, z_score, kalman_est)
        return result
    return None

# === UTILITIES ===
def log_trade(symbol, action, price, lot, sl, tp, z_score, kalman_est):
    with open(log_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            symbol,
            action,
            price,
            lot,
            sl,
            tp,
            f"{z_score:.2f}" if z_score else "",
            f"{kalman_est:.5f}" if kalman_est else "",
            mt5.account_info().balance if mt5.account_info() else 0
        ])

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": message}, timeout=5)
    except Exception as e:
        print(f"Telegram error: {e}")

def shutdown_sequence(signum, frame):
    send_telegram("🔴 Bot shutdown initiated")
    mt5.shutdown()
    sys.exit(0)

# === MAIN LOOP ===
def trading_thread():
    while True:
        try:
            for symbol in SYMBOLS:
                signal, z_score, kalman_est = generate_signal(symbol)
                if not signal:
                    continue
                    
                tick = safe_mt5_execute(mt5.symbol_info_tick, symbol)
                price = tick.ask if signal == "BUY" else tick.bid
                place_order(symbol, signal, price, z_score, kalman_est)
                
            time.sleep(30)
        except Exception as e:
            send_telegram(f"💥 Main loop error: {str(e)[:200]}")
            time.sleep(60)

if __name__ == "__main__":
    if not mt5.initialize():
        send_telegram("❌ MT5 initialization failed")
        sys.exit(1)
        
    signal.signal(signal.SIGINT, shutdown_sequence)
    signal.signal(signal.SIGTERM, shutdown_sequence)
    
    # Start threads
    threading.Thread(target=trading_thread, daemon=True).start()
    
    # Heartbeat monitor
    while True:
        send_telegram(f"❤️ Bot active | Balance: {mt5.account_info().balance if mt5.account_info() else 'N/A'}")
        time.sleep(HEARTBEAT_INTERVAL)