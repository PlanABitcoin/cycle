import os
import shutil
import subprocess
import requests
import numpy as np
import pandas as pd
from datetime import datetime

from bokeh.plotting import figure, output_file, save, show
from bokeh.models import (
    ColumnDataSource, HoverTool, Span, Label, Div,
    Button, CustomJS, PanTool, WheelZoomTool,
    BoxZoomTool, ResetTool, SaveTool,
    NumeralTickFormatter, LogScale, Range1d
)
from bokeh.layouts import column, row


REPO_URL = "https://github.com/PlanABitcoin/cycle.git"

PRICE_URL = (
    "https://api.blockchain.info/charts/market-price?"
    "timespan=18years&rollingAverage=24hours"
    "&start=2010-01-01"
    "&format=json&sampled=false"
)

CSV_FILE = "daily_block_heights.csv"
BLOCKS_PER_CYCLE = 210_000


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


def fetch_price_data():
    print("Downloading Bitcoin price data...")

    r = requests.get(PRICE_URL)
    r.raise_for_status()

    df = pd.DataFrame(r.json()["values"])
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

    df = df.dropna(subset=["Price", "block_number"])

    return df


def build_cycle_sources(df):
    blocks = df["block_number"].values
    prices = df["Price"].values

    halving_blocks = np.arange(
        BLOCKS_PER_CYCLE,
        blocks[-1] + 2 * BLOCKS_PER_CYCLE,
        BLOCKS_PER_CYCLE
    )

    colors = [
        "#1f77b4",
        "#ff7f0e",
        "#2ca02c",
        "#d62728",
        "#9467bd",
        "#8c564b",
    ]

    sources = []

    for i in range(len(halving_blocks)):
        mid_start = halving_blocks[i] - 105_000

        if i < len(halving_blocks) - 1:
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

        price_factor = cycle_prices / first_price

        source = ColumnDataSource(data=dict(
            block=cycle_blocks,
            price_factor=price_factor,
            price=cycle_prices,
            cycle=[f"Cycle {i + 1}"] * len(cycle_blocks),
        ))

        sources.append({
            "source": source,
            "label": f"Cycle {i + 1}",
            "color": colors[i % len(colors)]
        })

    return sources, halving_blocks, blocks[-1]


