prices = [1.1580, 1.1592, 1.1575, 1.1579, 1.1605]

slope_1 = prices[-1] - prices[-2]  # latest slope
slope_2 = prices[-2] - prices[-3]  # previous slope

if slope_1 > slope_2 and slope_1 > 0:
    print("BUY NOW — Momentum increasing")
elif slope_1 < slope_2 and slope_1 < 0:
    print("SELL NOW — Momentum dropping")
else:
    print("No strong entry")
# This code checks the momentum of the last two price changes and suggests an action based on the trend.
# The code compares the latest price change with the previous one to determine if the momentum is increasing or decreasing.
# If the latest momentum is increasing and positive, it suggests a buy. If it's decreasing and negative, it suggests a sell. Otherwise, it indicates no strong entry point.
# The code is designed to help traders make decisions based on recent price movements.