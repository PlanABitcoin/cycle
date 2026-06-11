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
    datetime(2028, 3, 31)
]

PRICE_URL = (
    "https://api.blockchain.info/charts/market-price?"
    "timespan=18years"
    "&rollingAverage=24hours"
    "&start=2010-01-01"
    "&format=json"
    "&sampled=false"
)

print("Downloading Bitcoin price...")

response = requests.get(PRICE_URL)
response.raise_for_status()
data = json.loads(response.content)

df = pd.DataFrame(data["values"])
df["Date"] = pd.to_datetime(df["x"], unit="s", utc=True)
df["Price"] = df["y"]

df = df[["Date", "Price"]]
df.set_index("Date", inplace=True)
df = df.resample("D").last()
df.index = df.index.tz_localize(None)

# --------------------------------------------------
# Mark halving and mid-halving lines
# exactly like your original code
# --------------------------------------------------

def mark_bitcoin_halvings(ax, halving_dates, color="red", linestyle="-", alpha=0.6):
    for i, date in enumerate(halving_dates, 1):
        ax.axvline(
            date,
            color=color,
            linestyle=linestyle,
            alpha=alpha,
            label="Bitcoin Halving"
        )

        ax.text(
            date,
            ax.get_ylim()[0],
            f" Halving {i}",
            rotation=90,
            ha="right",
            va="bottom"
        )

        if i < len(bitcoin_halving_dates):
            mid_date = date + (bitcoin_halving_dates[i] - date) / 2

            plt.axvline(
                mid_date,
                color="red",
                linestyle="--",
                alpha=0.6
            )

            ax.text(
                mid_date,
                ax.get_ylim()[0],
                " mid",
                rotation=90,
                ha="right",
                va="bottom"
            )

# --------------------------------------------------
# Calculate max values exactly like your original code
# --------------------------------------------------

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
        (
            start_date,
            end_date,
            max_date,
            max_value,
            max_date,
            max_value
        )
    )

# --------------------------------------------------
# Generate only f_cycle_dates
# --------------------------------------------------

plt.figure(figsize=(12, 7))

ax = df["Price"].plot(logy=True)

plt.ylabel("USD")
ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
plt.grid(True)

x_limit = datetime(2028, 6, 1)
plt.xlim(df.index[0], x_limit)

mark_bitcoin_halvings(ax, bitcoin_halving_dates)

# --------------------------------------------------
# Add arrows and exact date labels for halvings
# exactly like your original code
# --------------------------------------------------

for idx, halving_date in enumerate(bitcoin_halving_dates):

    if idx == 0:
        x_offset = 40
    else:
        x_offset = -40 if idx % 2 == 0 else 40

    y_arrow_target = 2
    y_text_offset = 25

    label_text = halving_date.strftime("%Y-%m-%d")

    if idx == 4:
        label_text = f"Predicted\n{halving_date.strftime('%Y-%m-%d')}"

    plt.annotate(
        label_text,
        xy=(halving_date, y_arrow_target),
        xytext=(x_offset, y_text_offset),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=10,
        color="darkred",
        bbox=dict(
            boxstyle="round,pad=0.2",
            fc="white",
            ec="darkred",
            alpha=0.8
        ),
        arrowprops=dict(
            arrowstyle="->",
            color="darkred",
            lw=0.8
        )
    )

# --------------------------------------------------
# Max, min, and arrows exactly like your original code
# --------------------------------------------------

i = 0

for start_date, end_date, max_date, max_value, max_date, max_value in max_values_for_halving_periods:

    subset = df[
        (df.index >= max_date) &
        (df.index <= end_date)
    ]

    min_value = subset["Price"].min()
    min_date = subset.loc[subset["Price"].idxmin()].name

    plt.scatter(max_date, max_value, c="red", marker="o", s=50)

    if i > 0:
        plt.annotate(
            max_date.strftime("%Y-%m-%d"),
            xy=(max_date, max_value),
            xytext=(0, 15),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=12,
            color="red",
            arrowprops=dict(
                arrowstyle="->",
                color="red",
                lw=0.8
            )
        )

    if i < 4:
        plt.scatter(min_date, min_value, c="blue", marker="x", s=60)

        if i > 0:
            plt.annotate(
                min_date.strftime("%Y-%m-%d"),
                xy=(min_date, min_value),
                xytext=(0, -25),
                textcoords="offset points",
                ha="center",
                va="top",
                fontsize=12,
                color="blue",
                arrowprops=dict(
                    arrowstyle="->",
                    color="blue",
                    lw=0.8
                )
            )

        plt.annotate(
            "",
            xy=(min_date, min_value),
            xytext=(max_date, max_value),
            arrowprops=dict(
                arrowstyle="->",
                color="black",
                lw=1
            )
        )

    dur_down = min_date.date() - max_date.date()

    if i > 0:
        dur_up = max_date.date() - prev_min_date.date()

        plt.annotate(
            "",
            xy=(max_date, max_value),
            xytext=(prev_min_date, prev_min),
            arrowprops=dict(
                arrowstyle="->",
                color="black",
                lw=1
            )
        )

        print(
            f"Between {start_date.date()} and {end_date.date()}: "
            f"Max Price = {max_value:>7.1f} on {max_date.date()} "
            f"Min Price = {min_value:>7.1f} on {min_date.date()} "
            f"down fac={max_value/min_value:.1f} "
            f"up fac={max_value/prev_min:>5.1f} "
            f"dur_down={dur_down.days} dur_up={dur_up.days}"
        )

    else:
        print(
            f"Between {start_date.date()} and {end_date.date()}: "
            f"Max Price = {max_value:>7.1f} on {max_date.date()} "
            f"Min Price = {min_value:>7.1f} on {min_date.date()} "
            f"down fac={max_value/min_value:5.1f} "
            f"dur_down={dur_down.days}"
        )

    prev_min = min_value
    prev_min_date = min_date

    if i == 3:
        max_date_pred = min_date + timedelta(days=1000)
        max_value_pred1 = min_value * 5
        max_value_pred2 = min_value * 8
        max_value_pred3 = min_value * 11

    if i == 4:
        min_date_pred = max_date + timedelta(days=340)
        min_value_pred1 = max_value / 2
        min_value_pred2 = max_value / 3
        min_value_pred3 = max_value / 4

    i += 1

plt.tight_layout()

#plt.savefig("f_cycle_dates.pdf", bbox_inches="tight")
#plt.savefig("f_cycle_dates.png", dpi=300, bbox_inches="tight")

plt.show()