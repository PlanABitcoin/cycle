import os
import json
import requests
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("TkAgg")

import matplotlib.pyplot as plt


PRICE_URL = (
    "https://api.blockchain.info/charts/market-price?"
    "timespan=18years&rollingAverage=24hours"
    "&start=2010-01-01"
    "&format=json&sampled=false"
)

CSV_FILE = "daily_block_heights.csv"
BLOCKS_PER_CYCLE = 210_000
OUTPUT_FILE = "f_dem1.pdf"


def fetch_price_data():
    print("Downloading Bitcoin price data...")

    response = requests.get(PRICE_URL)
    response.raise_for_status()

    data = response.json()["values"]

    df = pd.DataFrame(data)
    df["Date"] = pd.to_datetime(df["x"], unit="s", utc=True)
    df["Price"] = df["y"]

    df = df[["Date", "Price"]]
    df.set_index("Date", inplace=True)
    df = df.resample("D").last()
    df = df.tz_localize(None)

    return df


def load_block_data(df):
    if not os.path.exists(CSV_FILE):
        raise FileNotFoundError(f"{CSV_FILE} not found")

    df_blocks = pd.read_csv(CSV_FILE, parse_dates=["date"])
    df_blocks.set_index("date", inplace=True)

    if "block" not in df_blocks.columns:
        raise ValueError("CSV must contain a column named 'block'")

    full_index = pd.date_range(df.index.min(), df.index.max(), freq="D")
    df_blocks = df_blocks.reindex(full_index)

    df_blocks["block_number"] = df_blocks["block"]

    missing = df_blocks["block_number"].isna()

    if missing.any():
        last_idx = df_blocks["block_number"].last_valid_index()
        last_value = df_blocks.loc[last_idx, "block_number"]

        for i, date in enumerate(df_blocks.index[missing], start=1):
            df_blocks.loc[date, "block_number"] = last_value + 144 * i

    df_blocks["block_number"] = df_blocks["block_number"].astype(int)

    df = df.merge(
        df_blocks[["block_number"]],
        left_index=True,
        right_index=True,
        how="left"
    )

    return df


def plot_diminishing_returns(df):
    blocks = df["block_number"].values
    prices = df["Price"].values

    halving_blocks = np.arange(
        BLOCKS_PER_CYCLE,
        blocks[-1] + BLOCKS_PER_CYCLE,
        BLOCKS_PER_CYCLE
    )

    num_cycles = len(halving_blocks)

    colors = [
        "#1f77b4",
        "#ff7f0e",
        "#2ca02c",
        "#d62728",
        "#9467bd",
    ]

    fig, ax = plt.subplots(figsize=(14, 7))

    for i in range(num_cycles):
        mid_start = halving_blocks[i] - 105_000

        if i < num_cycles - 1:
            mid_end = halving_blocks[i + 1] - 105_000
        else:
            mid_end = blocks[-1] + 1

        mask = (blocks >= mid_start) & (blocks < mid_end)

        cycle_blocks = blocks[mask]
        cycle_prices = prices[mask]

        if len(cycle_prices) == 0:
            continue

        first_price = cycle_prices[0]

        if first_price == 0:
            non_zero = cycle_prices[cycle_prices > 0]
            first_price = non_zero[0] if len(non_zero) > 0 else 1

        price_index = (cycle_prices / first_price) * 100

        ax.plot(
            cycle_blocks,
            price_index,
            label=f"Cycle {i + 1}",
            color=colors[i % len(colors)]
        )

    ax.set_yscale("log")
    ax.set_ylim(10, 300000)

    ax.axhline(
        y=100,
        color="black",
        linestyle="-",
        alpha=0.7
    )

    ax.set_xlabel("Block Index")
    ax.set_ylabel("Price Index (Start = 100%)")

    ax.grid(
        True,
        which="both",
        linestyle="--",
        alpha=0.2
    )

    for b in halving_blocks:
        mid_halving_block = b - 105_000

        ax.axvline(
            x=mid_halving_block,
            color="yellow",
            linestyle="--",
            alpha=0.7,
            linewidth=1.5
        )

        ax.annotate(
            f"Mid-Halving\n{mid_halving_block:,}",
            xy=(mid_halving_block, 150000),
            xytext=(0, 10),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
            color="darkgoldenrod",
            bbox=dict(
                boxstyle="round,pad=0.2",
                facecolor="white",
                alpha=0.8,
                edgecolor="goldenrod"
            )
        )

    ax.legend()
    plt.tight_layout()

    fig.savefig(OUTPUT_FILE, bbox_inches="tight")
    print(f"Saved: {OUTPUT_FILE}")

    plt.show(block=False)

    print("Press SPACE in the figure window to close.")

    def close_all(event):
        if event.key == " ":
            plt.close("all")

    fig.canvas.mpl_connect("key_press_event", close_all)

    while plt.get_fignums():
        plt.pause(0.1)


def main():
    df = fetch_price_data()
    df = load_block_data(df)
    plot_diminishing_returns(df)


if __name__ == "__main__":
    main()