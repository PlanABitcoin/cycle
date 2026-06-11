import os
import shutil
import subprocess
import requests
import pandas as pd
from datetime import datetime, timedelta

from bokeh.plotting import figure, output_file, save, show
from bokeh.models import (
    ColumnDataSource, HoverTool, Span, Label, Div,
    Button, CustomJS, PanTool, WheelZoomTool, BoxZoomTool,
    ResetTool, SaveTool, NumeralTickFormatter, LogScale,
    FixedTicker
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
            (start_date, end_date, max_date, max_value, max_date, max_value)
        )

    points = []
    arrows = []

    prev_min = None
    prev_min_date = None

    i = 0

    for start_date, end_date, max_date, max_value, max_date, max_value in max_values_for_halving_periods:
        subset = df[
            (df.index >= max_date) &
            (df.index <= end_date)
        ]

        min_value = subset["Price"].min()
        min_date = subset.loc[subset["Price"].idxmin()].name

        points.append({
            "date": max_date,
            "price": max_value,
            "kind": "max",
            "label": max_date.strftime("%Y-%m-%d") if i > 0 else "",
        })

        if i < 4:
            points.append({
                "date": min_date,
                "price": min_value,
                "kind": "min",
                "label": min_date.strftime("%Y-%m-%d") if i > 0 else "",
            })

            arrows.append({
                "x_start": max_date,
                "y_start": max_value,
                "x_end": min_date,
                "y_end": min_value,
            })

        if i > 0:
            arrows.append({
                "x_start": prev_min_date,
                "y_start": prev_min,
                "x_end": max_date,
                "y_end": max_value,
            })

        prev_min = min_value
        prev_min_date = min_date
        i += 1

    return points, arrows


