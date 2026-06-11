#good
import os
import math
import shutil
import subprocess
import requests
import pandas as pd
from datetime import datetime

from bokeh.plotting import figure, output_file, save, show
from bokeh.models import (
    ColumnDataSource, HoverTool, Span, Label, Div,
    Button, CustomJS, PanTool, WheelZoomTool, BoxZoomTool,
    ResetTool, SaveTool, NumeralTickFormatter,
    LinearAxis, Range1d, LogScale, LinearScale,
    FixedTicker
)
from bokeh.layouts import column, row


REPO_URL = "https://github.com/PlanABitcoin/cycle.git"

BLUE = "#1f77b4"
RED = "#d62728"
GREEN = "#2ca02c"
ORANGE = "#ff7f0e"
OLIVE = "#bcbd22"

HALVINGS = [
    datetime(2012, 11, 28),
    datetime(2016, 7, 9),
    datetime(2020, 5, 11),
    datetime(2024, 4, 19),
    datetime(2028, 3, 31),
]

URLS = {
    "Price": "https://api.blockchain.info/charts/market-price?timespan=18years&rollingAverage=24hours&start=2010-01-01&format=json&sampled=false",
    "fees": "https://api.blockchain.info/charts/transaction-fees?timespan=18years&rollingAverage=24hours&start=2010-01-01&format=json&sampled=false",
}


def find_git():
    git_path = shutil.which("git")
    if git_path:
        return git_path

    for p in [
        r"C:\Program Files\Git\cmd\git.exe",
        r"C:\Program Files\Git\bin\git.exe",
        r"C:\Program Files (x86)\Git\cmd\git.exe",
        r"C:\Program Files (x86)\Git\bin\git.exe",
    ]:
        if os.path.exists(p):
            return p

    raise FileNotFoundError("Git not found")


GIT = find_git()


def run(cmd):
    print(" ".join(cmd))
    return subprocess.run(cmd, check=True)


def download_series(name, url):
    print(f"Downloading {name}...")
    r = requests.get(url)
    r.raise_for_status()

    df = pd.DataFrame(r.json()["values"])
    df["Date"] = pd.to_datetime(df["x"], unit="s", utc=True)
    df = df.rename(columns={"y": name})
    df = df.set_index("Date")[[name]]
    df = df.resample("D").last()
    df = df.tz_localize(None)

    return df


def btc_reward(date):
    reward = 50.0
    for h in HALVINGS:
        if date >= h:
            reward /= 2
    return reward


def load_data():
    df = None

    for name, url in URLS.items():
        s = download_series(name, url)
        df = s if df is None else df.join(s, how="left")

    df["fees"] = df["fees"].fillna(0)
    df["Reward"] = df.index.map(btc_reward)

    df["Mining cost"] = df["Price"] * df["Reward"] * 6 * 24 * 365 / 1_000_000_000
    df["Fees cost"] = df["fees"] * df["Price"] * 365 / 1_000_000_000
    df["Total cost"] = df["Mining cost"] + df["Fees cost"]

    df["Total cost MA 90"] = df["Total cost"].rolling(90).mean()
    df["Total cost MA 365"] = df["Total cost"].rolling(365).mean()
    df["Total cost MA 730"] = df["Total cost"].rolling(730).mean()

    df = df[df["Price"] > 0].copy()
    return df