def make_website(df):
    sources, halving_blocks, last_block = build_cycle_sources(df)

    x_start = 60_000
    x_end = last_block + 50_000

    y_start = 0.1
    y_end = 3000

    pan_tool = PanTool()
    wheel_zoom_tool = WheelZoomTool()
    box_zoom_tool = BoxZoomTool()
    reset_tool = ResetTool()
    save_tool = SaveTool()

    p = figure(
        title="Bitcoin Diminishing Returns Across Cycles",
        height=700,
        sizing_mode="stretch_width",
        tools=[
            pan_tool,
            wheel_zoom_tool,
            box_zoom_tool,
            reset_tool,
            save_tool
        ],
        active_scroll=wheel_zoom_tool,
        active_drag=box_zoom_tool,
        x_range=Range1d(x_start, x_end),
        y_range=Range1d(y_start, y_end),
    )

    p.y_scale = LogScale()
    p.toolbar.logo = None

    p.title.align = "center"
    p.title.text_font_size = "24pt"

    for item in sources:
        p.line(
            "block",
            "price_factor",
            source=item["source"],
            line_color=item["color"],
            line_width=2.5,
            legend_label=item["label"]
        )

    p.line(
        [x_start, x_end],
        [1, 1],
        line_color="black",
        line_width=1.5,
        line_alpha=0.7,
        legend_label="Start = 1x"
    )

    for b in halving_blocks:
        mid_halving_block = b - 105_000

        if mid_halving_block > last_block + 105_000:
            continue

        p.add_layout(Span(
            location=mid_halving_block,
            dimension="height",
            line_color="yellow",
            line_dash="dashed",
            line_width=2,
            line_alpha=0.9
        ))

        p.add_layout(Label(
            x=mid_halving_block,
            y=1250,
            text=f"Mid-Halving\n{mid_halving_block:,}",
            text_font_size="12pt",
            text_color="darkgoldenrod",
            text_align="center",
            background_fill_color="white",
            background_fill_alpha=0.90,
            border_line_color="goldenrod",
            border_line_alpha=0.9,
        ))

    p.xaxis.axis_label = "Block Index"
    p.yaxis.axis_label = "Price Factor (Start = 1x)"

    p.xaxis.axis_label_text_font_size = "22pt"
    p.yaxis.axis_label_text_font_size = "22pt"

    p.xaxis.major_label_text_font_size = "16pt"
    from bokeh.models import NumeralTickFormatter

    # show normal numbers instead of scientific notation
    p.xaxis.formatter = NumeralTickFormatter(
        format="0,0"
    )
    p.yaxis.major_label_text_font_size = "18pt"

    p.xaxis.major_label_text_color = "black"
    p.yaxis.major_label_text_color = "black"

    #p.yaxis.formatter = NumeralTickFormatter(format="0,0.0")
    from bokeh.models import FixedTicker

    # only show selected values
    p.yaxis.ticker = FixedTicker(
        ticks=[
            1,
            2,
            10,
            100,
            1000
        ]
    )

    # no decimals
    p.yaxis.formatter = NumeralTickFormatter(
        format="0"
    )

    p.grid.grid_line_alpha = 0.30
    p.grid.grid_line_color = "#bfbfbf"
    p.grid.grid_line_dash = "dashed"

    p.xaxis.axis_line_width = 2
    p.yaxis.axis_line_width = 2

    p.xaxis.major_tick_line_width = 2
    p.yaxis.major_tick_line_width = 2

    p.xaxis.major_tick_out = 8
    p.yaxis.major_tick_out = 8

    hover = HoverTool(
        tooltips=[
            ("Cycle", "@cycle"),
            ("Block", "@block{0,0}"),
            ("Factor", "@price_factor{0,0.00}x"),
            ("Price", "$@price{0,0}"),
        ],
        mode="mouse",
    )

    p.add_tools(hover)

    p.legend.location = "bottom_left"
    p.legend.background_fill_alpha = 0.85
    p.legend.label_text_font_size = "14pt"
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

    zoom_in_button = Button(
        label="ZOOM +",
        button_type="success",
        css_classes=["big-control-button"]
    )

    zoom_out_button = Button(
        label="ZOOM -",
        button_type="warning",
        css_classes=["big-control-button"]
    )

    box_zoom_button = Button(
        label="BOX ZOOM",
        button_type="primary",
        css_classes=["big-control-button"]
    )

    pan_button = Button(
        label="PAN",
        button_type="primary",
        css_classes=["big-control-button"]
    )

    home_button = Button(
        label="HOME",
        button_type="danger",
        css_classes=["big-control-button"]
    )

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
            x0=x_start,
            x1=x_end,
            y0=y_start,
            y1=y_end,
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
            x0=x_start,
            x1=x_end,
            y0=y_start,
            y1=y_end,
        ),
        code="""
        xr.start = x0;
        xr.end = x1;

        yr.start = y0;
        yr.end = y1;

        xr.change.emit();
        yr.change.emit();
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
        sizing_mode="stretch_width"
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

        <div class="analysis-title">Bitcoin Diminishing Returns</div>

        <div class="analysis-subtitle">
            This figure compares Bitcoin cycles after normalizing each cycle to
            <strong>1x at its mid-halving starting point</strong>.
            It shows that Bitcoin cycles may continue, but the percentage gains
            become smaller as Bitcoin grows.
        </div>

        <div class="analysis-grid">

            <div class="analysis-box">
                <h3>What is shown?</h3>
                <ul>
                    <li>Each colored line is one Bitcoin cycle.</li>
                    <li>The y-axis shows the price factor on a logarithmic scale.</li>
                    <li>1x means the starting price of that cycle.</li>
                    <li>10x means the price became ten times higher.</li>
                    <li>100x means the price became one hundred times higher.</li>
                    <li>Yellow dashed lines mark mid-halving block positions.</li>
                </ul>
            </div>

            <div class="analysis-box">
                <h3>Why normalize?</h3>
                <p>
                    Bitcoin traded at very different price levels in different cycles.
                    Comparing raw prices would hide the structure of the cycles.
                    By dividing each cycle by its starting price, all cycles begin at 1x.
                </p>

                <p>
                    This makes it possible to compare the strength of each cycle directly.
                    The question becomes: how many times did Bitcoin multiply during each cycle?
                </p>
            </div>

            <div class="analysis-box">
                <h3>Main observation</h3>
                <p>
                    Earlier cycles reached much larger multiples than later cycles.
                    In the early years, Bitcoin was small, so a modest inflow of capital
                    could create enormous percentage gains.
                </p>

                <p>
                    As Bitcoin becomes larger, much more capital is required to move the
                    price by the same percentage. Therefore, the cycle structure may remain,
                    but the size of the gains tends to decrease.
                </p>
            </div>

        </div>

        <div class="analysis-grid" style="margin-top: 24px;">

            <div class="analysis-box">
                <h3>Connection to the Bitcoin cycle</h3>
                <p>
                    The halving reduces the flow of newly created Bitcoin. If demand remains
                    strong, this reduction in new supply can support a long upward phase.
                </p>

                <p>
                    However, each new cycle begins from a larger market size. Therefore,
                    even if the halving effect remains important, the same supply shock
                    tends to produce smaller percentage gains over time.
                </p>
            </div>

            <div class="analysis-box">
                <h3>Why the rise slows</h3>
                <p>
                    A move from $1,000 to $10,000 requires far less new capital than a move
                    from $100,000 to $1,000,000. Both are 10x moves, but the second requires
                    a much larger amount of money entering the market.
                </p>

                <p>
                    This is the key idea behind diminishing returns: as Bitcoin matures,
                    the same relative growth becomes harder to achieve.
                </p>
            </div>

            <div class="analysis-box">
                <h3>Why corrections still happen</h3>
                <p>
                    When Bitcoin price rises strongly, mining becomes more profitable.
                    This attracts more miners and increases spending on electricity,
                    hardware, cooling and infrastructure.
                </p>

                <p>
                    At very high prices, total mining costs can become extremely large.
                    If these costs become difficult to sustain, they can contribute to
                    the end of the upward phase and the beginning of a correction.
                </p>
            </div>

        </div>

        <div class="footer-note">
            <strong>Main takeaway:</strong>
            Bitcoin cycles appear to repeat, but their amplitude declines over time.
            The figure suggests that future cycles may still produce new highs,
            but the percentage gains are likely to be smaller than in earlier cycles.
            This is the idea of diminishing returns.
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

    output_file("index.html", title="Bitcoin Diminishing Returns")
    save(layout)

    output_file("figures/f_dem1.html", title="Bitcoin Diminishing Returns")
    save(layout)

    print("Saved index.html")
    print("Saved figures/f_dem1.html")

    show(layout)


def git_push():
    from github_publish import publish_to_github

    publish_to_github(
        add_paths=["index.html", "figures/f_dem1.html"],
        message=f"update diminishing returns website {datetime.now()}",
        log_file="run_log.txt",
    )


def main():
    df = fetch_price_data()
    df = load_block_data(df)

    make_website(df)
    if os.environ.get("SKIP_GITHUB_PUSH") == "1":
        print("Skipping per-script GitHub push; runner will publish once at the end.")
    else:
        git_push()

    print("DONE")


if __name__ == "__main__":
    main()
