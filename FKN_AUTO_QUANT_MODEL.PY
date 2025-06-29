# CodeName: EXECUTE v2.5.3
# Patch: Added trailing stop logic after $50 profit, no direct closures

import MetaTrader5 as mt5
from datetime import datetime, timedelta
import time
import requests
import csv
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

# === CONFIGURATION ===
BOT_TOKEN = "8036850178:AAHZuvkQ_tJrsT08kNu3R_Ep1n1OLY3mLSM"
CHAT_ID = "-4980111550"
SYMBOLS = ["EURUSD", "GBPUSD","USDJPY", "AUDUSD","EURGBP", "EURJPY"]
TIMEFRAME = mt5.TIMEFRAME_M1
BAR_COUNT = 6
HEARTBEAT_INTERVAL = 3600
ERROR_ALERT_INTERVAL = 1000
EXIT_ALERT_INTERVAL = 500
EXIT_REPEAT_THROTTLE = 500
AUTO_EXECUTE = True
DEFAULT_LOT = 0.1
MIN_TP_SL = 0.0010
MIN_SL_PIPS = 0.0010
COOLDOWN_AFTER_LOSS = 300
REVERSE_LOGIC_FOR = {"GBPUSD": True, "EURUSD": False}
MAX_RECENT_LOSSES = 3
TRAIL_START_PROFIT = 50
TRAIL_OFFSET = 30  # distance in profit $ to maintain from peak
ml_result_checked = set()

log_file = "trade_log.csv"
winrate_file = "win_rate.csv"
ml_data_file = "FKN_MODEL_SIGNAL_DATA.csv"

for file_path, headers in [
    (log_file, ["Time", "Symbol", "Action", "Price", "Z-Score", "Kalman Est", "Trend", "Momentum"]),
    (winrate_file, ["Symbol", "Wins", "Losses"]),
    (ml_data_file, ["Time", "Symbol", "Price", "Z-Score", "Kalman", "Trend", "Momentum", "Signal", "TP", "SL", "Result"])
]:
    if not os.path.exists(file_path):
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if file_path == winrate_file:
                for sym in SYMBOLS:
                    writer.writerow([sym, 0, 0])
            else:
                writer.writerow(headers)

def update_winrate(symbol, won):
    rows = []
    with open(winrate_file, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
    for row in rows:
        if row[0] == symbol:
            if won:
                row[1] = str(int(row[1]) + 1)
            else:
                row[2] = str(int(row[2]) + 1)
    with open(winrate_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

def store_ml_data(symbol, price, z_score, kalman, trend, momentum, signal, tp, sl, result="pending"):
    with open(ml_data_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now(), symbol, price, z_score, kalman, trend, momentum, signal, tp, sl, result])

def update_ml_result(symbol, timestamp, result):
    rows = []
    with open(ml_data_file, 'r', newline='', encoding='utf-8') as f:
        rows = list(csv.reader(f))
    for row in rows:
        if symbol == row[1] and result in ["win", "loss"]:
            if row[-1] == "pending" and row[0].startswith(timestamp[:16]):
                row[-1] = result
                break
    with open(ml_data_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    except Exception as e:
        print(f"💥 Telegram send error: {e}")

if not mt5.initialize():
    print("❌ MT5 initialization failed:", mt5.last_error())
    send_telegram(f"❌ MT5 initialization failed: {mt5.last_error()}")
    quit()

def calculate_lot(symbol, risk_pct=0.01, fallback=0.01):
    acc_info = mt5.account_info()
    if acc_info is None or acc_info.balance <= 0:
        return fallback
    risk_amount = acc_info.balance * risk_pct
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None or symbol_info.trade_contract_size <= 0:
        return fallback
    tick = mt5.symbol_info_tick(symbol)
    if not tick or tick.ask == 0:
        return fallback
    price = tick.ask
    sl_pips = 30
    pip_value = symbol_info.trade_contract_size * 0.0001
    lot = risk_amount / (sl_pips * pip_value)
    return fallback if lot < fallback else round(min(lot, symbol_info.volume_max), 2)

def recent_losses(symbol):
    try:
        with open(log_file, 'r', newline='', encoding='utf-8') as f:
            reader = list(csv.reader(f))[-20:]
            filtered = [r for r in reader if r[1] == symbol and 'SELL' in r[2] or 'BUY' in r[2]]
            return sum(1 for r in filtered[-MAX_RECENT_LOSSES:] if 'LOSS' in r[2].upper())
    except:
        return 0

def trail_stop(symbol):
    positions = mt5.positions_get(symbol=symbol)
    if positions:
        for pos in positions:
            if pos.profit >= TRAIL_START_PROFIT:
                price = mt5.symbol_info_tick(symbol).bid if pos.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).ask
                sl_price = price - TRAIL_OFFSET * 0.0001 if pos.type == mt5.ORDER_TYPE_BUY else price + TRAIL_OFFSET * 0.0001
                sl_price = round(sl_price, 5)
                if abs(sl_price - pos.sl) > 0.00005:
                    mt5.order_send({
                        "action": mt5.TRADE_ACTION_SLTP,
                        "position": pos.ticket,
                        "sl": sl_price,
                        "tp": pos.tp,
                        "symbol": symbol,
                        "magic": 234000,
                        "comment": "TRAIL_SL_UPDATE"
                    })

def place_order(symbol, order_type, lot, sl, tp):
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        return "Tick data missing"
    price = tick.ask if order_type == "BUY" else tick.bid
    order_type_const = mt5.ORDER_TYPE_BUY if order_type == "BUY" else mt5.ORDER_TYPE_SELL

    sl = round(price - MIN_SL_PIPS if order_type == "BUY" else price + MIN_SL_PIPS, 5)
    tp = round(price + MIN_SL_PIPS if order_type == "BUY" else price - MIN_SL_PIPS, 5)

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": order_type_const,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": 234000,
        "comment": f"EXECUTE_AUTO_{order_type}",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC
    }
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        request["volume"] = 0.01
        return mt5.order_send(request)
    store_ml_data(symbol, price, 0, 0, "-", "-", order_type, tp, sl)
    return result

