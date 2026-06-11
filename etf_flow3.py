import yfinance as yf
import pandas as pd

# Define the ETF ticker
etf_ticker = "BITO"  # Replace with the desired Spot BTC ETF ticker.

# Fetch historical price data
etf_data = yf.Ticker(etf_ticker)
historical_data = etf_data.history(period="max")  # Adjust period as needed.

# Placeholder for Shares Outstanding (You must provide or automate this)
# Replace with actual Shares Outstanding data
shares_outstanding_dict = {
    "2024-01-01": 100000000,  # Example data
    "2024-01-02": 100500000,
    # Add more dates and values as needed
}

# Convert to a DataFrame
shares_outstanding_df = pd.DataFrame(list(shares_outstanding_dict.items()), columns=["Date", "Shares Outstanding"])
shares_outstanding_df["Date"] = pd.to_datetime(shares_outstanding_df["Date"])

# Merge price data with Shares Outstanding
historical_data.reset_index(inplace=True)

# Ensure both Date columns are timezone-naive
historical_data['Date'] = historical_data['Date'].dt.tz_localize(None)
shares_outstanding_df['Date'] = shares_outstanding_df['Date'].dt.tz_localize(None)

# Merge price data with Shares Outstanding
merged_data = pd.merge(historical_data, shares_outstanding_df, left_on="Date", right_on="Date", how="left")

# Calculate Market Cap
merged_data["Market Cap"] = merged_data["Close"] * merged_data["Shares Outstanding"]

print(merged_data)
# Save to CSV
