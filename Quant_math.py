prices = [1.17016,1.16598,1.16084,1.15786,1.16426,1.14966,1.14810,1.14807,1.15609]
current_price = 1.16980  # use latest candle or live price here

mean = sum(prices) / len(prices)
print(f"Mean: {mean:.5f}")

variance = sum((x - mean)**2 for x in prices) / len(prices)
print(f"Variance: {variance:.10f}")

std_dev = variance ** 0.5
print(f"Standard Deviation: {std_dev:.5f}")

z_score = (current_price - mean) / std_dev
print(f"Z-Score: {z_score:.2f}")
