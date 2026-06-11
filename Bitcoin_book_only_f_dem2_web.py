# f_dem2_website_git.py

import os
import shutil
import subprocess
import requests
import numpy as np
import pandas as pd
from datetime import datetime

from bokeh.plotting import figure, output_file, save, show
from bokeh.models import (
    ColumnDataSource, HoverTool, Span, Label,
    Button, CustomJS, PanTool, WheelZoomTool,
    BoxZoomTool, ResetTool, SaveTool,
    Div, Range1d, LogScale,
    NumeralTickFormatter, FixedTicker
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

COLORS = [
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
]


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


def fetch_price():
    print("Downloading Bitcoin price...")

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


def add_blocks(df):
    if not os.path.exists(CSV_FILE):
        raise FileNotFoundError(CSV_FILE)

    blocks = pd.read_csv(CSV_FILE, parse_dates=["date"])
    blocks.set_index("date", inplace=True)

    blocks = blocks.reindex(
        pd.date_range(df.index.min(), df.index.max(), freq="D")
    )

    blocks["block_number"] = blocks["block"]

    missing = blocks["block_number"].isna()

    if missing.any():
        last_idx = blocks["block_number"].last_valid_index()
        last_val = blocks.loc[last_idx, "block_number"]

        blocks.loc[missing, "block_number"] = (
            last_val + np.arange(1, missing.sum() + 1) * 144
        )

    blocks["block_number"] = blocks["block_number"].astype(int)

    df = df.merge(
        blocks[["block_number"]],
        left_index=True,
        right_index=True,
        how="left"
    )

    return df.dropna()


def build_sources(df):
    blocks = df["block_number"].values
    prices = df["Price"].values

    halving_blocks = np.arange(
        BLOCKS_PER_CYCLE,
        blocks[-1] + 2 * BLOCKS_PER_CYCLE,
        BLOCKS_PER_CYCLE
    )

    sources = []
    points = []
    vlines = []

    cycle_counter = 0

    for i in range(len(halving_blocks)):
        start = halving_blocks[i] - 105_000

        if i < len(halving_blocks) - 1:
            end = halving_blocks[i + 1] - 105_000
        else:
            end = blocks[-1] + 1

        mask = (blocks >= start) & (blocks < end)

        cycle_blocks = blocks[mask]
        cycle_prices = prices[mask]

        if len(cycle_prices) == 0:
            continue

        cycle_counter += 1

        factor = cycle_prices / cycle_prices[0]
        relative = cycle_blocks - start
        color = COLORS[i % len(COLORS)]

        sources.append({
            "source": ColumnDataSource(dict(
                relative=relative,
                factor=factor,
                price=cycle_prices,
                block=cycle_blocks,
                cycle=[f"Cycle {cycle_counter}"] * len(relative),
            )),
            "label": f"Cycle {cycle_counter}",
            "color": color,
        })

        if cycle_counter < 5:
            max_idx = factor.argmax()

            points.append({
                "kind": f"Max {cycle_counter}",
                "x": float(relative[max_idx]),
                "y": float(factor[max_idx]),
                "color": color,
                "marker": "x",
            })

            vlines.append({
                "x": float(relative[max_idx]),
                "color": color,
                "dash": "dotted",
            })

            if cycle_counter > 1:
                min_idx = factor.argmin()

                points.append({
                    "kind": f"Min {cycle_counter}",
                    "x": float(relative[min_idx]),
                    "y": float(factor[min_idx]),
                    "color": color,
                    "marker": "circle",
                })

                vlines.append({
                    "x": float(relative[min_idx]),
                    "color": color,
                    "dash": "dashed",
                })

    return sources, points, vlines


def make_html(df):
    sources, points, vlines = build_sources(df)

    x_start = 0
    x_end = 210_000
    y_start = 0.1
    y_end = 3000

    pan_tool = PanTool()
    wheel_zoom_tool = WheelZoomTool()
    box_zoom_tool = BoxZoomTool()
    reset_tool = ResetTool()
    save_tool = SaveTool()

    p = figure(
        title="Bitcoin Cycle Comparison",
        height=700,
        sizing_mode="stretch_width",
        x_range=Range1d(x_start, x_end),
        y_range=Range1d(y_start, y_end),
        tools=[pan_tool, wheel_zoom_tool, box_zoom_tool, reset_tool, save_tool],
        active_scroll=wheel_zoom_tool,
        active_drag=box_zoom_tool,
    )

    p.y_scale = LogScale()
    p.toolbar.logo = None

    p.title.align = "center"
    p.title.text_font_size = "24pt"

    for item in sources:
        p.line(
            "relative",
            "factor",
            source=item["source"],
            line_color=item["color"],
            line_width=3,
            line_alpha=0.75,
            legend_label=item["label"],
        )

    p.line(
        [x_start, x_end],
        [1, 1],
        line_color="black",
        line_width=1.5,
        line_alpha=0.8,
        legend_label="Start = 1x",
    )

    p.add_layout(Span(
        location=105_000,
        dimension="height",
        line_color="gray",
        line_width=2,
    ))

    p.add_layout(Label(
        x=105_000,
        y=1800,
        text="Halving",
        text_align="center",
        text_font_size="14pt",
        background_fill_color="white",
        background_fill_alpha=0.9,
        border_line_color="gray",
        border_line_alpha=0.7,
    ))

    for vl in vlines:
        p.add_layout(Span(
            location=vl["x"],
            dimension="height",
            line_color=vl["color"],
            line_dash=vl["dash"],
            line_width=1.7,
            line_alpha=0.55,
        ))

    label_offsets = {
        "Max 1": (-15000, 0.72),
        "Max 2": (16000, 1.18),
        "Max 3": (-16000, 1.18),
        "Max 4": (18000, 1.20),
        "Min 2": (-18000, 0.65),
        "Min 3": (-14000, 0.75),
        "Min 4": (16000, 0.70),
    }

    for pt in points:
        source = ColumnDataSource(dict(
            x=[pt["x"]],
            y=[pt["y"]],
            label=[pt["kind"]],
        ))

        if pt["marker"] == "x":
            p.x(
                "x",
                "y",
                source=source,
                size=18,
                line_width=4,
                color=pt["color"],
            )
        else:
            p.circle(
                "x",
                "y",
                source=source,
                size=12,
                color=pt["color"],
            )

        dx, yf = label_offsets.get(pt["kind"], (12000, 1.18))
        label_y = pt["y"] * yf

        if label_y < 0.12:
            label_y = 0.12

        if label_y > 2600:
            label_y = 2600

        from bokeh.models import Arrow, NormalHead

        # ------------------------
        # TEXT WITHOUT BOX
        # ------------------------

        text_x = pt["x"] + dx
        text_y = label_y

        p.add_layout(Label(
            x=text_x,
            y=text_y,
            text=pt["kind"],

            text_color=pt["color"],
            text_font_size="14pt",
            text_font_style="bold",

            background_fill_alpha=0.0,
            border_line_alpha=0.0,

            text_align="center"
        ))

        # ------------------------
        # ARROW FROM SHORTER SIDE OF TEXT
        # ------------------------

        # ------------------------
        # ARROW FROM MIDDLE OF TEXT
        # ------------------------

        TEXT_HALF_WIDTH = 4200

        # approximate half text height in log-scale coordinates
        TEXT_HALF_HEIGHT = text_y * 0.16

        if pt["x"] > text_x:
            # point is to right → arrow leaves right side
            arrow_x = text_x + TEXT_HALF_WIDTH
        else:
            # point is to left → arrow leaves left side
            arrow_x = text_x - TEXT_HALF_WIDTH

        # move arrow to vertical middle of text
        arrow_y = text_y + TEXT_HALF_HEIGHT

        p.add_layout(
            Arrow(
                end=NormalHead(
                    size=13,
                    fill_color=pt["color"],
                    line_color=pt["color"]
                ),

                x_start=arrow_x,
                y_start=arrow_y,

                x_end=pt["x"],
                y_end=pt["y"],

                line_color=pt["color"],
                line_width=2.4
            )
        )
    p.xaxis.axis_label = "Blocks Since Mid-Halving Start"
    p.yaxis.axis_label = "Price Factor (Start = 1x)"

    p.xaxis.axis_label_text_font_size = "20pt"
    p.yaxis.axis_label_text_font_size = "20pt"

    p.xaxis.major_label_text_font_size = "15pt"
    p.yaxis.major_label_text_font_size = "15pt"

    p.xaxis.formatter = NumeralTickFormatter(format="0,0")

    p.yaxis.ticker = FixedTicker(ticks=[0.1, 1, 2, 10, 100, 1000])
    p.yaxis.formatter = NumeralTickFormatter(format="0[.]0")

    p.grid.grid_line_dash = "dashed"
    p.grid.grid_line_alpha = 0.25

    hover = HoverTool(
        tooltips=[
            ("Cycle", "@cycle"),
            ("Relative block", "@relative{0,0}"),
            ("Factor", "@factor{0,0.00}x"),
            ("Price", "$@price{0,0}"),
            ("Block", "@block{0,0}"),
        ],
        mode="mouse",
    )
    p.add_tools(hover)

    p.legend.location = "top_left"
    p.legend.background_fill_alpha = 0.85
    p.legend.label_text_font_size = "13pt"
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

    zoom_in_button = Button(label="ZOOM +", button_type="success", css_classes=["big-control-button"])
    zoom_out_button = Button(label="ZOOM -", button_type="warning", css_classes=["big-control-button"])
    box_zoom_button = Button(label="BOX ZOOM", button_type="primary", css_classes=["big-control-button"])
    pan_button = Button(label="PAN", button_type="primary", css_classes=["big-control-button"])
    home_button = Button(label="HOME", button_type="danger", css_classes=["big-control-button"])

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

    explanation = Div(text="""
    <style>
    .analysis-wrapper {
        width: 100%;
        max-width: none;
        box-sizing: border-box;
        margin: 35px auto 50px auto;
        background: linear-gradient(135deg, #081224 0%, #0b132b 45%, #111827 100%);
        border-radius: 22px;
        padding: 28px;
        color: white;
        box-shadow: 0 10px 35px rgba(0,0,0,0.30);
        font-family: Arial, sans-serif;
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

    .analysis-subtitle strong {
        color: #38bdf8;
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
            width: 96%;
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

        <div class="analysis-title">Bitcoin Cycle Comparison</div>

        <div class="analysis-subtitle">
            This chart compares Bitcoin cycles after normalizing each cycle to
            <strong>1x at the mid-halving starting point</strong>.
            It shows that different cycles have surprisingly similar shapes and
            that their tops and bottoms often occur close to one another in block time.
        </div>

        <div class="analysis-grid">

            <div class="analysis-box">
                <h3>What is shown?</h3>
                <ul>
                    <li>Each colored line is one Bitcoin cycle.</li>
                    <li>The x-axis is blocks since the mid-halving start.</li>
                    <li>The y-axis is price factor on a log scale.</li>
                    <li>1x means the cycle starting price.</li>
                    <li>Markers show the maximum and minimum of each completed cycle.</li>
                    <li>Cycle 5 is partial, so no maximum or minimum is marked.</li>
                </ul>
            </div>

            <div class="analysis-box">
                <h3>Why normalize?</h3>
                <p>
                    Bitcoin traded at very different prices in different cycles.
                    Comparing raw prices would hide the common structure.
                </p>
                <p>
                    By dividing each cycle by its starting price, all cycles begin at 1x.
                    This makes it possible to compare their shapes, timing and growth factors.
                </p>
            </div>

            <div class="analysis-box">
                <h3>Close tops and bottoms</h3>
                <p>
                    A key observation is that the cycle maxima appear close to one another
                    in terms of blocks since the mid-halving start.
                </p>
                <p>
                    The minima also appear close to one another. This suggests that Bitcoin
                    cycles are not random in time, but are related to the halving-based block clock.
                </p>
            </div>

        </div>

        <div class="analysis-grid" style="margin-top: 24px;">

            <div class="analysis-box">
                <h3>Connection to the halving</h3>
                <p>
                    Bitcoin supply is reduced every 210,000 blocks. The halving therefore
                    gives Bitcoin a natural block-based rhythm.
                </p>
                <p>
                    When the tops and bottoms of different cycles appear near similar block
                    positions, it supports the idea that the cycle is linked to this issuance schedule.
                </p>
            </div>

            <div class="analysis-box">
                <h3>Diminishing returns</h3>
                <p>
                    Although the timing is similar, the cycle amplitudes become smaller.
                    Earlier cycles reached much larger multiples than later cycles.
                </p>
                <p>
                    As Bitcoin becomes larger, more capital is required to create the same
                    percentage increase. This is why the cycle may continue while returns diminish.
                </p>
            </div>

            <div class="analysis-box">
                <h3>Main interpretation</h3>
                <p>
                    The figure suggests two ideas at the same time: Bitcoin cycles have
                    similar timing, but their gains become smaller over time.
                </p>
                <p>
                    This combination is important: the cycle may remain visible, but future
                    cycles may be less explosive than the early ones.
                </p>
            </div>

        </div>

        <div class="footer-note">
            <strong>Main takeaway:</strong>
            The maxima and minima of Bitcoin cycles occur surprisingly close to one another
            when measured in blocks from the mid-halving point. This supports the view that
            Bitcoin cycles are connected to the 210,000-block halving structure. At the same time,
            the height of each cycle decreases, showing diminishing returns as Bitcoin matures.
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
        button_style,
        row(
            zoom_in_button,
            zoom_out_button,
            box_zoom_button,
            pan_button,
            home_button,
            sizing_mode="stretch_width",
        ),
        p,
        explanation,
        sizing_mode="stretch_width",
        css_classes=["main-page"],
    )

    os.makedirs("figures", exist_ok=True)

    output_file("index.html", title="Bitcoin Cycle Comparison")
    save(layout)

    output_file("figures/f_dem2.html", title="Bitcoin Cycle Comparison")
    save(layout)

    print("Saved index.html")
    print("Saved figures/f_dem2.html")

    show(layout)


def git_push():
    from github_publish import publish_to_github

    publish_to_github(
        add_paths=["index.html", "figures/f_dem2.html"],
        message=f"update f_dem2 website {datetime.now()}",
        log_file="run_log.txt",
    )


def main():
    df = fetch_price()
    df = add_blocks(df)
    make_html(df)
    if os.environ.get("SKIP_GITHUB_PUSH") == "1":
        print("Skipping per-script GitHub push; runner will publish once at the end.")
    else:
        git_push()
    print("DONE")


if __name__ == "__main__":
    main()
