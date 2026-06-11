import pandas as pd
import numpy as np
import requests
import json
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
from datetime import datetime
import os

plt.close("all")

# ============================================================
# CONFIG
# ============================================================

BLOCKS_PER_CYCLE = 210000

PRICE_URL = (
    "https://api.blockchain.info/charts/market-price?"
    "timespan=18years"
    "&rollingAverage=24hours"
    "&start=2010-01-01"
    "&format=json"
    "&sampled=false"
)

CSV_FILE = "daily_block_heights.csv"

COLORS = [
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd"
]

# ============================================================
# DOWNLOAD BTC PRICE
# ============================================================

def fetch_price():

    print("Downloading Bitcoin price...")

    r = requests.get(PRICE_URL)

    data = json.loads(r.content)

    df = pd.DataFrame(data["values"])

    df["Date"] = pd.to_datetime(
        df["x"],
        unit="s",
        utc=True
    )

    df["Price"] = df["y"]

    df = df[["Date", "Price"]]

    df.set_index("Date", inplace=True)

    df = df.resample("D").last()

    df = df.tz_localize(None)

    return df


# ============================================================
# LOAD BLOCK NUMBERS
# ============================================================

def add_blocks(df):

    if not os.path.exists(CSV_FILE):

        raise FileNotFoundError(CSV_FILE)

    blocks = pd.read_csv(
        CSV_FILE,
        parse_dates=["date"]
    )

    blocks.set_index(
        "date",
        inplace=True
    )

    blocks = blocks.reindex(
        pd.date_range(
            df.index.min(),
            df.index.max(),
            freq="D"
        )
    )

    blocks["block_number"] = blocks["block"]

    missing = blocks["block"].isna()

    if missing.any():

        last_idx = blocks["block"].last_valid_index()

        last_val = blocks.loc[
            last_idx,
            "block"
        ]

        count = missing.sum()

        blocks.loc[
            missing,
            "block_number"
        ] = (
            last_val
            +
            np.arange(
                1,
                count + 1
            ) * 144
        )

    blocks["block_number"] = (
        blocks["block_number"]
        .astype(int)
    )

    df = df.merge(
        blocks[
            ["block_number"]
        ],
        left_index=True,
        right_index=True,
        how="left"
    )

    return df


# ============================================================
# CREATE F_DEM2
# ============================================================

def create_f_dem2(df):

    blocks = df["block_number"].values
    prices = df["Price"].values

    # include partial cycle 5
    halving_blocks = np.arange(
        BLOCKS_PER_CYCLE,
        blocks[-1] + 2 * BLOCKS_PER_CYCLE,
        BLOCKS_PER_CYCLE
    )

    fig, ax = plt.subplots(
        figsize=(15, 8)
    )

    cycle_counter = 0

    for i in range(len(halving_blocks)):

        start = halving_blocks[i] - 105000

        if i < len(halving_blocks) - 1:
            end = halving_blocks[i + 1] - 105000
        else:
            end = blocks[-1] + 1

        mask = (
            (blocks >= start)
            &
            (blocks < end)
        )

        cycle_blocks = blocks[mask]
        cycle_prices = prices[mask]

        if len(cycle_prices) == 0:
            continue

        cycle_counter += 1

        first = cycle_prices[0]

        factor = (
            cycle_prices
            /
            first
        )

        relative = (
            cycle_blocks
            -
            start
        )

        ax.plot(
            relative,
            factor,
            color=COLORS[i % len(COLORS)],
            linewidth=3,
            alpha=0.75,
            label=f"Cycle {cycle_counter}"
        )

        # ------------------------------------------------
        # Skip max/min for partial cycle (cycle 5)
        # ------------------------------------------------

        if cycle_counter < 5:

            max_idx = factor.argmax()

            max_x = relative[max_idx]
            max_y = factor[max_idx]

            ax.scatter(
                max_x,
                max_y,
                s=140,
                marker="x",
                color=COLORS[i]
            )

            ax.axvline(
                max_x,
                linestyle=":",
                color=COLORS[i],
                alpha=0.7
            )

            # offsets for max labels
            max_label_offsets = {
                1: (-15000, 1.22),
                2: (16000, 1.18),
                3: (-16000, 1.18),
                4: (18000, 1.20),
            }

            dx, y_factor = max_label_offsets.get(
                cycle_counter,
                (15000, 1.18)
            )

            ax.annotate(
                f"Max {cycle_counter}",

                xy=(max_x, max_y),

                xytext=(
                    max_x + dx,
                    max_y * y_factor
                ),

                fontsize=12,
                fontweight="bold",

                color=COLORS[i],

                ha="center",

                arrowprops=dict(
                    arrowstyle="-|>",
                    color=COLORS[i],
                    lw=1.6,
                    shrinkA=5,
                    shrinkB=4
                )
            )

            if cycle_counter > 1:

                min_idx = factor.argmin()

                min_x = relative[min_idx]
                min_y = factor[min_idx]

                ax.scatter(
                    min_x,
                    min_y,
                    s=120,
                    marker="o",
                    color=COLORS[i]
                )

                ax.axvline(
                    min_x,
                    linestyle="--",
                    color=COLORS[i],
                    alpha=0.5
                )

                # Manual offsets to avoid overlap
                min_label_offsets = {
                    2: (-18000, 0.65),
                    3: (-14000, 0.75),
                    4: (16000, 0.70),
                }

                dx, y_factor = min_label_offsets.get(
                    cycle_counter,
                    (12000, 0.75)
                )

                ax.annotate(
                    f"Min {cycle_counter}",
                    xy=(min_x, min_y),
                    xytext=(min_x + dx, min_y * y_factor),
                    fontsize=12,
                    fontweight="bold",
                    color=COLORS[i],
                    ha="center",
                    arrowprops=dict(
                        arrowstyle="->",
                        color=COLORS[i],
                        lw=1.2
                    )
                )
    ax.set_yscale("log")

    ax.set_xlim(
        0,
        210000
    )

    ax.set_ylim(
        0.1,
        3000
    )

    ax.axhline(
        1,
        color="black"
    )

    ax.axvline(
        105000,
        color="gray",
        linewidth=2
    )

    ax.text(
        105000,
        2500,
        "Halving",
        ha="center"
    )

    ax.set_xlabel(
        "Blocks Since Mid-Halving Start",
        fontsize=18
    )

    ax.set_ylabel(
        "Price Factor (Start = 1×)",
        fontsize=18
    )

    ax.set_yticks([
        0.1,
        1,
        2,
        10,
        100,
        1000
    ])

    from matplotlib.ticker import FuncFormatter

    ax.yaxis.set_major_formatter(
        FuncFormatter(
            lambda x, _: (
                "0.1"
                if x == 0.1
                else f"{int(x)}"
            )
        )
    )

    ax.grid(
        True,
        which="both",
        linestyle="--",
        alpha=0.2
    )

    ax.legend()

    plt.tight_layout()

    # plt.savefig(
    #     "f_dem2.pdf",
    #     bbox_inches="tight"
    # )

    plt.show()

#    print("Saved f_dem2.pdf")

# ============================================================

def main():

    df = fetch_price()

    df = add_blocks(df)

    create_f_dem2(df)


if __name__ == "__main__":

    main()