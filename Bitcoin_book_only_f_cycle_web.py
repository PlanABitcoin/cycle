import os
import math
import shutil
import subprocess
import requests
import pandas as pd
from datetime import datetime, timedelta

from bokeh.plotting import figure, output_file, save, show
from bokeh.models import (
    ColumnDataSource, HoverTool, Span, Label, Div,
    Button, CustomJS, PanTool, WheelZoomTool,
    BoxZoomTool, ResetTool, SaveTool,
    NumeralTickFormatter, LogScale, Range1d,
    Arrow, NormalHead, FixedTicker
)
from bokeh.layouts import column, row


REPO_URL = "https://github.com/PlanABitcoin/cycle.git"

PRICE_URL = (
    "https://api.blockchain.info/charts/market-price?"
    "timespan=18years"
    "&rollingAverage=24hours"
    "&start=2010-01-01"
    "&format=json"
    "&sampled=false"
)

HALVINGS = [
    datetime(2012, 11, 28),
    datetime(2016, 7, 9),
    datetime(2020, 5, 11),
    datetime(2024, 4, 19),
    datetime(2028, 3, 31),
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
    df = df[df["Price"] > 0].copy()

    return df


def calculate_cycle_points(df):
    max_values_for_halving_periods = []

    for i in range(len(HALVINGS)):
        if i == 0:
            start_date = df.index[0]
        else:
            start_date = HALVINGS[i - 1]

        end_date = HALVINGS[i]
        reduced_end_date = end_date - timedelta(days=60)

        subset = df[
            (df.index >= start_date) &
            (df.index <= reduced_end_date)
        ]

        max_value = subset["Price"].max()
        max_date = subset.loc[subset["Price"].idxmax()].name

        max_values_for_halving_periods.append(
            (start_date, end_date, max_date, max_value)
        )

    max_points = []
    min_points = []
    arrows = []

    prev_min = None
    prev_min_date = None

    for i, (start_date, end_date, max_date, max_value) in enumerate(max_values_for_halving_periods):
        subset = df[
            (df.index >= max_date) &
            (df.index <= end_date)
        ]

        min_value = subset["Price"].min()
        min_date = subset.loc[subset["Price"].idxmin()].name

        max_points.append({
            "date": max_date,
            "price": max_value,
            "cycle": f"Cycle {i + 1} maximum",
        })

        if i < 4:
            min_points.append({
                "date": min_date,
                "price": min_value,
                "cycle": f"Cycle {i + 1} minimum",
            })

            arrows.append({
                "x_start": max_date,
                "y_start": max_value,
                "x_end": min_date,
                "y_end": min_value,
                "color": "red",
            })

        if i > 0:
            arrows.append({
                "x_start": prev_min_date,
                "y_start": prev_min,
                "x_end": max_date,
                "y_end": max_value,
                "color": "green",
            })

        prev_min = min_value
        prev_min_date = min_date

    return max_points, min_points, arrows


def make_website(df):
    max_points, min_points, arrows = calculate_cycle_points(df)

    source = ColumnDataSource(data=dict(
        Date=df.index,
        Price=df["Price"],
    ))

    max_source = ColumnDataSource(data=dict(
        Date=[p["date"] for p in max_points],
        Price=[p["price"] for p in max_points],
        Cycle=[p["cycle"] for p in max_points],
    ))

    min_source = ColumnDataSource(data=dict(
        Date=[p["date"] for p in min_points],
        Price=[p["price"] for p in min_points],
        Cycle=[p["cycle"] for p in min_points],
    ))

    x_start = df.index[0]
    x_end = datetime(2028, 6, 1)

    y_start = 0.1
    y_end = 250000

    pan_tool = PanTool()
    wheel_zoom_tool = WheelZoomTool()
    box_zoom_tool = BoxZoomTool()
    reset_tool = ResetTool()
    save_tool = SaveTool()

    p = figure(
        title="Bitcoin Cycle",
        x_axis_type="datetime",
        height=760,
        sizing_mode="stretch_width",
        tools=[pan_tool, wheel_zoom_tool, box_zoom_tool, reset_tool, save_tool],
        active_scroll=wheel_zoom_tool,
        active_drag=box_zoom_tool,
        x_range=Range1d(x_start, x_end),
        y_range=Range1d(y_start, y_end),
    )

    p.y_scale = LogScale()

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

    p.yaxis.formatter = NumeralTickFormatter(format="0,0.[0]")

    p.toolbar.logo = None

    p.title.align = "center"
    p.title.text_font_size = "24pt"

    p.line(
        "Date",
        "Price",
        source=source,
        line_color="#1f77b4",
        line_width=2.3,
        legend_label="Bitcoin price",
    )

    for i, h in enumerate(HALVINGS, 1):
        p.add_layout(Span(
            location=h,
            dimension="height",
            line_color="red",
            line_width=2,
            line_alpha=0.65,
        ))

        p.add_layout(Label(
            x=h,
            y=0.35,
            text=f"Halving {i}",
            angle=math.pi / 2,
            text_font_size="13pt",
            text_color="black",
        ))

        if i < len(HALVINGS):
            mid = h + (HALVINGS[i] - h) / 2

            p.add_layout(Span(
                location=mid,
                dimension="height",
                line_color="red",
                line_dash="dashed",
                line_width=2,
                line_alpha=0.55,
            ))

            p.add_layout(Label(
                x=mid,
                y=0.35,
                text="mid",
                angle=math.pi / 2,
                text_font_size="13pt",
                text_color="black",
            ))

    for ar in arrows:
        p.add_layout(Arrow(
            end=NormalHead(
                size=12,
                fill_color=ar["color"],
                line_color=ar["color"],
            ),
            x_start=ar["x_start"],
            y_start=ar["y_start"],
            x_end=ar["x_end"],
            y_end=ar["y_end"],
            line_color=ar["color"],
            line_width=2.4,
            line_alpha=0.8,
        ))

    p.scatter(
        "Date",
        "Price",
        source=max_source,
        size=9,
        color="red",
        marker="circle",
        legend_label="Cycle maximum",
    )

    p.scatter(
        "Date",
        "Price",
        source=min_source,
        size=11,
        color="blue",
        marker="x",
        legend_label="Cycle minimum",
    )

    p.xaxis.axis_label = "Date"
    p.yaxis.axis_label = "USD"

    p.xaxis.axis_label_text_font_size = "18pt"
    p.yaxis.axis_label_text_font_size = "18pt"
    p.xaxis.major_label_text_font_size = "13pt"
    p.yaxis.major_label_text_font_size = "13pt"

    p.grid.grid_line_alpha = 0.45
    p.grid.grid_line_color = "gray"

    hover_price = HoverTool(
        renderers=[],
        tooltips=[
            ("Date", "@Date{%F}"),
            ("Price", "$@Price{0,0}"),
        ],
        formatters={"@Date": "datetime"},
        mode="vline",
    )

    hover_points = HoverTool(
        tooltips=[
            ("Point", "@Cycle"),
            ("Date", "@Date{%F}"),
            ("Price", "$@Price{0,0}"),
        ],
        formatters={"@Date": "datetime"},
        mode="mouse",
    )

    p.add_tools(hover_price)
    p.add_tools(hover_points)

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
            x0=x_start.timestamp() * 1000,
            x1=x_end.timestamp() * 1000,
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
        font-size: 16px;
        color: #cbd5e1;
        line-height: 1.8;
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

        <div class="analysis-title">
            Understanding the Bitcoin Cycle
        </div>

        <div class="analysis-subtitle">
            This chart shows Bitcoin price on a logarithmic scale, together with
            the halving dates, mid-halving dates, cycle tops, cycle bottoms,
            and the large upward and downward movements that repeat across cycles.
        </div>

        <div class="analysis-grid">

            <div class="analysis-box">
                <h3>Cycle Structure</h3>

                <p>
                    Each Bitcoin cycle has two main phases.
                </p>

                <ul>
                      <li>
                        <span style="color:#22c55e;font-weight:bold;">
                            Upward phase:
                        </span>
                        a long rise that usually lasts about three years.
                        It begins near a cycle bottom, continues through the
                        halving, and often reaches a cycle top after the halving.
                    </li>

                    <li>
                        <span style="color:#ef4444;font-weight:bold;">
                            Downward phase:
                        </span>
                        a shorter correction phase that usually lasts about one year.
                        It begins after the cycle top and continues until the next
                        cycle bottom.
                    </li>


                    <li>
                        The red halving line usually appears near the middle of
                        the upward phase.
                    </li>

                    <li>
                        The dashed red mid-halving line often appears near the
                        correction region of the cycle.
                    </li>
                </ul>
            </div>

            <div class="analysis-box">
                <h3>What the Figure Shows</h3>

                <ul>
                    <li><b>Blue line:</b> Bitcoin price in USD.</li>

                    <li><b>Red vertical lines:</b> halving dates.</li>

                    <li><b>Dashed red lines:</b> midpoints between halvings.</li>

                    <li><b>Red circles:</b> cycle maximum points.</li>

                    <li><b>Blue X marks:</b> cycle minimum points.</li>

                    <li><b>Green arrows:</b> upward movements from cycle bottoms to tops.</li>

                    <li><b>Red arrows:</b> downward corrections from cycle tops to bottoms.</li>
                </ul>

                <p>
                    On a logarithmic scale, straight upward lines represent
                    approximately constant percentage growth, while straight
                    downward lines represent approximately constant percentage
                    decline.
                </p>
            </div>

            <div class="analysis-box">
                <h3>Size of the Cycles</h3>

                <ul>
                    <li>
                        Early cycles were extremely large because Bitcoin was
                        small and a modest amount of capital could move the price
                        by a very large percentage.
                    </li>

                    <li>
                        Later cycles are still large, but the percentage gains
                        become smaller. This is the phenomenon of
                        <b>diminishing returns</b>.
                    </li>

                    <li>
                        Historical corrections after cycle tops were often very
                        deep, sometimes in the range of about 50% to 80%.
                    </li>

                    <li>
                        The cycle is not exactly a four-year calendar cycle.
                        It is more naturally connected to the 210,000-block
                        halving interval.
                    </li>
                </ul>
            </div>

        </div>

        <div class="footer-note">
            <b>Cycle Theory Summary</b><br><br>

            The Bitcoin Cycle theory is based on two central ideas.
            First, the mining reward is the main source of new Bitcoin supply.
            Therefore, when the halving cuts the reward in half, the flow of new
            Bitcoin entering the market is reduced. If demand remains strong, this
            creates upward pressure on price.

            <br><br>

            Second, mining cost tends to follow Bitcoin price. When price rises too
            much, the implied mining cost becomes very large and may become difficult
            to sustain. This can create pressure for a correction.

            <br><br>

            Together, these forces help explain the repeated pattern of a long upward
            phase followed by a shorter downward phase. The purpose of this figure is
            not to predict the future exactly, but to show the rhythm of Bitcoin cycles
            and where the major tops, bottoms, halvings, and corrections have appeared
            historically.

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

    output_file("index.html", title="Bitcoin Cycle")
    save(layout)

    output_file("figures/f_cycle.html", title="Bitcoin Cycle")
    save(layout)

    print("Saved index.html")
    print("Saved figures/f_cycle.html")

    show(layout)


def git_push():
    from github_publish import publish_to_github

    publish_to_github(
        add_paths=["index.html", "figures/f_cycle.html"],
        message=f"update cycle website {datetime.now()}",
        log_file="run_log.txt",
    )


def main():
    df = fetch_price()
    make_website(df)
    if os.environ.get("SKIP_GITHUB_PUSH") == "1":
        print("Skipping per-script GitHub push; runner will publish once at the end.")
    else:
        git_push()
    print("DONE")


if __name__ == "__main__":
    main()
