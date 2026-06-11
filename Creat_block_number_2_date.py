import os
import requests
import pandas as pd
from datetime import datetime, timedelta

# --- Settings ---
csv_file = 'daily_block_heights.csv'
start_date = datetime(2009, 2, 1)
today = datetime.today()
temp_records = []

# --- Load existing data if exists ---
if os.path.exists(csv_file):
    df_main = pd.read_csv(csv_file, parse_dates=['date'])
    last_date = df_main['date'].max()
    current_date = last_date + timedelta(days=1)
    print(f"Resuming from {current_date.strftime('%Y-%m-%d')}")
else:
    df_main = pd.DataFrame(columns=['date', 'block'])
    current_date = start_date
    print(f"Starting from {current_date.strftime('%Y-%m-%d')}")

# --- Main loop ---
while current_date <= today:
    date_str = current_date.strftime('%Y-%m-%d')
    url = f'https://blockchain.info/blocks/{int(current_date.timestamp() * 1000)}?format=json'

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        blocks = response.json()
        if blocks:
            # Take the first block of the day
            first_block_height = blocks[0]['height']
            temp_records.append({'date': current_date, 'block': first_block_height})
            print(f"{date_str} -> block {first_block_height}")
        else:
            print(f"{date_str}: block not found, skipping")
    except Exception as e:
        print(f"{date_str}: error {e}, skipping")

    # Save yearly: on Dec 31 or last day
    if (current_date.month == 12 and current_date.day == 31) or current_date == today:
        if temp_records:
            df_temp = pd.DataFrame(temp_records)
            df_main = pd.concat([df_main, df_temp], ignore_index=True)
            df_main.to_csv(csv_file, index=False)
            temp_records = []
            print(f"Saved data up to {date_str}")

    # Next day
    current_date += timedelta(days=1)

# --- Ensure any remaining days are saved at the very end ---
if temp_records:
    df_temp = pd.DataFrame(temp_records)
    df_main = pd.concat([df_main, df_temp], ignore_index=True)
    df_main.to_csv(csv_file, index=False)
    print(f"Final save up to {today.strftime('%Y-%m-%d')}")