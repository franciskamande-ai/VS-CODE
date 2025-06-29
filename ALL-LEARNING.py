import matplotlib.pyplot as plt

# Data
days = [1, 2, 3, 4, 5]
price = [100, 102, 101, 105, 110]
ma = [100, 101, 101.5, 102.5, 104]

# Create 2 stacked plots
plt.subplot(2, 1, 1)  # (rows, cols, position)
plt.plot(days, price, color='blue')
plt.title("Price")

plt.subplot(2, 1, 2)
plt.plot(days, ma, color='red')
plt.title("Moving Average")

plt.tight_layout()
plt.show()
# Create a single plot with two lines
# Add legend
plt.title("📈 Price vs Moving Average")
plt.xlabel("Day")
plt.ylabel("Price (USD)")
plt.legend("FRANCIS KAMANDE", loc='upper left')

plt.show()
