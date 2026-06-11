import os
import requests
import pandas as pd

from bokeh.plotting import figure, output_file, save, show

from bokeh.models import (
    ColumnDataSource, HoverTool, Div, Button, CustomJS,
    PanTool, WheelZoomTool, BoxZoomTool, ResetTool, SaveTool,
    CustomJSTransform, Range1d, LinearAxis, FixedTicker
)
from bokeh.transform import transform
from bokeh.layouts import column, row
from bokeh.models import Arrow, NormalHead, Label


PRICE_URL = (
    "https://api.blockchain.info/charts/market-price?"
    "timespan=18years&rollingAverage=24hours"
    "&start=2010-01-01"
    "&format=json&sampled=false"
)

CSV_FILE = "daily_block_heights.csv"
BLOCKS_PER_CYCLE = 210_000
SEGMENTS = 8


def fetch_price_data():
    print("Downloading Bitcoin price data...")

    r = requests.get(PRICE_URL)
    r.raise_for_status()

    data = r.json()["values"]
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
        last_val = df_blocks.loc[last_idx, "block_number"]

        for i, date in enumerate(df_blocks.index[missing], start=1):
            df_blocks.loc[date, "block_number"] = last_val + 144 * i

    df_blocks["block_number"] = df_blocks["block_number"].astype(int)

    df = df.merge(
        df_blocks[["block_number"]],
        left_index=True,
        right_index=True,
        how="left"
    )

    return df


def make_heatmap_table(df):
    df = df.copy().sort_values("block_number")

    df["cycle"] = df["block_number"] // BLOCKS_PER_CYCLE
    df["block_in_cycle"] = df["block_number"] % BLOCKS_PER_CYCLE

    current_block_val = df["block_in_cycle"].iloc[-1]

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

    return table, current_block_val, blocks_per_segment