# === RUNTIME STATE ===
kalman_states = {s: None for s in SYMBOLS}
last_signal = {s: None for s in SYMBOLS}
last_heartbeat = {s: 0 for s in SYMBOLS}
last_error_alert = {s: 0 for s in SYMBOLS}
last_exit_alert = {s: 0 for s in SYMBOLS}
last_loss_time = {s: 0 for s in SYMBOLS}

while True:
    for symbol in SYMBOLS:
        try:
            if not mt5.symbol_select(symbol, True):
                continue

            trail_stop(symbol)

            rates = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 0, BAR_COUNT)
            if rates is None or len(rates) < BAR_COUNT:
                now = datetime.now() - timedelta(minutes=5)
                rates = mt5.copy_rates_from(symbol, TIMEFRAME, now, BAR_COUNT)
            if rates is None or len(rates) < BAR_COUNT:
                if time.time() - last_error_alert[symbol] >= ERROR_ALERT_INTERVAL:
                    send_telegram(f"⚠️ Not enough data for {symbol} (Bars: {len(rates) if rates else 0})")
                    last_error_alert[symbol] = time.time()
                continue

            if recent_losses(symbol) >= MAX_RECENT_LOSSES:
                continue

            if time.time() - last_exit_alert[symbol] > EXIT_REPEAT_THROTTLE:
                last_exit_alert[symbol] = time.time()
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {symbol}: WAITING — Weak signal")
                send_telegram(f"📢 ⏳ WAIT\n❌ EXIT — Weak confirmation [{symbol}]")

        except Exception as e:
            if time.time() - last_error_alert[symbol] >= ERROR_ALERT_INTERVAL:
                send_telegram(f"💥 Error with {symbol}: {e}")
                last_error_alert[symbol] = time.time()

    deals = mt5.history_deals_get(datetime.now() - timedelta(days=1), datetime.now())
    if deals:
        for d in deals:
            if d.comment.startswith("EXECUTE_AUTO_"):
                key = f"{d.symbol}_{d.time}"
                if key in ml_result_checked:
                    continue
                ml_result_checked.add(key)
                outcome = "win" if d.profit > 0 else "loss"
                update_ml_result(d.symbol, str(datetime.fromtimestamp(d.time)), outcome)

    time.sleep(30)

mt5.shutdown()
# Final cleanup
