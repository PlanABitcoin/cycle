import os
import json
import requests
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("TkAgg")

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns


# =========================
# PARAMETERS
# =========================

PRICE_URL = (
    "https://api.blockchain.info/charts/market-price?"
    "timespan=18years"
    "&rollingAverage=24hours"
    "&start=2010-01-01"
    "&format=json"
    "&sampled=false"
)

CSV_FILE = "daily_block_heights.csv"
BLOCKS_PER_CYCLE = 210_000
SEGMENTS = 8
OUTPUT_FILE = "f_seg.pdf"


# =========================
# LOAD PRICE DATA
# =========================

def fetch_price_data():
    print("Downloading Bitcoin price data...")

    response = requests.get(PRICE_URL)
    data = json.loads(response.content).get("values", [])

    df = pd.DataFrame(data)
    df["Date"] = pd.to_datetime(df["x"], unit="s", utc=True)
    df["Price"] = df["y"]

    df = df[["Date", "Price"]]
    df.set_index("Date", inplace=True)
    df = df.resample("D").last()
    df = df.tz_localize(None)

    return df


# =========================
# LOAD BLOCK DATA
# =========================

def load_block_data(df):
    if not os.path.exists(CSV_FILE):
        raise FileNotFoundError(f"{CSV_FILE} not found.")

    df_blocks = pd.read_csv(CSV_FILE, parse_dates=["date"])
    df_blocks.set_index("date", inplace=True)

    if "block" not in df_blocks.columns:
        raise ValueError("CSV must contain a column named 'block'.")

    full_index = pd.date_range(df.index.min(), df.index.max(), freq="D")
    df_blocks = df_blocks.reindex(full_index)

    df_blocks["block_number"] = df_blocks["block"]

    missing_mask = df_blocks["block_number"].isna()

    if missing_mask.any():
        last_valid_idx = df_blocks["block_number"].last_valid_index()
        last_known_value = df_blocks.loc[last_valid_idx, "block_number"]

        missing_dates = df_blocks.index[missing_mask]

        for i, date in enumerate(missing_dates, start=1):
            df_blocks.loc[date, "block_number"] = last_known_value + 144 * i

    df_blocks["block_number"] = df_blocks["block_number"].astype(int)

    df = df.merge(
        df_blocks[["block_number"]],
        left_index=True,
        right_index=True,
        how="left"
    )

    return df


# =========================
# CREATE HEATMAP
# =========================

def create_heatmap(df):
    df = df.copy().sort_values("block_number")

    df["cycle"] = df["block_number"] // BLOCKS_PER_CYCLE
    df["block_in_cycle"] = df["block_number"] % BLOCKS_PER_CYCLE

    current_block_val = df["block_in_cycle"].iloc[-1]

    # Remove cycle 0
    df = df[df["cycle"] > 0].copy()

    blocks_per_segment = BLOCKS_PER_CYCLE // SEGMENTS

    df["segment"] = (
        df["block_in_cycle"] // blocks_per_segment
    ).clip(upper=SEGMENTS - 1)

    returns = df.groupby(["cycle", "segment"]).agg(
        first_price=("Price", "first"),
        last_price=("Price", "last")
    )

    returns["yield_pct"] = (
        returns["last_price"] / returns["first_price"] - 1
    ) * 100

    table = returns["yield_pct"].unstack("segment").fillna(0)
    table.columns = [f"S{i + 1}" for i in range(SEGMENTS)]

    cycle_labels = []

    for cyc in table.index:
        start_b = cyc * BLOCKS_PER_CYCLE

        if cyc == df["cycle"].max():
            end_b = df[df["cycle"] == cyc]["block_number"].max()
        else:
            end_b = (cyc + 1) * BLOCKS_PER_CYCLE - 1

        cycle_labels.append(
            f"Cycle {cyc} ({start_b // 1000}K–{end_b // 1000}K)"
        )

    table.index = cycle_labels

    annot_labels = table.map(
        lambda x: f"+{x:.1f}" if x > 0 else f"{x:.1f}"
    )

    custom_cmap = mcolors.LinearSegmentedColormap.from_list(
        "",
        [
            (0.00, "#d73027"),
            (0.49, "#f4cccc"),
            (0.498, "#ffffff"),
            (0.502, "#ffffff"),
            (0.51, "#d9ead3"),
            (1.00, "#1a9850"),
        ]
    )

    plt.figure(figsize=(16, 6))

    ax = sns.heatmap(
        table,
        annot=annot_labels,
        fmt="",
        cmap=custom_cmap,
        center=0,
        vmin=-100,
        vmax=100,
        linewidths=0.7,
        linecolor="white"
    )

    exact_x_pos = current_block_val / blocks_per_segment
    num_rows = len(table)

    ax.annotate(
        "",
        xy=(exact_x_pos, num_rows),
        xytext=(exact_x_pos, num_rows - 0.12),
        arrowprops=dict(
            arrowstyle="->",
            color="black",
            lw=1.5
        )
    )

    ax.text(
        exact_x_pos,
        num_rows - 0.15,
        f"{current_block_val:,}",
        ha="center",
        va="bottom",
        fontsize=8,
        fontweight="bold",
        bbox=dict(
            facecolor="white",
            alpha=0.7,
            edgecolor="none",
            pad=0.05
        )
    )

    plt.xlabel(f"Segments ({blocks_per_segment:,} blocks each)")
    plt.ylabel("Cycle Range")
    plt.tight_layout()

    plt.savefig(OUTPUT_FILE, bbox_inches="tight")
    plt.show(block=False)

    print(f"Saved: {OUTPUT_FILE}")


# =========================
# WAIT FOR SPACE
# =========================

def wait_until_space():
    print("\nFigure generated.")
    print("Press SPACE in the figure window to close it.")

    def close_all(event):
        if event.key == " ":
            plt.close("all")

    for num in plt.get_fignums():
        fig = plt.figure(num)
        fig.canvas.mpl_connect("key_press_event", close_all)

    while plt.get_fignums():
        plt.pause(0.1)


# =========================
# MAIN
# =========================

df = fetch_price_data()
df = load_block_data(df)
create_heatmap(df)
wait_until_space()

#exit()