def make_website(df):
    points, arrows = calculate_cycle_points(df)

    source = ColumnDataSource(data=dict(
        Date=df.index,
        Price=df["Price"],
    ))

    x_start = df.index[0]
    x_end = datetime(2029, 1, 1)

    y_start = 0.1
    y_end = 250000

    pan_tool = PanTool()
    wheel_zoom_tool = WheelZoomTool()
    box_zoom_tool = BoxZoomTool()
    reset_tool = ResetTool()
    save_tool = SaveTool()

    p = figure(
        title="Bitcoin Cycle Dates",
        x_axis_type="datetime",
        height=760,
        sizing_mode="stretch_width",
        tools=[pan_tool, wheel_zoom_tool, box_zoom_tool, reset_tool, save_tool],
        active_scroll=wheel_zoom_tool,
        active_drag=box_zoom_tool,
        x_range=(x_start, x_end),
        y_range=(y_start, y_end),
    )

    p.y_scale = LogScale()
    p.toolbar.logo = None

    p.title.align = "center"
    p.title.text_font_size = "24pt"

    p.line(
        "Date",
        "Price",
        source=source,
        line_color="#1f77b4",
        line_width=2.2,
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
            y=0.14,
            text=f"Halving {i}",
            angle=1.5708,
            text_font_size="12pt",
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
                y=0.14,
                text="mid",
                angle=1.5708,
                text_font_size="12pt",
                text_color="black",
            ))

    for idx, h in enumerate(HALVINGS):
        label_text = h.strftime("%Y-%m-%d")
        label_y = 3.0

        if idx == 4:
            label_text = "Predicted\n" + h.strftime("%Y-%m-%d")
            label_y = 120

        p.add_layout(Label(
            x=h,
            y=label_y,
            text=label_text,
            text_font_size="12pt",
            text_color="darkred",
            background_fill_color="white",
            background_fill_alpha=0.9,
            border_line_color="darkred",
            border_line_alpha=0.9,
            text_align="center",
        ))

    from bokeh.models import Arrow, NormalHead

    for ar in arrows:
        p.add_layout(Arrow(
            end=NormalHead(size=10),
            x_start=ar["x_start"],
            y_start=ar["y_start"],
            x_end=ar["x_end"],
            y_end=ar["y_end"],
            line_color="black",
            line_width=1.2,
        ))

    max_source = ColumnDataSource(data=dict(
        Date=[pt["date"] for pt in points if pt["kind"] == "max"],
        Price=[pt["price"] for pt in points if pt["kind"] == "max"],
        Label=[pt["label"] for pt in points if pt["kind"] == "max"],
    ))

    min_source = ColumnDataSource(data=dict(
        Date=[pt["date"] for pt in points if pt["kind"] == "min"],
        Price=[pt["price"] for pt in points if pt["kind"] == "min"],
        Label=[pt["label"] for pt in points if pt["kind"] == "min"],
    ))

    p.scatter(
        "Date",
        "Price",
        source=max_source,
        size=10,
        color="red",
        marker="circle",
        legend_label="Cycle maximum",
    )

    p.scatter(
        "Date",
        "Price",
        source=min_source,
        size=12,
        color="blue",
        marker="x",
        legend_label="Cycle minimum",
    )

    for pt in points:
        if not pt["label"]:
            continue

        if pt["kind"] == "max":
            y = pt["price"] * 1.35
            color = "red"
        else:
            y = pt["price"] * 0.72
            color = "blue"

        p.add_layout(Label(
            x=pt["date"],
            y=y,
            text=pt["label"],
            text_font_size="11pt",
            text_color=color,
            text_align="center",
        ))

    p.xaxis.axis_label = "Date"
    p.yaxis.axis_label = "USD"

    p.xaxis.axis_label_text_font_size = "18pt"
    p.yaxis.axis_label_text_font_size = "18pt"
    p.xaxis.major_label_text_font_size = "13pt"
    p.yaxis.major_label_text_font_size = "13pt"

    p.yaxis.ticker = FixedTicker(ticks=[0.1, 1, 10, 100, 1000, 100000])
    p.yaxis.formatter = NumeralTickFormatter(format="0[.]0")

    p.grid.grid_line_alpha = 0.45
    p.grid.grid_line_color = "gray"

    hover = HoverTool(
        tooltips=[
            ("Date", "@Date{%F}"),
            ("Price", "$@Price{0,0}"),
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
        margin-bottom: 18px;
    }

    .analysis-subtitle {
        text-align: center;
        font-size: 22px;
        line-height: 1.7;
        color: #d1d5db;
        margin-bottom: 28px;
    }

    .analysis-table {
        width: 100%;
        border-collapse: collapse;
        margin: 24px 0 30px 0;
        font-size: 17px;
        overflow: hidden;
        border-radius: 14px;
    }

    .analysis-table th {
        background: rgba(56,189,248,0.22);
        color: #e0f2fe;
        padding: 12px;
        border: 1px solid rgba(255,255,255,0.22);
    }

    .analysis-table td {
        padding: 11px;
        text-align: center;
        color: #e5e7eb;
        border: 1px solid rgba(255,255,255,0.18);
        background: rgba(255,255,255,0.035);
    }

    .analysis-grid {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 24px;
        border-top: 1px solid rgba(255,255,255,0.15);
        padding-top: 26px;
    }

    .analysis-box {
        background: rgba(255,255,255,0.045);
        border: 1px solid rgba(255,255,255,0.09);
        border-radius: 18px;
        padding: 24px;
    }

    .analysis-box h3 {
        margin-top: 0;
        font-size: 27px;
        color: #38bdf8;
    }

    .analysis-box ul,
    .analysis-box p {
        line-height: 1.85;
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

        .analysis-table {
            font-size: 13px;
        }

        .analysis-table th,
        .analysis-table td {
            padding: 7px;
        }
    }
    </style>

    <div class="analysis-wrapper">
        <div class="analysis-title">Bitcoin Cycle Dates</div>

        <div class="analysis-subtitle">
            Bitcoin is often described as having a <strong>four-year cycle</strong>,
            but this is only an approximation. The cycle is driven by the halving mechanism,
            which occurs every <strong>210,000 blocks</strong>, not every four calendar years.
        </div>

        <table class="analysis-table">
            <tr>
                <th>Halving</th>
                <th>Date</th>
                <th>Days since previous</th>
                <th>Elapsed time</th>
            </tr>
            <tr>
                <td>1</td>
                <td>2012-11-28</td>
                <td>--</td>
                <td>--</td>
            </tr>
            <tr>
                <td>2</td>
                <td>2016-07-09</td>
                <td>1319</td>
                <td>3 years, 7 months, 11 days</td>
            </tr>
            <tr>
                <td>3</td>
                <td>2020-05-11</td>
                <td>1402</td>
                <td>3 years, 10 months, 2 days</td>
            </tr>
            <tr>
                <td>4</td>
                <td>2024-04-20</td>
                <td>1440</td>
                <td>3 years, 11 months, 9 days</td>
            </tr>
            <tr>
                <td>5, predicted</td>
                <td>2028-03-31</td>
                <td>1441</td>
                <td>3 years, 11 months, 11 days</td>
            </tr>
        </table>

        <div class="analysis-grid">

            <div class="analysis-box">
                <h3>What is shown?</h3>
                <ul>
                    <li>Blue line: Bitcoin price on a log scale</li>
                    <li>Red vertical lines: halving dates</li>
                    <li>Dashed red lines: mid-halving dates</li>
                    <li>Red dots: cycle tops</li>
                    <li>Blue x marks: cycle bottoms</li>
                </ul>
            </div>

            <div class="analysis-box">
                <h3>Main idea</h3>
                <p>
                    The phrase “four-year cycle” can be misleading.
                    The observed cycle is usually slightly shorter than four years,
                    often closer to <strong>3 years and 11 months</strong>.
                    This helps explain why tops and bottoms may appear earlier than a strict
                    calendar-year interpretation would suggest.
                </p>
            </div>

            <div class="analysis-box">
                <h3>Method</h3>
                <p>
                    Cycle maxima are calculated as in the original code:
                    within each halving period, the maximum is searched only up to
                    <strong>60 days before the next halving</strong>.
                    The arrows connect cycle tops to bottoms and bottoms to the next tops.
                </p>
            </div>

        </div>

        <div class="footer-note">
            Blocks are found randomly, with an average target of about 10 minutes.
            When blocks arrive slightly faster, 210,000 blocks are completed before four full calendar years.
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

    output_file("index.html", title="Bitcoin Cycle Dates")
    save(layout)

    output_file("figures/f_cycle_dates.html", title="Bitcoin Cycle Dates")
    save(layout)

    print("Saved index.html")
    print("Saved figures/f_cycle_dates.html")

    show(layout)


def git_push():
    from github_publish import publish_to_github

    publish_to_github(
        add_paths=["index.html", "figures/f_cycle_dates.html"],
        message=f"update cycle dates website {datetime.now()}",
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
