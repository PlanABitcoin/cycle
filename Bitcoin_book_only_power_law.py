import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
import requests
import json

plt.close("all")

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

    df = df[df["Price"] > 0].copy()

    return df


def create_power_law_figure(df):
    genesis_date = pd.Timestamp("2009-01-03")

    plot_start = pd.Timestamp("2012-06-01")
    plot_end = pd.Timestamp("2032-12-31")

    df_power = df.copy()
    df_power["days_since_genesis"] = (
        df_power.index - genesis_date
    ).days

    df_power = df_power[
        df_power["days_since_genesis"] > 0
    ].copy()

    df_power = df_power[
        df_power.index >= plot_start
    ].copy()

    X = np.log10(
        df_power["days_since_genesis"].values
    )

    y = np.log10(
        df_power["Price"].values
    )

    slope, intercept = np.polyfit(X, y, 1)

    future_dates = pd.date_range(
        start=plot_start,
        end=plot_end,
        freq="D"
    )

    future_days = (
        future_dates - genesis_date
    ).days.values

    future_powerlaw = 10 ** (
        slope * np.log10(future_days)
        + intercept
    )

    upper_band = future_powerlaw * 2
    lower_band = future_powerlaw / 2

    plt.figure(figsize=(13, 8))

    plt.plot(
        df_power.index,
        df_power["Price"],
        label="Bitcoin Price",
        linewidth=2
    )

    plt.plot(
        future_dates,
        future_powerlaw,
        label="Power Law Fit",
        linewidth=2
    )

    plt.plot(
        future_dates,
        upper_band,
        linestyle="--",
        label="Upper Band ×2",
        linewidth=1.5
    )

    plt.plot(
        future_dates,
        lower_band,
        linestyle="--",
        label="Lower Band ÷2",
        linewidth=1.5
    )

    plt.yscale("log")
    plt.xlim(plot_start, plot_end)
    plt.ylim(1, 10_000_000)

    ax = plt.gca()
    ax.yaxis.set_major_formatter(
        ScalarFormatter(useOffset=False)
    )
    ax.ticklabel_format(style="plain", axis="y")

    plt.xlabel("Date")
    plt.ylabel("USD")
    plt.grid(True, which="both", linestyle="--", alpha=0.25)
    plt.legend(loc="upper left")

    plt.title(
        f"Bitcoin Power Law Model\n"
        f"log10(price) = {slope:.3f} log10(days) {intercept:.3f}"
    )

    plt.tight_layout()

    # plt.savefig(
    #     "f_powerlaw.pdf",
    #     bbox_inches="tight"
    # )

    plt.show(block=False)

    # print("Saved f_powerlaw.pdf")


def main():
    df = fetch_price()
    create_power_law_figure(df)


if __name__ == "__main__":
    main()