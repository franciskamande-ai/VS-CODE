prices = [1.1580, 1.1592, 1.1575, 1.1579, 1.1570]
current_price = prices[-1]

mean = sum(prices) / len(prices)
variance = sum((x - mean)**2 for x in prices) / len(prices)
std_dev = variance ** 0.5

z_score = (current_price - mean) / std_dev

print(f"Z-Score: {z_score:.2f}")

# Entry Trigger
if z_score <= -2:
    print("BUY NOW — Oversold zone")
elif z_score >= 2:
    print("SELL NOW — Overbought zone")
else:
    print("No signal — Wait")
# Exit Trigger
if z_score <= -1:
    print("Exit BUY position")