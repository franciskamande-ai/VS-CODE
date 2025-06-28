import numpy as np

prices = [1.17016,1.16598,1.16084,1.15786,1.16426,1.14966,1.14810,1.14807,1.15609]
x = np.arange(len(prices))
slope, intercept = np.polyfit(x, prices, 1)
regression_line = [slope * i + intercept for i in x]

if prices[-1] > regression_line[-1]:
    print("BUY signal")
elif prices[-1] < regression_line[-1]:
    print("SELL signal")
else:
    print("NO signal")
