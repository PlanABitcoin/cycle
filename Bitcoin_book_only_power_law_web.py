# f_powerlaw_website_git.py

import os
import shutil
import subprocess
import requests
import numpy as np
import pandas as pd
from datetime import datetime

from bokeh.plotting import figure, output_file, save, show
from bokeh.models import (
    ColumnDataSource,
    HoverTool,
    Div,
    Button,
    CustomJS,
    PanTool,
    WheelZoomTool,
    BoxZoomTool,
    ResetTool,
    SaveTool,
    NumeralTickFormatter,
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


def build_powerlaw_data(df):
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

    x = np.log10(df_power["days_since_genesis"].values)
    y = np.log10(df_power["Price"].values)

    slope, intercept = np.polyfit(x, y, 1)

    future_dates = pd.date_range(
        start=plot_start,
        end=plot_end,
        freq="D"
    )

    future_days = (
        future_dates - genesis_date
    ).days.values

    powerlaw = 10 ** (
        slope * np.log10(future_days)
        + intercept
    )

    upper_band = powerlaw * 2
    lower_band = powerlaw / 2

    return (
        df_power,
        future_dates,
        powerlaw,
        upper_band,
        lower_band,
        slope,
        intercept,
        plot_start,
        plot_end,
    )


def make_website(df):
    (
        df_power,
        future_dates,
        powerlaw,
        upper_band,
        lower_band,
        slope,
        intercept,
        plot_start,
        plot_end,
    ) = build_powerlaw_data(df)

    pan_tool = PanTool()
    wheel_zoom_tool = WheelZoomTool()
    box_zoom_tool = BoxZoomTool()
    reset_tool = ResetTool()
    save_tool = SaveTool()

    p = figure(
        title="Bitcoin Power Law",
        height=700,
        sizing_mode="stretch_width",
        x_axis_type="datetime",
        y_axis_type="log",
        x_range=(plot_start, plot_end),
        y_range=(1, 10_000_000),
        tools=[
            pan_tool,
            wheel_zoom_tool,
            box_zoom_tool,
            reset_tool,
            save_tool,
        ],
        active_scroll=wheel_zoom_tool,
        active_drag=box_zoom_tool,
    )

    p.toolbar.logo = None

    p.title.align = "center"
    p.title.text_font_size = "24pt"

    price_source = ColumnDataSource(
        data=dict(
            Date=df_power.index,
            Price=df_power["Price"],
        )
    )

    model_source = ColumnDataSource(
        data=dict(
            Date=future_dates,
            PowerLaw=powerlaw,
            Upper=upper_band,
            Lower=lower_band,
        )
    )

    p.line(
        "Date",
        "Price",
        source=price_source,
        line_width=2.2,
        line_color="#1f77b4",
        legend_label="Bitcoin Price",
    )

    p.line(
        "Date",
        "PowerLaw",
        source=model_source,
        line_width=2.5,
        line_color="#ff7f0e",
        legend_label="Power Law Fit",
    )

    p.line(
        "Date",
        "Upper",
        source=model_source,
        line_width=2,
        line_dash="dashed",
        line_color="#2ca02c",
        legend_label="Upper Band ×2",
    )

    p.line(
        "Date",
        "Lower",
        source=model_source,
        line_width=2,
        line_dash="dashed",
        line_color="#d62728",
        legend_label="Lower Band ÷2",
    )

    p.xaxis.axis_label = "Date"
    p.yaxis.axis_label = "USD"

    p.xaxis.axis_label_text_font_size = "20pt"
    p.yaxis.axis_label_text_font_size = "20pt"

    p.xaxis.major_label_text_font_size = "15pt"
    p.yaxis.major_label_text_font_size = "15pt"

    p.yaxis.formatter = NumeralTickFormatter(format="0,0")

    p.background_fill_color = "white"
    p.border_fill_color = "white"

    p.grid.grid_line_color = "#d9d9d9"
    p.grid.grid_line_alpha = 0.85
    p.grid.grid_line_dash = "solid"
    p.grid.grid_line_width = 1

    p.xgrid.minor_grid_line_color = "#eeeeee"
    p.ygrid.minor_grid_line_color = "#eeeeee"

    p.xgrid.minor_grid_line_alpha = 0.8
    p.ygrid.minor_grid_line_alpha = 0.8

    p.xgrid.minor_grid_line_dash = "dashed"
    p.ygrid.minor_grid_line_dash = "dashed"

    p.xgrid.minor_grid_line_width = 0.8
    p.ygrid.minor_grid_line_width = 0.8

    p.xaxis.minor_tick_line_color = "#cccccc"
    p.yaxis.minor_tick_line_color = "#cccccc"

    p.xaxis.minor_tick_out = 4
    p.yaxis.minor_tick_out = 4

    hover = HoverTool(
        tooltips=[
            ("Date", "$x{%F}"),
            ("USD", "$y{0,0}"),
        ],
        formatters={
            "$x": "datetime",
        },
        mode="mouse",
        point_policy="follow_mouse",
    )

    p.add_tools(hover)

    p.legend.location = "top_left"
    p.legend.background_fill_color = "white"
    p.legend.background_fill_alpha = 0.95
    p.legend.border_line_color = "#cccccc"
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

    zoom_in_button = Button(
        label="ZOOM +",
        button_type="success",
        css_classes=["big-control-button"],
    )

    zoom_out_button = Button(
        label="ZOOM -",
        button_type="warning",
        css_classes=["big-control-button"],
    )

    box_zoom_button = Button(
        label="BOX ZOOM",
        button_type="primary",
        css_classes=["big-control-button"],
    )

    pan_button = Button(
        label="PAN",
        button_type="primary",
        css_classes=["big-control-button"],
    )

    home_button = Button(
        label="HOME",
        button_type="danger",
        css_classes=["big-control-button"],
    )

    x_start_ms = plot_start.timestamp() * 1000
    x_end_ms = plot_end.timestamp() * 1000

    y_start = 1
    y_end = 10_000_000

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
            x0=x_start_ms,
            x1=x_end_ms,
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
            x0=x_start_ms,
            x1=x_end_ms,
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

    explanation = Div(text=f"""
    <style>
    .analysis-wrapper {{
        width: 96%;
        box-sizing: border-box;
        margin: 35px auto 50px auto;
        background: linear-gradient(135deg, #081224 0%, #0b132b 45%, #111827 100%);
        border-radius: 22px;
        padding: 28px;
        color: white;
        box-shadow: 0 10px 35px rgba(0,0,0,0.30);
        font-family: Arial, sans-serif;
    }}

    .analysis-title {{
        text-align: center;
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 20px;
    }}

    .analysis-subtitle {{
        text-align: center;
        font-size: 22px;
        line-height: 1.7;
        color: #d1d5db;
        margin-bottom: 28px;
    }}

    .analysis-subtitle strong {{
        color: #38bdf8;
    }}

    .analysis-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 28px;
        border-top: 1px solid rgba(255,255,255,0.15);
        padding-top: 28px;
    }}

    .analysis-box {{
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 18px;
        padding: 24px;
    }}

    .analysis-box h3 {{
        margin-top: 0;
        font-size: 28px;
        color: #38bdf8;
    }}

    .analysis-box ul,
    .analysis-box p {{
        line-height: 1.9;
        font-size: 18px;
        color: #e5e7eb;
    }}

    .footer-note {{
        margin-top: 28px;
        padding-top: 18px;
        border-top: 1px solid rgba(255,255,255,0.15);
        text-align: center;
        font-size: 15px;
        color: #cbd5e1;
        line-height: 1.8;
    }}

    .footer-note strong {{
        color: #facc15;
    }}

    @media (max-width: 900px) {{
        .analysis-wrapper {{
            width: 100%;
            padding: 18px;
            border-radius: 16px;
        }}

        .analysis-title {{
            font-size: 30px;
        }}

        .analysis-subtitle {{
            font-size: 17px;
        }}

        .analysis-grid {{
            grid-template-columns: 1fr;
            gap: 18px;
        }}

        .analysis-box h3 {{
            font-size: 24px;
        }}

        .analysis-box ul,
        .analysis-box p {{
            font-size: 16px;
        }}
    }}
    </style>

    <div class="analysis-wrapper">

        <div class="analysis-title">Bitcoin Power Law</div>

        <div class="analysis-subtitle">
            This figure shows Bitcoin's long-term growth path using a
            <strong>power law trend</strong>. It is complementary to the Bitcoin cycle:
            the power law describes the long-term road, while the cycle describes the
            repeated movements above and below that road.
        </div>

        <div class="analysis-grid">

            <div class="analysis-box">
                <h3>📊 What is shown?</h3>
                <ul>
                    <li><span style="color:#60a5fa;">Blue</span>: Bitcoin market price.</li>
                    <li><span style="color:#f97316;">Orange</span>: fitted power law trend.</li>
                    <li><span style="color:#22c55e;">Green dashed</span>: upper band, 2x above trend.</li>
                    <li><span style="color:#ef4444;">Red dashed</span>: lower band, 2x below trend.</li>
                    <li>The y-axis is logarithmic, so long-term percentage growth is easier to see.</li>
                </ul>
            </div>

            <div class="analysis-box">
                <h3>📈 Why a power law?</h3>
                <p>
                    Bitcoin is a growing network. In the early years, it was small, so a modest
                    amount of new capital could create very large percentage gains.
                </p>
                <p>
                    As Bitcoin becomes larger and more mature, each additional percentage gain
                    requires much more capital. This creates a natural slowdown in growth,
                    which is why the long-term trend can look like a power law.
                </p>
            </div>

            <div class="analysis-box">
                <h3>🔁 Connection to the Bitcoin cycle</h3>
                <p>
                    The Bitcoin cycle explains the repeated upward and downward phases around
                    halvings. The power law explains the long-term direction around which these
                    cycles move.
                </p>
                <p>
                    In this view, bull markets push Bitcoin above the long-term trend, while bear
                    markets bring it back toward, or below, the trend.
                </p>
            </div>

        </div>

        <div class="analysis-grid" style="margin-top: 24px;">

            <div class="analysis-box">
                <h3>🚀 Above the trend</h3>
                <p>
                    When Bitcoin approaches the upper band, price is high relative to the
                    long-term power law path.
                </p>
                <p>
                    These periods often correspond to the later stages of an upward cycle,
                    when optimism is strong and price rises faster than the long-term trend.
                </p>
            </div>

            <div class="analysis-box">
                <h3>📉 Below the trend</h3>
                <p>
                    When Bitcoin approaches the lower band, price is low relative to the
                    long-term trend.
                </p>
                <p>
                    These periods often occur after large corrections, when market sentiment
                    is weak and Bitcoin trades below its long-term growth path.
                </p>
            </div>

            <div class="analysis-box">
                <h3>🎯 Main interpretation</h3>
                <p>
                    The power law and the Bitcoin cycle are not competing explanations.
                    They answer different questions.
                </p>
                <p>
                    The power law describes the long-term growth trajectory. The Bitcoin cycle
                    explains why the price repeatedly moves above and below that trajectory.
                </p>
            </div>

        </div>

        <div class="footer-note">
            <strong>Main takeaway:</strong>
            Bitcoin's long-term price appears to grow along a power-law path, while halvings
            and market psychology create repeated cycles around that path. The power law gives
            the broad direction; the Bitcoin cycle explains the timing of booms and corrections.
            Together, they provide a more complete picture than either model alone.
            <br><br>
            Model:
            log10(price) = {slope:.3f} · log10(days) + {intercept:.3f}
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

    output_file("index.html", title="Bitcoin Power Law")
    save(layout)

    output_file("figures/f_powerlaw.html", title="Bitcoin Power Law")
    save(layout)

    print("Saved index.html")
    print("Saved figures/f_powerlaw.html")

    show(layout)


def git_push():
    from github_publish import publish_to_github

    publish_to_github(
        add_paths=["index.html", "figures/f_powerlaw.html"],
        message=f"update power law website {datetime.now()}",
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