def make_website(table, current_block_val, blocks_per_segment):
    data = {
        "cycle": [],
        "segment": [],
        "xpos": [],
        "value": [],
        "label": [],
    }

    cycles = list(table.index)
    segments = list(table.columns)

    for cyc in cycles:
        for j, seg in enumerate(segments):
            val = float(table.loc[cyc, seg])

            data["cycle"].append(str(cyc))
            data["segment"].append(str(seg))
            data["xpos"].append(j + 0.5)
            data["value"].append(val)
            data["label"].append(
                f"+{val:.1f}%" if val > 0 else f"{val:.1f}%"
            )

    source = ColumnDataSource(data=data)

    color_transform = CustomJSTransform(
        v_func="""
        const colors = [];

        for (let i = 0; i < xs.length; i++) {
            const v = xs[i];

            if (v >= -1 && v <= 1) {
                colors.push("#ffffff");
            } else if (v > 1) {
                const t = Math.min((v - 1) / 99, 1);
                const r = Math.floor(245 - 215 * t);
                const g = Math.floor(255 - 105 * t);
                const b = Math.floor(245 - 165 * t);
                colors.push(`rgb(${r},${g},${b})`);
            } else {
                const t = Math.min((-v - 1) / 99, 1);
                const r = Math.floor(255 - 25 * t);
                const g = Math.floor(245 - 205 * t);
                const b = Math.floor(245 - 205 * t);
                colors.push(`rgb(${r},${g},${b})`);
            }
        }

        return colors;
        """
    )

    pan_tool = PanTool()
    wheel_zoom_tool = WheelZoomTool()
    box_zoom_tool = BoxZoomTool()
    reset_tool = ResetTool()
    save_tool = SaveTool()

    p = figure(
        title="Bitcoin Cycle Returns Heatmap",
        x_range=Range1d(0, SEGMENTS),
        y_range=list(reversed(cycles)),
        height=620,
        sizing_mode="stretch_width",
        tools=[pan_tool, wheel_zoom_tool, box_zoom_tool, reset_tool, save_tool],
        active_scroll=wheel_zoom_tool,
        active_drag=box_zoom_tool,
        toolbar_location=None
    )

    p.title.align = "center"
    p.title.text_font_size = "24pt"

    p.rect(
        x="xpos",
        y="cycle",
        width=1,
        height=1,
        source=source,
        fill_color=transform("value", color_transform),
        line_color="white",
        line_width=2
    )

    p.text(
        x="xpos",
        y="cycle",
        text="label",
        source=source,
        text_align="center",
        text_baseline="middle",
        text_font_size="12pt",
        text_color="black"
    )

    # ==========================================
    # Current position marker
    # ==========================================

    exact_x_pos = current_block_val / blocks_per_segment
    exact_x_pos = max(0, min(exact_x_pos, SEGMENTS))

    current_cycle = cycles[-1]

    marker_source = ColumnDataSource(data=dict(
        x=[exact_x_pos],
        y=[current_cycle],
        title=["Current Block in Cycle"],
        block=[f"{current_block_val:,}"],
        arrow=["▼"]
    ))

    # TOP: Current Block in Cycle
    p.text(
        x="x",
        y="y",
        text="title",
        source=marker_source,
        text_align="center",
        text_baseline="middle",
        text_font_size="8pt",
        text_font_style="bold",
        text_color="black",
        y_offset=23
    )

    # MIDDLE: block number
    p.text(
        x="x",
        y="y",
        text="block",
        source=marker_source,
        text_align="center",
        text_baseline="middle",
        text_font_size="9pt",
        text_font_style="bold",
        text_color="black",
        y_offset=37
    )

    # BOTTOM: arrow closest to x-axis
    p.text(
        x="x",
        y="y",
        text="arrow",
        source=marker_source,
        text_align="center",
        text_baseline="middle",
        text_font_size="14pt",
        text_font_style="bold",
        text_color="black",
        y_offset=50
    )

    hover = HoverTool(
        tooltips=[
            ("Cycle", "@cycle"),
            ("Segment", "@segment"),
            ("Return", "@label"),
        ]
    )
    p.add_tools(hover)

    boundary_ticks = list(range(SEGMENTS + 1))
    boundary_labels = {
        0: "+0",
        1: "+26.25K",
        2: "+52.5K",
        3: "+78.75K",
        4: "+105K",
        5: "+131.25K",
        6: "+157.5K",
        7: "+183.75K",
        8: "+210K",
    }

    p.xaxis.ticker = FixedTicker(ticks=boundary_ticks)
    p.xaxis.major_label_overrides = boundary_labels
    p.xaxis.axis_label = f"Segments ({blocks_per_segment:,} blocks each)"

    segment_ticks = [i + 0.5 for i in range(SEGMENTS)]
    segment_labels = {i + 0.5: f"S{i + 1}" for i in range(SEGMENTS)}

    top_axis = LinearAxis(
        ticker=FixedTicker(ticks=segment_ticks),
        major_label_overrides=segment_labels
    )

    p.add_layout(top_axis, "above")

    p.yaxis.axis_label = "Cycle Range"

    p.xaxis.major_label_text_font_size = "11pt"
    top_axis.major_label_text_font_size = "14pt"

    p.yaxis.major_label_text_font_size = "12pt"
    p.xaxis.axis_label_text_font_size = "16pt"
    p.yaxis.axis_label_text_font_size = "16pt"

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

    box_zoom_button = Button(label="BOX ZOOM", button_type="primary", css_classes=["big-control-button"])
    pan_button = Button(label="PAN", button_type="primary", css_classes=["big-control-button"])
    home_button = Button(label="HOME", button_type="danger", css_classes=["big-control-button"])

    box_zoom_button.js_on_click(CustomJS(args=dict(plot=p, box_zoom_tool=box_zoom_tool), code="plot.toolbar.active_drag = box_zoom_tool;"))
    pan_button.js_on_click(CustomJS(args=dict(plot=p, pan_tool=pan_tool), code="plot.toolbar.active_drag = pan_tool;"))
    home_button.js_on_click(CustomJS(args=dict(plot=p), code="plot.reset.emit();"))

    controls = column(
        button_style,
        row(box_zoom_button, pan_button, home_button, sizing_mode="stretch_width"),
        sizing_mode="stretch_width"
    )

    color_legend = Div(text="""
    <div style="width:110px;height:620px;display:flex;justify-content:center;align-items:center;">
        <div>
            <div style="text-align:center;font-size:18px;font-weight:bold;margin-bottom:15px;">
                Return %
            </div>
            <div style="display:flex;align-items:stretch;">
                <div style="
                    width:38px;
                    height:520px;
                    border-radius:12px;
                    border:1px solid #ccc;
                    background:linear-gradient(
                        to top,
                        #e32620 0%,
                        #f4a7a3 48%,
                        #ffffff 49.5%,
                        #ffffff 50.5%,
                        #d8ead8 52%,
                        #1f9d4a 100%
                    );
                "></div>
                <div style="
                    height:520px;
                    display:flex;
                    flex-direction:column;
                    justify-content:space-between;
                    padding-left:10px;
                    font-size:13px;
                ">
                    <div>+100%</div>
                    <div>+50%</div>
                    <div>+1%</div>
                    <div>0%</div>
                    <div>-1%</div>
                    <div>-50%</div>
                    <div>-100%</div>
                </div>
            </div>
        </div>
    </div>
        """, width=110, height=620)
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

            <div class="analysis-title">🔥 Bitcoin Cycle Returns Heatmap</div>

            <div class="analysis-subtitle">
                This heatmap divides each Bitcoin halving cycle into
                <strong>{SEGMENTS} equal block segments</strong>
                and shows the return in each segment. The goal is to see whether
                Bitcoin returns are random, or whether they follow a repeating cycle structure.
            </div>

            <div class="analysis-grid">

                <div class="analysis-box">
                    <h3>📊 What is shown?</h3>
                    <ul>
                        <li>Each row represents one Bitcoin halving cycle.</li>
                        <li>Each column represents one equal block segment.</li>
                        <li>Green cells indicate positive returns.</li>
                        <li>Red cells indicate negative returns.</li>
                        <li>Darker colors indicate stronger moves.</li>
                        <li>Current block in cycle: <strong>{current_block_val:,}</strong>.</li>
                    </ul>
                </div>

                <div class="analysis-box">
                    <h3>🔁 Evidence for a cycle</h3>
                    <p>
                        If Bitcoin returns were completely random, the green and red cells
                        would appear scattered without a clear structure.
                    </p>
                    <p>
                        Instead, the heatmap shows that similar parts of different cycles
                        often behave in similar ways. This repeating structure is visual
                        evidence that Bitcoin has followed a cycle tied to the halving period.
                    </p>
                </div>

                <div class="analysis-box">
                    <h3>📈 Upward and downward phases</h3>
                    <p>
                        The heatmap shows that Bitcoin cycles are not symmetric.
                        Historically, much of the cycle is positive, while the correction
                        phase is shorter and more concentrated.
                    </p>
                    <p>
                        A typical pattern is a long upward phase followed by a shorter
                        downward phase. This matches the idea that Bitcoin often rises for
                        several segments and then corrects sharply.
                    </p>
                </div>

            </div>

            <div class="analysis-grid" style="margin-top: 24px;">

                <div class="analysis-box">
                    <h3>⛏ Why the upward phase?</h3>
                    <p>
                        Every 210,000 blocks, the mining reward is cut in half.
                        This reduces the amount of newly created Bitcoin entering the market.
                    </p>
                    <p>
                        If demand remains strong, this reduction in new supply creates
                        upward pressure on price. The repeated green regions in the heatmap
                        are consistent with this halving-driven supply effect.
                    </p>
                </div>

                <div class="analysis-box">
                    <h3>⚡ Why the correction?</h3>
                    <p>
                        As Bitcoin price rises, mining becomes more profitable.
                        This attracts additional miners and increases spending on electricity,
                        hardware, cooling and infrastructure.
                    </p>
                    <p>
                        Eventually mining costs can become extremely large. When these costs
                        become difficult to sustain, they may contribute to the end of the
                        upward phase and the beginning of the correction phase.
                    </p>
                </div>

                <div class="analysis-box">
                    <h3>🎯 Main observation</h3>
                    <p>
                        The important point is not one single cell, but the repeated pattern
                        across cycles.
                    </p>
                    <p>
                        The heatmap suggests that Bitcoin's strongest returns tend to cluster
                        in similar parts of the halving cycle, while negative returns also
                        tend to appear in similar parts of the cycle.
                    </p>
                </div>

            </div>

            <div class="footer-note">
                <strong>Main takeaway:</strong>
                Across multiple halving periods, Bitcoin cycles show a surprisingly similar
                internal structure. Positive and negative returns are not evenly scattered;
                they tend to cluster in recurring parts of the 210,000 block cycle.
                This supports the view that Bitcoin's long-term behavior is influenced by
                the halving schedule and by the economic interaction between reduced supply
                and rising mining costs.
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

            .figure-row {
                width: 92% !important;
                max-width: 1350px !important;
                margin-left: auto !important;
                margin-right: auto !important;
            }

            .bk-plot-layout {
                max-width: 1250px !important;
            }
        }

        @media (max-width: 900px) {
            .main-page {
                width: 100% !important;
                max-width: 100% !important;
            }

            .figure-row {
                width: 100% !important;
                max-width: 100% !important;
            }
        }
        </style>
        """, sizing_mode="stretch_width")
        
    figure_row = row(
            p,
            color_legend,
            sizing_mode="stretch_width",
            css_classes=["figure-row"]
        )

    boundary_axis = Div(text="""
        <div style="
            width:92%;
            max-width:1250px;
            margin:-8px auto 12px auto;
            display:grid;
            grid-template-columns: repeat(8, 1fr);
            font-size:13px;
            color:black;
        ">
            <div style="text-align:left;">+0</div>
            <div style="text-align:left;">+26.25K</div>
            <div style="text-align:left;">+52.5K</div>
            <div style="text-align:left;">+78.75K</div>
            <div style="text-align:left;">+105K</div>
            <div style="text-align:left;">+131.25K</div>
            <div style="text-align:left;">+157.5K</div>
            <div style="text-align:left;">+183.75K</div>
            <div style="text-align:right;">+210K</div>
        </div>
        """, sizing_mode="stretch_width")

    layout = column(
        page_style,
        controls,
        figure_row,
        explanation,
        sizing_mode="stretch_width",
        css_classes=["main-page"]
    )

    os.makedirs("figures", exist_ok=True)

    output_file("index.html", title="Bitcoin Cycle Returns Heatmap")
    save(layout)

    output_file("figures/f_seg.html", title="Bitcoin Cycle Returns Heatmap")
    save(layout)

    print("Saved index.html")
    print("Saved figures/f_seg.html")

    show(layout)

def main():
    df = fetch_price_data()
    df = load_block_data(df)

    table, current_block_val, blocks_per_segment = make_heatmap_table(df)

    make_website(
        table,
        current_block_val,
        blocks_per_segment
    )


if __name__ == "__main__":
    main()