def make_website(df):
    source = ColumnDataSource(data=dict(
        Date=df.index,
        Price=df["Price"],
        TotalCost=df["Total cost"],
        MA90=df["Total cost MA 90"],
        MA365=df["Total cost MA 365"],
        MA730=df["Total cost MA 730"],
    ))

    x_start = datetime(2010, 1, 1)
    x_end = datetime(2028, 6, 1)

    price_y_start = 0.1
    price_y_end = 250000

    cost_y_start = 0
    cost_y_end = 45

    pan_tool = PanTool()
    wheel_zoom_tool = WheelZoomTool()
    box_zoom_tool = BoxZoomTool()
    reset_tool = ResetTool()
    save_tool = SaveTool()

    p = figure(
        title="Bitcoin Price and Mining Cost",
        x_axis_type="datetime",
        height=700,
        sizing_mode="stretch_width",
        tools=[pan_tool, wheel_zoom_tool, box_zoom_tool, reset_tool, save_tool],
        active_scroll=wheel_zoom_tool,
        active_drag=box_zoom_tool,
        x_range=(x_start, x_end),
        y_range=Range1d(price_y_start, price_y_end),
    )

    p.y_scale = LogScale()

    p.extra_y_ranges = {
        "cost_axis": Range1d(start=cost_y_start, end=cost_y_end)
    }

    p.extra_y_scales = {
        "cost_axis": LinearScale()
    }

    p.toolbar.logo = None
    p.toolbar_location = None
    p.title.align = "center"
    p.title.text_font_size = "24pt"

    p.yaxis.axis_label = "Price (log scale)"
    p.yaxis.axis_label_text_color = BLUE
    p.yaxis.major_label_text_color = BLUE
    p.yaxis.axis_label_text_font_size = "18pt"
    p.yaxis.major_label_text_font_size = "14pt"
    p.xaxis.major_label_text_font_size = "14pt"
    p.yaxis.formatter = NumeralTickFormatter(format="0,0")
    p.yaxis.ticker = FixedTicker(ticks=[
        0.1,
        1,
        10,
        100,
        1000,
        10000,
        100000,
        250000,
    ])

    p.grid.grid_line_alpha = 0.45
    p.grid.grid_line_color = "gray"

    p.line("Date", "Price", source=source, line_color=BLUE, line_width=2,
           legend_label="Price")

    p.add_layout(
        LinearAxis(
            y_range_name="cost_axis",
            axis_label="total_cost (fee+reward)",
            axis_label_text_color=RED,
            major_label_text_color=RED,
            axis_label_text_font_size="18pt",
            major_label_text_font_size="14pt",
        ),
        "right",
    )

    p.line("Date", "TotalCost", source=source, y_range_name="cost_axis",
           line_color=RED, line_width=2,
           legend_label="Mining total cost (fee+reward)")

    p.line("Date", "MA365", source=source, y_range_name="cost_axis",
           line_color=GREEN, line_width=2,
           legend_label="Mining total cost MA 365")

    p.line("Date", "MA730", source=source, y_range_name="cost_axis",
           line_color=ORANGE, line_width=2,
           legend_label="Mining total cost MA 730")

    p.line("Date", "MA90", source=source, y_range_name="cost_axis",
           line_color=OLIVE, line_width=2,
           legend_label="Mining total cost MA 90")

    for i, h in enumerate(HALVINGS, 1):
        p.add_layout(Span(location=h, dimension="height",
                          line_color=RED, line_width=2, line_alpha=0.65))

        p.add_layout(Label(
            x=h, y=0.12, text=f"Halving {i}",
            angle=math.pi / 2,
            text_font_size="13pt",
            text_color="black",
        ))

        if i < len(HALVINGS):
            mid = h + (HALVINGS[i] - h) / 2
            p.add_layout(Span(location=mid, dimension="height",
                              line_color=RED, line_dash="dashed",
                              line_width=2, line_alpha=0.55))

    hover = HoverTool(
        tooltips=[
            ("Date", "@Date{%F}"),
            ("Price", "$@Price{0,0}"),
            ("Total cost", "@TotalCost{0.00} B USD"),
            ("MA 90", "@MA90{0.00} B USD"),
            ("MA 365", "@MA365{0.00} B USD"),
            ("MA 730", "@MA730{0.00} B USD"),
        ],
        formatters={"@Date": "datetime"},
        mode="vline",
    )
    p.add_tools(hover)

    p.legend.location = "top_left"
    p.legend.label_text_font_size = "13pt"
    p.legend.background_fill_alpha = 0.75
    p.legend.click_policy = "hide"

    button_style = Div(text="""
    <style>
    .big-control-button button {
        width: 220px !important;
        height: 115px !important;
        border-radius: 18px !important;
        margin: 6px !important;
        font-size: 34px !important;
        font-weight: bold !important;
    }

    @media (max-width: 700px) {
        .big-control-button button {
            width: 160px !important;
            height: 95px !important;
            font-size: 25px !important;
        }
    }
    </style>
    """, sizing_mode="stretch_width")

    zoom_in_button = Button(label="ZOOM +", button_type="success",
                            css_classes=["big-control-button"])
    zoom_out_button = Button(label="ZOOM −", button_type="warning",
                             css_classes=["big-control-button"])
    box_zoom_button = Button(label="BOX ZOOM", button_type="primary",
                             css_classes=["big-control-button"])
    pan_button = Button(label="PAN", button_type="primary",
                        css_classes=["big-control-button"])
    home_button = Button(label="HOME", button_type="danger",
                         css_classes=["big-control-button"])

    zoom_in_button.js_on_click(CustomJS(
        args=dict(xr=p.x_range, yr=p.y_range),
        code="""
        const factor = 0.70;

        const xmid = (xr.start + xr.end) / 2.0;
        const xrange = (xr.end - xr.start) * factor;
        xr.start = xmid - xrange / 2.0;
        xr.end = xmid + xrange / 2.0;

        const log_start = Math.log10(yr.start);
        const log_end = Math.log10(yr.end);
        const log_mid = (log_start + log_end) / 2.0;
        const log_range = (log_end - log_start) * factor;

        yr.start = Math.pow(10, log_mid - log_range / 2.0);
        yr.end = Math.pow(10, log_mid + log_range / 2.0);

        xr.change.emit();
        yr.change.emit();
        """
    ))

    zoom_out_button.js_on_click(CustomJS(
        args=dict(
            xr=p.x_range,
            yr=p.y_range,
            x0=x_start.timestamp() * 1000,
            x1=x_end.timestamp() * 1000,
            y0=price_y_start,
            y1=price_y_end,
        ),
        code="""
        const factor = 1.40;

        const xmid = (xr.start + xr.end) / 2.0;
        const xrange = (xr.end - xr.start) * factor;
        xr.start = xmid - xrange / 2.0;
        xr.end = xmid + xrange / 2.0;

        const log_start = Math.log10(yr.start);
        const log_end = Math.log10(yr.end);
        const log_mid = (log_start + log_end) / 2.0;
        const log_range = (log_end - log_start) * factor;

        yr.start = Math.pow(10, log_mid - log_range / 2.0);
        yr.end = Math.pow(10, log_mid + log_range / 2.0);

        if (xr.start < x0) xr.start = x0;
        if (xr.end > x1) xr.end = x1;
        if (yr.start < y0) yr.start = y0;
        if (yr.end > y1) yr.end = y1;

        xr.change.emit();
        yr.change.emit();
        """
    ))

    box_zoom_button.js_on_click(CustomJS(
        args=dict(plot=p, box_zoom_tool=box_zoom_tool),
        code="plot.toolbar.active_drag = box_zoom_tool;"
    ))

    pan_button.js_on_click(CustomJS(
        args=dict(plot=p, pan_tool=pan_tool),
        code="plot.toolbar.active_drag = pan_tool;"
    ))

    home_button.js_on_click(CustomJS(
        args=dict(
            xr=p.x_range,
            yr=p.y_range,
            cr=p.extra_y_ranges["cost_axis"],
            x0=x_start.timestamp() * 1000,
            x1=x_end.timestamp() * 1000,
            y0=price_y_start,
            y1=price_y_end,
            c0=cost_y_start,
            c1=cost_y_end,
        ),
        code="""
        xr.start = x0;
        xr.end = x1;

        yr.start = y0;
        yr.end = y1;

        cr.start = c0;
        cr.end = c1;

        xr.change.emit();
        yr.change.emit();
        cr.change.emit();
        """
    ))

    controls = column(
        button_style,
        row(
            zoom_in_button,
            zoom_out_button,
            box_zoom_button,
            pan_button,
            home_button,
            sizing_mode="stretch_width",
        ),
        sizing_mode="stretch_width",
    )

    explanation = Div(text="""
<style>
.analysis-wrapper {
    width: 96%;
    box-sizing: border-box;
    margin: 35px auto 50px auto;
    background: linear-gradient(135deg, #081224 0%, #0b132b 45%, #111827 100%);
    border-radius: 22px;
    padding: 28px;
    color: white;
    box-shadow: 0 10px 35px rgba(0,0,0,0.30);
}

.analysis-title {
    text-align: center;
    font-size: 42px;
    font-weight: 700;
    margin-bottom: 20px;
}

.analysis-subtitle {
    text-align: center;
    font-size: 22px;
    line-height: 1.7;
    color: #d1d5db;
    margin-bottom: 28px;
}

.analysis-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 28px;
    border-top: 1px solid rgba(255,255,255,0.15);
    padding-top: 28px;
}

.analysis-box {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 24px;
}

.analysis-box h3 {
    margin-top: 0;
    font-size: 28px;
    color: #38bdf8;
}

.analysis-box ul,
.analysis-box p {
    line-height: 1.9;
    font-size: 18px;
    color: #e5e7eb;
}

.footer-note {
    margin-top: 28px;
    padding-top: 18px;
    border-top: 1px solid rgba(255,255,255,0.15);
    text-align: center;
    font-size: 15px;
    color: #cbd5e1;
    line-height: 1.8;
}

.footer-note strong {
    color: #facc15;
}

@media (max-width: 900px) {
    .analysis-wrapper {
        width: 100%;
        padding: 18px;
        border-radius: 16px;
    }

    .analysis-title {
        font-size: 30px;
    }

    .analysis-subtitle {
        font-size: 17px;
    }

    .analysis-grid {
        grid-template-columns: 1fr;
        gap: 18px;
    }

    .analysis-box h3 {
        font-size: 24px;
    }

    .analysis-box ul,
    .analysis-box p {
        font-size: 16px;
    }
}
</style>

<div class="analysis-wrapper">

    <div class="analysis-title">⚡ Bitcoin Price and Mining Cost</div>

    <div class="analysis-subtitle">
        This figure illustrates the relationship between Bitcoin price and the
        economic cost of securing the Bitcoin network.
    </div>

    <div class="analysis-grid">

        <div class="analysis-box">
            <h3>📊 What is shown?</h3>
            <ul>
                <li><span style="color:#60a5fa;">Blue</span>: Bitcoin price on a logarithmic scale.</li>
                <li><span style="color:#ef4444;">Red</span>: estimated annual miner revenue from block rewards and transaction fees.</li>
                <li><span style="color:#d4d400;">Olive</span>: 90 day moving average of mining cost.</li>
                <li><span style="color:#22c55e;">Green</span>: 365 day moving average of mining cost.</li>
                <li><span style="color:#f97316;">Orange</span>: 730 day moving average of mining cost.</li>
            </ul>
        </div>

        <div class="analysis-box">
            <h3>⚙ Why does mining cost follow price?</h3>
            <p>
                When Bitcoin price rises, miners receive more dollars for each block
                they produce. Higher profitability attracts additional miners and
                increases spending on hardware, electricity, cooling and infrastructure.
            </p>
            <p>
                As competition increases, total mining expenditure rises. Over long
                periods, mining cost therefore tends to move together with Bitcoin price.
            </p>
        </div>

                      
        <div class="analysis-box">
            <h3>🔁 Connection to the Bitcoin Cycle</h3>

            <p>
            The Bitcoin cycle can be viewed as the interaction between two opposing forces.
            The first force is the halving mechanism, which reduces the flow of newly
            created Bitcoin and tends to create a multi-year upward phase. The second
            force is the increasing cost of mining, which grows together with Bitcoin price.
            </p>

            <p>
            After each halving, the supply of new Bitcoin entering the market is cut in
            half. If demand remains relatively stable, this reduction in supply creates
            upward pressure on price. Historically, this has been associated with an
            upward phase lasting roughly three years.
            </p>

            <p>
            As Bitcoin price rises, miner revenue rises as well. This attracts additional
            miners, increases competition, and causes total spending on hardware,
            electricity, cooling and infrastructure to grow. Consequently, mining cost
            tends to increase together with Bitcoin price.
            </p>
        </div>


    </div>

    <div class="footer-note">
        <strong>Main observation:</strong>
        Bitcoin price and mining cost are strongly connected over long time horizons.
        As price reaches extreme levels, total mining cost can grow to tens of billions
        of dollars per year. Such levels may become difficult to sustain indefinitely,
        often coinciding with the end of an upward phase and the beginning of a correction.
        This provides a possible economic mechanism linking halvings, miner behavior
        and the recurring Bitcoin cycle.
        <br><br>
        This chart is for educational purposes only and is not financial advice.
    </div>

</div>
""", sizing_mode="stretch_width")

    page_style = Div(text="""
    <style>
    body {
        margin: 0;
        background: white;
        font-family: Arial, sans-serif;
    }

    @media (min-width: 901px) {
        .main-page {
            width: 100% !important;
            max-width: 100% !important;
        }

        .bk-plot-layout {
            max-width: 1250px !important;
            width: 92% !important;
            margin-left: auto !important;
            margin-right: auto !important;
        }
    }

    @media (max-width: 900px) {
        .main-page {
            width: 100% !important;
            max-width: 100% !important;
        }
    }
    </style>
    """, sizing_mode="stretch_width")

    layout = column(
        page_style,
        controls,
        p,
        explanation,
        sizing_mode="stretch_width",
        css_classes=["main-page"],
    )

    os.makedirs("figures", exist_ok=True)

    output_file("index.html", title="Bitcoin Price and Mining Cost")
    save(layout)

    output_file("figures/f_mining_cost.html", title="Bitcoin Price and Mining Cost")
    save(layout)

    print("Saved index.html")
    print("Saved figures/f_mining_cost.html")

    show(layout)


def git_push():
    from github_publish import publish_to_github

    publish_to_github(
        add_paths=["index.html", "figures/f_mining_cost.html"],
        message=f"update mining cost website {datetime.now()}",
        log_file="run_log.txt",
    )


def main():
    df = load_data()
    make_website(df)
    if os.environ.get("SKIP_GITHUB_PUSH") == "1":
        print("Skipping per-script GitHub push; runner will publish once at the end.")
    else:
        git_push()
    print("DONE")


if __name__ == "__main__":
    main()
