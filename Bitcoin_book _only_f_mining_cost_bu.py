
import json
import requests
import pandas as pd
import matplotlib
matplotlib.use("TkAgg")

import matplotlib.pyplot as plt

from datetime import datetime


# =========================================================
# HALVING DATES
# =========================================================

HALVINGS = [
    datetime(2012, 11, 28),
    datetime(2016, 7, 9),
    datetime(2020, 5, 11),
    datetime(2024, 4, 19),
    datetime(2028, 3, 31),
]


# =========================================================
# DATA URLS
# =========================================================

URLS = {
    "Price":
        "https://api.blockchain.info/charts/market-price"
        "?timespan=18years"
        "&rollingAverage=24hours"
        "&start=2010-01-01"
        "&format=json"
        "&sampled=false",

    "fees":
        "https://api.blockchain.info/charts/transaction-fees"
        "?timespan=18years"
        "&rollingAverage=24hours"
        "&start=2010-01-01"
        "&format=json"
        "&sampled=false",
}


# =========================================================
# DOWNLOAD FUNCTION
# =========================================================

def download_series(name, url):

    print(f"Downloading {name}...")

    data = requests.get(url).json()["values"]

    df = pd.DataFrame(data)

    df["Date"] = pd.to_datetime(df["x"], unit="s")

    df = df.rename(columns={"y": name})

    df = df.set_index("Date")[[name]]

    return df.resample("D").last()


# =========================================================
# BTC REWARD
# =========================================================

def btc_reward(date):

    reward = 50.0

    for h in HALVINGS:
        if date >= h:
            reward /= 2

    return reward


# =========================================================
# HALVING LINES
# =========================================================

def add_halving_lines(ax):

    for i, h in enumerate(HALVINGS, 1):

        ax.axvline(
            h,
            color="red",
            linestyle="--",
            alpha=0.6
        )

        ax.text(
            h,
            ax.get_ylim()[0],
            f" Halving {i}",
            rotation=90,
            va="bottom"
        )


# =========================================================
# MAIN
# =========================================================

def main():

    # -----------------------------------------------------
    # DOWNLOAD DATA
    # -----------------------------------------------------

    df = None

    for name, url in URLS.items():

        s = download_series(name, url)

        if df is None:
            df = s
        else:
            df = df.join(s, how="left")

    # -----------------------------------------------------
    # CLEAN DATA
    # -----------------------------------------------------

    df["fees"] = df["fees"].fillna(0)

    # -----------------------------------------------------
    # REWARD
    # -----------------------------------------------------

    df["Reward"] = df.index.map(btc_reward)

    # -----------------------------------------------------
    # MINING COST
    # -----------------------------------------------------

    # 6 blocks/hour
    # annualized
    # in billions USD

    df["Mining cost"] = (
        df["Price"]
        * df["Reward"]
        * 6
        * 24
        * 365
        / 1_000_000_000
    )

    # -----------------------------------------------------
    # FEES COST
    # -----------------------------------------------------

    df["Fees cost"] = (
        df["fees"]
        * df["Price"]
        * 365
        / 1_000_000_000
    )

    # -----------------------------------------------------
    # TOTAL COST
    # -----------------------------------------------------

    df["Total cost"] = (
        df["Mining cost"]
        + df["Fees cost"]
    )

    # -----------------------------------------------------
    # MOVING AVERAGES
    # -----------------------------------------------------

    df["Total cost MA 90"] = (
        df["Total cost"]
        .rolling(90)
        .mean()
    )

    df["Total cost MA 365"] = (
        df["Total cost"]
        .rolling(365)
        .mean()
    )

    df["Total cost MA 730"] = (
        df["Total cost"]
        .rolling(730)
        .mean()
    )

    # =====================================================
    # PLOT
    # =====================================================

    fig, ax1 = plt.subplots(figsize=(12, 6))

    # -----------------------------------------------------
    # LEFT AXIS : PRICE
    # -----------------------------------------------------

    ax1.set_yscale("log")

    ax1.set_ylabel(
        "Price (log scale)",
        color="tab:blue"
    )

    ax1.plot(
        df.index,
        df["Price"],
        color="tab:blue",
        label="Price"
    )

    ax1.tick_params(
        axis="y",
        labelcolor="tab:blue"
    )

    # -----------------------------------------------------
    # RIGHT AXIS : COST
    # -----------------------------------------------------

    ax2 = ax1.twinx()

    ax2.set_ylabel(
        "total_cost (fee+reward)",
        color="tab:red"
    )

    ax2.plot(
        df.index,
        df["Total cost"],
        color="tab:red",
        label="Mining total cost (fee+reward)"
    )

    ax2.plot(
        df.index,
        df["Total cost MA 365"],
        color="tab:green",
        label="Mining total cost MA 365"
    )

    ax2.plot(
        df.index,
        df["Total cost MA 730"],
        color="tab:orange",
        label="Mining total cost MA 730"
    )

    ax2.plot(
        df.index,
        df["Total cost MA 90"],
        color="tab:olive",
        label="Mining total cost MA 90"
    )

    ax2.tick_params(
        axis="y",
        labelcolor="tab:red"
    )

    ax2.set_ylim(0, 45)

    # -----------------------------------------------------
    # LEGEND
    # -----------------------------------------------------

    lines1, labels1 = ax1.get_legend_handles_labels()

    lines2, labels2 = ax2.get_legend_handles_labels()

    ax1.legend(
        lines1 + lines2,
        labels1 + labels2,
        loc="upper left"
    )

    # -----------------------------------------------------
    # TITLE + GRID
    # -----------------------------------------------------

    plt.title("Bitcoin Price and Mining Cost")

    add_halving_lines(ax1)

    plt.grid(True)

    plt.tight_layout()

    # KEEP WINDOW OPEN
    plt.show(block=True)


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()

