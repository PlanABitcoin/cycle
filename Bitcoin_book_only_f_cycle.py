import pandas as pd
import requests
import json
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
from datetime import datetime, timedelta

plt.close("all")

bitcoin_halving_dates = [
    datetime(2012, 11, 28),
    datetime(2016, 7, 9),
    datetime(2020, 5, 11),
    datetime(2024, 4, 19),
    datetime(2028, 3, 31),
]

PRICE_URL = (
    "https://api.blockchain.info/charts/market-price?"
    "timespan=18years"
    "&rollingAverage=24hours"
    "&start=2010-01-01"
    "&format=json"
    "&sampled=false"
)


def fetch_price():
    print("Downloading Bitcoin price...")
    r = requests.get(PRICE_URL)
    r.raise_for_status()

    data = json.loads(r.content)
    df = pd.DataFrame(data["values"])

    df["Date"] = pd.to_datetime(df["x"], unit="s", utc=True)
    df["Price"] = df["y"]

    df = df[["Date", "Price"]]
    df.set_index("Date", inplace=True)
    df = df.resample("D").last()
    df.index = df.index.tz_localize(None)

    return df


def mark_bitcoin_halvings(ax, halving_dates, color="red", linestyle="-", alpha=0.6):
    for i, date in enumerate(halving_dates, 1):
        ax.axvline(date, color=color, linestyle=linestyle, alpha=alpha)
        ax.text(
            date,
            ax.get_ylim()[0],
            f" Halving {i}",
            rotation=90,
            ha="right",
            va="bottom",
        )

        if i < len(bitcoin_halving_dates):
            mid_date = date + (bitcoin_halving_dates[i] - date) / 2
            ax.axvline(mid_date, color="red", linestyle="--", alpha=0.6)
            ax.text(
                mid_date,
                ax.get_ylim()[0],
                " mid",
                rotation=90,
                ha="right",
                va="bottom",
            )


df = fetch_price()
df = df.resample("D").last()

# Calculate cycle maxima exactly as in your original code
max_values_for_halving_periods = []

for i in range(len(bitcoin_halving_dates)):
    if i == 0:
        start_date = df.index[0]
    else:
        start_date = bitcoin_halving_dates[i - 1]

    end_date = bitcoin_halving_dates[i]
    reduced_end_date = end_date - timedelta(days=60)

    subset = df[
        (df.index >= start_date) &
        (df.index <= reduced_end_date)
    ]

    max_value = subset["Price"].max()
    max_date = subset.loc[subset["Price"].idxmax()].name

    max_values_for_halving_periods.append(
        (start_date, end_date, max_date, max_value, max_date, max_value)
    )

# Generate only the cycle figure
plt.figure(figsize=(12, 7))

ax = df["Price"].plot(logy=True)

plt.ylabel("USD")
ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
plt.grid(True)

x_limit = datetime(2028, 6, 1)
plt.xlim(df.index[0], x_limit)

mark_bitcoin_halvings(ax, bitcoin_halving_dates)

i = 0

for start_date, end_date, max_date, max_value, max_date, max_value in max_values_for_halving_periods:
    subset = df[
        (df.index >= max_date) &
        (df.index <= end_date)
    ]

    min_value = subset["Price"].min()
    min_date = subset.loc[subset["Price"].idxmin()].name

    plt.scatter(max_date, max_value, c="red", marker="o")

    if i < 4:
        plt.scatter(min_date, min_value, c="blue", marker="x")

        plt.annotate(
            "",
            xy=(min_date, min_value),
            xytext=(max_date, max_value),
            arrowprops=dict(arrowstyle="->", color="black"),
        )

    if i > 0:
        plt.annotate(
            "",
            xy=(max_date, max_value),
            xytext=(prev_min_date, prev_min),
            arrowprops=dict(arrowstyle="->", color="black"),
        )

    prev_min = min_value
    prev_min_date = min_date

    i += 1

plt.tight_layout()
plt.show()