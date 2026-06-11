# import requests
# import datetime
# import matplotlib
# matplotlib.use('TkAgg')  # Or 'Qt5Agg' if you have PyQt5 installed
# import matplotlib.pyplot as plt
#
# #import matplotlib.pyplot as plt
#
# # Define the API endpoint and parameters
# url = "https://api.coingecko.com/api/v3/coins/tether/market_chart"
# params = {
#     "vs_currency": "usd",
#     "days": "364"  # Approximate number of days in 10 months
# }
#
# # Fetch the data
# response = requests.get(url, params=params)
# data = response.json()
#
# # Extract timestamps and market caps
# timestamps = [entry[0] for entry in data['market_caps']]
# market_caps = [entry[1] for entry in data['market_caps']]
#
# # Convert timestamps to datetime objects
# dates = [datetime.datetime.fromtimestamp(ts / 1000) for ts in timestamps]
#
# # Plot the data
# plt.figure(figsize=(12, 6))
# plt.plot(dates, market_caps, label="USDT Market Cap (USD)", color="green")
# plt.title("Tether (USDT) Market Cap - Last 10 Months")
# plt.xlabel("Date")
# plt.ylabel("Market Cap (USD)")
# plt.grid(True)
# plt.legend()
# plt.xticks(rotation=45)
# plt.tight_layout()
# plt.show()


import requests
import datetime
import matplotlib
matplotlib.use('TkAgg')  # Or 'Qt5Agg' if you have PyQt5 installed
import matplotlib.pyplot as plt

# Parameters
days = "364"

# Fetch Tether market cap data
usdt_url = "https://api.coingecko.com/api/v3/coins/tether/market_chart"
btc_url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"

params = {"vs_currency": "usd", "days": days}

usdt_response = requests.get(usdt_url, params=params)
btc_response = requests.get(btc_url, params=params)

usdt_data = usdt_response.json()
btc_data = btc_response.json()

# Extract timestamps and values
usdt_dates = [datetime.datetime.fromtimestamp(ts / 1000) for ts, _ in usdt_data["market_caps"]]
usdt_market_caps = [cap for _, cap in usdt_data["market_caps"]]

btc_dates = [datetime.datetime.fromtimestamp(ts / 1000) for ts, _ in btc_data["prices"]]
btc_prices = [price for _, price in btc_data["prices"]]

# Plotting
fig, ax1 = plt.subplots(figsize=(14, 6))

color1 = 'tab:green'
ax1.set_xlabel('Date')
ax1.set_ylabel('USDT Market Cap (USD)', color=color1)
usdt_line, =  ax1.plot(usdt_dates, usdt_market_caps, color=color1, label='USDT Market Cap')
ax1.tick_params(axis='y', labelcolor=color1)

# Add second y-axis for BTC price
ax2 = ax1.twinx()
color2 = 'tab:blue'
ax2.set_ylabel('BTC Price (USD)', color=color2)
btc_line, = ax2.plot(btc_dates, btc_prices, color=color2, label='BTC Price')
ax2.tick_params(axis='y', labelcolor=color2)

plt.title("USDT Market Cap and BTC Price - Last 10 Months")
fig.autofmt_xdate()
plt.tight_layout()
lines = [usdt_line, btc_line]
labels = ['USDT Market Cap', 'BTC Price']
ax2.legend(lines, labels, loc='upper left')
ax1.grid(True)
plt.show()