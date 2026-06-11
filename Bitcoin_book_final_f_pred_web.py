import pandas as pd
from datetime import datetime, timedelta
import requests, json, math, os, shutil, subprocess

from bokeh.plotting import figure, output_file, save, show
from bokeh.models import (
    ColumnDataSource, HoverTool, Span, BoxAnnotation, Label,
    Arrow, NormalHead, NumeralTickFormatter, FixedTicker,
    Button, CustomJS, Div,
    PanTool, WheelZoomTool, BoxZoomTool, ResetTool, SaveTool
)
from bokeh.layouts import column, row

REPO_URL = "https://github.com/PlanABitcoin/cycle.git"


# ============================================================
# GIT
# ============================================================

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
print("Using Git:", GIT)


# ============================================================
# HELPERS
# ============================================================

def fetch_and_process(url, column_name):
    response = requests.get(url)
    response.raise_for_status()
    data = json.loads(response.content).get("values", [])

    df = pd.DataFrame(data)
    df["Date"] = pd.to_datetime(df["x"], unit="s", utc=True)
    df.rename(columns={"y": column_name}, inplace=True)
    df.set_index("Date", inplace=True)
    df.drop(columns=["x"], inplace=True)
    df = df.resample("D").last().tz_localize(None)

    return df


def log_interp(y0, y1, frac):
    return y0 * (y1 / y0) ** frac


def date_interp(x0, x1, frac):
    return x0 + (x1 - x0) * frac


def add_line_with_arrow(
    p,
    x0,
    y0,
    x1,
    y1,
    line_dash="solid",
    line_width=1.5,
    line_color="black",
):
    p.line(
        [x0, x1],
        [y0, y1],
        line_color=line_color,
        line_width=line_width,
        line_dash=line_dash,
    )

    tail_frac = 0.90
    head_frac = 0.975

    xt = date_interp(x0, x1, tail_frac)
    xh = date_interp(x0, x1, head_frac)
    yt = log_interp(y0, y1, tail_frac)
    yh = log_interp(y0, y1, head_frac)

    p.add_layout(
        Arrow(
            end=NormalHead(
                size=10,
                fill_color=line_color,
                line_color=line_color,
            ),
            x_start=xt,
            y_start=yt,
            x_end=xh,
            y_end=yh,
            line_color=line_color,
            line_width=line_width,
        )
    )


# ============================================================
# DATES
# ============================================================

halvings = [
    datetime(2012, 11, 28),
    datetime(2016, 7, 9),
    datetime(2020, 5, 11),
    datetime(2024, 4, 19),
    datetime(2028, 3, 31),
]

mid_halvings = [
    halvings[i] + (halvings[i + 1] - halvings[i]) / 2
    for i in range(len(halvings) - 1)
]


# ============================================================
# LOAD PRICE
# ============================================================

url_price = (
    "https://api.blockchain.info/charts/market-price?"
    "timespan=18years&rollingAverage=24hours"
    "&start=2010-01-01"
    "&format=json"
    "&sampled=false"
)

print("Downloading Bitcoin price data...")

df = fetch_and_process(url_price, "Price")
df = df[df["Price"] > 0].copy()

# ============================================================
# LAST DATA DATE
# ============================================================

last_data_date = df.index.max().strftime("%Y-%m-%d")
print("Data through:", last_data_date)


# ============================================================
# FIND CYCLE MAXIMA
# ============================================================

print("Finding cycle maxima...")

max_values = []

for i in range(len(halvings)):
    start_date = df.index[0] if i == 0 else halvings[i - 1]
    end_date = halvings[i]
    reduced_end = end_date - timedelta(days=60)

    subset = df[
        (df.index >= start_date) &
        (df.index <= reduced_end)
    ]

    max_value = subset["Price"].max()
    max_date = subset["Price"].idxmax()

    max_values.append(
        (
            start_date,
            end_date,
            max_date,
            max_value,
        )
    )


# ============================================================
# CREATE BOKEH FIGURE
# ============================================================

print("Creating Bokeh figure...")

end_prediction = datetime(2030, 5, 1)
today = datetime.today()

x_start = df.index[0]
x_end = end_prediction
y_start = 0.1
y_end = 600_000

pan_tool = PanTool()
wheel_zoom_tool = WheelZoomTool()
box_zoom_tool = BoxZoomTool()
reset_tool = ResetTool()
save_tool = SaveTool()

p = figure(
    title="Bitcoin Cycle Prediction",
    sizing_mode="stretch_width",
    height=700,

    x_axis_type="datetime",
    y_axis_type="log",

    tools=[
        pan_tool,
        wheel_zoom_tool,
        box_zoom_tool,
        reset_tool,
        save_tool,
    ],

    active_scroll=wheel_zoom_tool,
    active_drag=box_zoom_tool,

    x_range=(x_start, x_end),
    y_range=(y_start, y_end),
)

p.toolbar.logo = None
p.toolbar_location = None

p.title.align = "center"
p.title.text_font_size = "24pt"

p.xaxis.axis_label = "Date"
p.yaxis.axis_label = "USD"

# Larger axis labels
p.xaxis.axis_label_text_font_size = "20pt"
p.yaxis.axis_label_text_font_size = "20pt"

# Larger tick numbers
p.xaxis.major_label_text_font_size = "16pt"
p.yaxis.major_label_text_font_size = "16pt"

p.yaxis.formatter = NumeralTickFormatter(format="0,0.[0]")

p.yaxis.ticker = FixedTicker(ticks=[
    0.1,
    1,
    10,
    100,
    1000,
    10000,
    100000,
    500000,
])

p.grid.grid_line_alpha = 0.35

# ============================================================
# PRICE LINE
# ============================================================

source_price = ColumnDataSource(
    data=dict(
        Date=df.index,
        Price=df["Price"],
    )
)

price_line = p.line(
    "Date",
    "Price",
    source=source_price,
    line_color="royalblue",
    line_width=2,
    legend_label="Price",
)
# ============================================================
# HOVER TOOL
# Works everywhere in the figure
# ============================================================
# ============================================================
# HOVER TOOL
# Shows cursor Date and USD anywhere in the visible plot
# Works also after zoom
# ============================================================

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

# # Invisible hover line so tooltip works even when cursor is not exactly on price line
# hover_source = ColumnDataSource(
#     data=dict(
#         Date=df.index,
#         Price=df["Price"],
#     )
# )
#
# hover_line = p.line(
#     "Date",
#     "Price",
#     source=hover_source,
#     line_alpha=0,
#     line_width=40,
# )
#
# ============================================================
# PREDICTION REGION
# ============================================================

p.add_layout(
    BoxAnnotation(
        left=today,
        right=end_prediction,
        fill_color="gray",
        fill_alpha=0.08,
    )
)

p.add_layout(
    Span(
        location=today,
        dimension="height",
        line_color="black",
        line_dash="dashed",
        line_width=1.5,
        line_alpha=0.7,
    )
)

p.add_layout(
    Label(
        x=today,
        y=1.25,
        text="Today",
        angle=math.pi / 2,
        text_font_size="11pt",
    )
)

p.add_layout(
    Label(
        #x=today + (end_prediction - today) / 2,
        x=today + timedelta(days=120),
        y=3000,
        text="Prediction Region",
        text_font_size="22pt",
        text_color="gray",
        text_alpha=0.45,
    )
)


# ============================================================
# HALVING AND MID HALVING LINES
# ============================================================

for i, d in enumerate(halvings, 1):
    p.add_layout(
        Span(
            location=d,
            dimension="height",
            line_color="red",
            line_width=2,
            line_alpha=0.6,
        )
    )

    p.add_layout(
        Label(
            x=d,
            y=0.35,
            text=f"Halving {i}",
            angle=math.pi / 2,
            text_font_size="10pt",
        )
    )


for i, d in enumerate(mid_halvings, 1):
    p.add_layout(
        Span(
            location=d,
            dimension="height",
            line_color="red",
            line_dash="dashed",
            line_width=1.5,
            line_alpha=0.45,
        )
    )

    p.add_layout(
        Label(
            x=d,
            y=0.35,
            text="mid",
            angle=math.pi / 2,
            text_font_size="10pt",
        )
    )


# ============================================================
# MAIN CYCLE LOGIC
# ============================================================

prev_min = None
prev_min_date = None

print("\n" + "#" * 80)
print("NUMERICAL RESULTS")
print("#" * 80)

down_rows = []
up_rows = []
future_bottom_rows = []
future_top_rows = []

for i, (start_date, end_date, max_date, max_value) in enumerate(max_values):

    subset = df[
        (df.index >= max_date) &
        (df.index <= end_date)
    ]

    min_value = subset["Price"].min()
    min_date = subset["Price"].idxmin()

    print("\n" + "=" * 70)
    print(f"Cycle {i + 1}")
    print(f"Max date: {max_date.date()}")
    print(f"Max price: ${max_value:,.2f}")
    print(f"Min date after max: {min_date.date()}")
    print(f"Min price after max: ${min_value:,.2f}")

    p.circle(
        [max_date],
        [max_value],
        size=9,
        color="red",
        legend_label="Cycle Max",
    )

    if i < 4:

        p.scatter(
            [min_date],
            [min_value],
            size=12,
            marker="x",
            color="blue",
            line_width=3,
            legend_label="Cycle Min",
        )

        add_line_with_arrow(
            p,
            max_date,
            max_value,
            min_date,
            min_value,
            line_color="red",
        )

        growth_down = (
            (min_value / max_value)
            ** (1 / ((min_date - max_date).days / 365.25))
            - 1
        ) * 100

        print(f"Down rate: {growth_down:.2f}%/year")

        down_ratio = max_value / min_value
        drawdown_pct = (min_value / max_value - 1) * 100

        down_rows.append({
            "cycle": f"Cycle {i + 1}",
            "top_date": max_date.strftime("%Y-%m-%d"),
            "top_price": max_value,
            "bottom_date": min_date.strftime("%Y-%m-%d"),
            "bottom_price": min_value,
            "drawdown_pct": drawdown_pct,
            "top_to_bottom": down_ratio,
            "annual_rate": growth_down,
        })

        p.add_layout(
            Label(
                x=min_date - timedelta(days=35),
                y=min_value * 0.55,
                text=f"{growth_down:.1f}%/y",
                text_font_size="13pt",
                background_fill_color="white",
                background_fill_alpha=0.75,
            )
        )

    if i > 0 and prev_min is not None:

        add_line_with_arrow(
            p,
            prev_min_date,
            prev_min,
            max_date,
            max_value,
            line_color="green",
        )

        growth_up = (
            (max_value / prev_min)
            ** (1 / ((max_date - prev_min_date).days / 365.25))
            - 1
        ) * 100

        print(f"Up rate: {growth_up:.2f}%/year")

        up_multiple = max_value / prev_min

        up_rows.append({
            "cycle": f"Cycle {i + 1}",
            "bottom_date": prev_min_date.strftime("%Y-%m-%d"),
            "bottom_price": prev_min,
            "top_date": max_date.strftime("%Y-%m-%d"),
            "top_price": max_value,
            "multiple": up_multiple,
            "annual_rate": growth_up,
        })

        p.add_layout(
            Label(
                x=max_date - timedelta(days=45),
                y=max_value * 1.10,
                text=f"{growth_up:+.1f}%/y",
                text_font_size="13pt",
                background_fill_color="white",
                background_fill_alpha=0.75,
            )
        )

    if i == 4:

        min_date_pred = max_date + timedelta(days=350)

        bottom_preds = [
            max_value / 2.41,
            max_value / 3.17,
            max_value / 4.68,
        ]

        print("\nFuture bottom predictions:")

        for k, mv in enumerate(bottom_preds, 1):

            rate = (
                (mv / max_value)
                ** (1 / ((min_date_pred - max_date).days / 365.25))
                - 1
            ) * 100

            print(
                f"Bottom {k}: ${mv:,.2f}, "
                f"rate {rate:.2f}%/year"
            )

            future_bottom_rows.append({
                "scenario": f"Bottom {k}",
                "date": min_date_pred.strftime("%Y-%m-%d"),
                "price": mv,
                "top_to_bottom": max_value / mv,
                "annual_rate": rate,
            })

            p.circle(
                [min_date_pred],
                [mv],
                size=12,
                fill_color="white",
                line_color="green",
                line_width=2,
            )

            add_line_with_arrow(
                p,
                max_date,
                max_value,
                min_date_pred,
                mv,
                line_dash="dotted",
                line_width=1.2,
                line_color="red",
            )
            # Separate the prediction labels vertically
            # Separate the prediction labels vertically
            y_text = mv

            if k == 1:  # first label
                y_text = mv * 1.06

            elif k == 2:  # second label
                y_text = mv * 0.80

            elif k == 3:  # third label
                y_text = mv * 0.70

            p.add_layout(
                Label(
                    x=min_date_pred + timedelta(days=30),
                    y=y_text,
                    text=f"{rate:.0f}%/y",
                    text_font_size="13pt",
                    background_fill_color="white",
                    background_fill_alpha=0.75,
                )
            )
            # p.add_layout(
            #     Label(
            #         x=min_date_pred + timedelta(days=60),
            #         y=mv,
            #         text=f"{rate:.0f}%/y",
            #         text_font_size="13pt",
            #         background_fill_color="white",
            #         background_fill_alpha=0.75,
            #     )
            # )

        up_days = 1000
        up_date_pred = min_date_pred + timedelta(days=up_days)

        annual_growths = [2.20, 2.00, 1.80]

        up_preds = [
            bottom_preds[1] * (g ** (up_days / 365.25))
            for g in annual_growths
        ]

        print("\nFuture top predictions:")

        for k, mv in enumerate(up_preds, 1):

            rate = (
                (mv / bottom_preds[1])
                ** (1 / (up_days / 365.25))
                - 1
            ) * 100

            print(
                f"Top {k}: ${mv:,.2f}, "
                f"rate {rate:.2f}%/year"
            )

            future_top_rows.append({
                "scenario": f"Top {k}",
                "date": up_date_pred.strftime("%Y-%m-%d"),
                "price": mv,
                "bottom_price": bottom_preds[1],
                "multiple": mv / bottom_preds[1],
                "annual_rate": rate,
            })

            p.circle(
                [up_date_pred],
                [mv],
                size=12,
                fill_color="white",
                line_color="green",
                line_width=2,
            )

            add_line_with_arrow(
                p,
                min_date_pred,
                bottom_preds[1],
                up_date_pred,
                mv,
                line_dash="dotted",
                line_width=1.2,
                line_color="green",
            )

            # Separate the upper prediction labels vertically
            y_text = mv

            if k == 1:  # +120%
                y_text = mv * 1.03

            elif k == 2:  # +100%
                y_text = mv * 0.85

            elif k == 3:  # +80%
                y_text = mv * 0.70

            p.add_layout(
                Label(
                    x=up_date_pred + timedelta(days=30),
                    y=y_text,
                    text=f"{rate:+.0f}%/y",
                    text_font_size="13pt",
                    background_fill_color="white",
                    background_fill_alpha=0.75,
                )
            )

    prev_min = min_value
    prev_min_date = min_date


p.legend.location = "top_left"
p.legend.background_fill_alpha = 0.7
p.legend.click_policy = "hide"


# ============================================================
# BIG MOBILE AND DESKTOP BUTTONS
# ============================================================
# ============================================================
# HUGE MOBILE + DESKTOP BUTTONS
# ============================================================
# ============================================================
# HUGE MOBILE + DESKTOP BUTTONS
# ============================================================
# ============================================================
# HUGE MOBILE + DESKTOP BUTTONS
# ============================================================

button_style = Div(
    text="""
    <style>
    .big-control-button button {
        width: 240px !important;
        height: 160px !important;
        border-radius: 18px !important;
        margin: 6px !important;
        font-size: 44px !important;
        font-weight: bold !important;
    }

    @media (max-width: 700px) {
        .big-control-button button {
            width: 190px !important;
            height: 140px !important;
            font-size: 32px !important;
        }
    }
    </style>
    """,
    sizing_mode="stretch_width",
)

# ============================================================
# BUTTONS
# ============================================================

zoom_in_button = Button(
    label="ZOOM +",
    button_type="success",
    css_classes=["big-control-button"],
    styles={'font-size': '44px', 'font-weight': 'bold'}
)

zoom_out_button = Button(
    label="ZOOM −",
    button_type="warning",
    css_classes=["big-control-button"],
    styles={'font-size': '44px', 'font-weight': 'bold'}
)

box_zoom_button = Button(
    label="BOX ZOOM",
    button_type="primary",
    css_classes=["big-control-button"],
    styles={'font-size': '44px', 'font-weight': 'bold'}
)

pan_button = Button(
    label="PAN",
    button_type="primary",
    css_classes=["big-control-button"],
    styles={'font-size': '44px', 'font-weight': 'bold'}
)

home_button = Button(
    label="HOME",
    button_type="danger",
    css_classes=["big-control-button"],
    styles={'font-size': '44px', 'font-weight': 'bold'}
)
# ============================================================
# BUTTON ACTIONS
# ============================================================

zoom_in_button.js_on_click(
    CustomJS(
        args=dict(
            xr=p.x_range,
            yr=p.y_range
        ),
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

        yr.start = Math.pow(
            10,
            log_mid - log_range / 2.0
        );

        yr.end = Math.pow(
            10,
            log_mid + log_range / 2.0
        );

        xr.change.emit();
        yr.change.emit();
        """
    )
)

zoom_out_button.js_on_click(
    CustomJS(
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

        yr.start = Math.pow(
            10,
            log_mid - log_range / 2.0
        );

        yr.end = Math.pow(
            10,
            log_mid + log_range / 2.0
        );

        if (xr.start < x0)
            xr.start = x0;

        if (xr.end > x1)
            xr.end = x1;

        if (yr.start < y0)
            yr.start = y0;

        if (yr.end > y1)
            yr.end = y1;

        xr.change.emit();
        yr.change.emit();
        """
    )
)

box_zoom_button.js_on_click(
    CustomJS(
        args=dict(
            plot=p,
            box_zoom_tool=box_zoom_tool
        ),
        code="""
        plot.toolbar.active_drag =
            box_zoom_tool;
        """
    )
)

pan_button.js_on_click(
    CustomJS(
        args=dict(
            plot=p,
            pan_tool=pan_tool
        ),
        code="""
        plot.toolbar.active_drag =
            pan_tool;
        """
    )
)

home_button.js_on_click(
    CustomJS(
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
    )
)

# ============================================================
# CONTROLS LAYOUT
# ============================================================

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


# ============================================================
# BUILD EXPLANATION TABLES
# ============================================================

def fmt_money(x):
    return f"${x:,.0f}"


def fmt_pct(x):
    return f"{x:+.1f}%"


def fmt_mult(x):
    return f"{x:.2f}x"


def make_down_table(rows):
    html = """
    <table class="prediction-table">
        <thead>
            <tr>
                <th>Cycle</th>
                <th>Top date</th>
                <th>Top price</th>
                <th>Bottom date</th>
                <th>Bottom price</th>
                <th>Drawdown</th>
                <th>Top / Bottom</th>
            </tr>
        </thead>
        <tbody>
    """

    for r in rows:
        html += f"""
            <tr>
                <td>{r["cycle"]}</td>
                <td>{r["top_date"]}</td>
                <td>{fmt_money(r["top_price"])}</td>
                <td>{r["bottom_date"]}</td>
                <td>{fmt_money(r["bottom_price"])}</td>
                <td>{fmt_pct(r["drawdown_pct"])}</td>
                <td>{fmt_mult(r["top_to_bottom"])}</td>
            </tr>
        """

    html += """
        </tbody>
    </table>
    """

    return html


def make_up_table(rows):
    html = """
    <table class="prediction-table">
        <thead>
            <tr>
                <th>Cycle</th>
                <th>Bottom date</th>
                <th>Bottom price</th>
                <th>Top date</th>
                <th>Top price</th>
                <th>Bottom → Top</th>
                <th>Annual rate</th>
            </tr>
        </thead>
        <tbody>
    """

    for r in rows:
        html += f"""
            <tr>
                <td>{r["cycle"]}</td>
                <td>{r["bottom_date"]}</td>
                <td>{fmt_money(r["bottom_price"])}</td>
                <td>{r["top_date"]}</td>
                <td>{fmt_money(r["top_price"])}</td>
                <td>{fmt_mult(r["multiple"])}</td>
                <td>{fmt_pct(r["annual_rate"])}</td>
            </tr>
        """

    html += """
        </tbody>
    </table>
    """

    return html


def make_future_bottom_table(rows):
    html = """
    <table class="prediction-table">
        <thead>
            <tr>
                <th>Scenario</th>
                <th>Predicted date</th>
                <th>Predicted bottom</th>
                <th>Top / Bottom</th>
                <th>Annual decline</th>
            </tr>
        </thead>
        <tbody>
    """

    for r in rows:
        html += f"""
            <tr>
                <td>{r["scenario"]}</td>
                <td>{r["date"]}</td>
                <td>{fmt_money(r["price"])}</td>
                <td>{fmt_mult(r["top_to_bottom"])}</td>
                <td>{fmt_pct(r["annual_rate"])}</td>
            </tr>
        """

    html += """
        </tbody>
    </table>
    """

    return html


def make_future_top_table(rows):
    html = """
    <table class="prediction-table">
        <thead>
            <tr>
                <th>Scenario</th>
                <th>Predicted date</th>
                <th>Starting bottom</th>
                <th>Predicted top</th>
                <th>Bottom → Top</th>
                <th>Annual growth</th>
            </tr>
        </thead>
        <tbody>
    """

    for r in rows:
        html += f"""
            <tr>
                <td>{r["scenario"]}</td>
                <td>{r["date"]}</td>
                <td>{fmt_money(r["bottom_price"])}</td>
                <td>{fmt_money(r["price"])}</td>
                <td>{fmt_mult(r["multiple"])}</td>
                <td>{fmt_pct(r["annual_rate"])}</td>
            </tr>
        """

    html += """
        </tbody>
    </table>
    """

    return html


down_table_html = make_down_table(down_rows)
up_table_html = make_up_table(up_rows)
future_bottom_table_html = make_future_bottom_table(future_bottom_rows)
future_top_table_html = make_future_top_table(future_top_rows)

# ============================================================
# SIMPLE FULL-WIDTH RESPONSIVE EXPLANATION
# ============================================================

explanation = Div(
    text=f"""
    <style>

    .analysis-wrapper {{
        width: 100%;
        box-sizing: border-box;
        margin-top: 35px;
        margin-bottom: 40px;

        background:
            linear-gradient(
                135deg,
                #081224 0%,
                #0b132b 45%,
                #111827 100%
            );

        border-radius: 22px;
        padding: 28px;
        color: white;

        box-shadow:
            0 10px 35px rgba(0,0,0,0.30);

        overflow-x: hidden;
        font-family: Arial, sans-serif;
    }}

    .analysis-title {{
        text-align: center;
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 20px;
        color: white;
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

        border-top:
            1px solid rgba(255,255,255,0.15);

        padding-top: 28px;
    }}

    .analysis-box {{
        background:
            rgba(255,255,255,0.04);

        border:
            1px solid rgba(255,255,255,0.08);

        border-radius: 18px;
        padding: 24px;
        backdrop-filter: blur(8px);
    }}

    .analysis-box h3 {{
        margin-top: 0;
        margin-bottom: 18px;
        font-size: 28px;
        color: #38bdf8;
    }}

    .analysis-box ul {{
        margin: 0;
        padding-left: 22px;
        line-height: 1.9;
        font-size: 18px;
        color: #e5e7eb;
    }}

    .analysis-box li {{
        margin-bottom: 10px;
    }}

    .analysis-box p {{
        line-height: 1.9;
        font-size: 18px;
        color: #e5e7eb;
    }}

    .wide-box {{
        margin-top: 28px;
        background:
            rgba(255,255,255,0.04);

        border:
            1px solid rgba(255,255,255,0.08);

        border-radius: 18px;
        padding: 24px;
    }}

    .wide-box h3 {{
        margin-top: 0;
        font-size: 30px;
        color: #facc15;
    }}

    .wide-box p {{
        line-height: 1.9;
        font-size: 18px;
        color: #e5e7eb;
    }}

    .table-wrapper {{
        width: 100%;
        overflow-x: auto;
        margin: 18px 0 26px 0;
    }}

    .prediction-table {{
        width: 100%;
        border-collapse: collapse;
        min-width: 760px;
        font-size: 16px;
        color: #e5e7eb;
        background: rgba(255,255,255,0.03);
    }}

    .prediction-table th {{
        background: rgba(56,189,248,0.18);
        color: #ffffff;
        padding: 12px;
        text-align: left;
        border-bottom: 1px solid rgba(255,255,255,0.18);
        white-space: nowrap;
    }}

    .prediction-table td {{
        padding: 11px 12px;
        border-bottom: 1px solid rgba(255,255,255,0.10);
        white-space: nowrap;
    }}

    .prediction-table tr:hover {{
        background: rgba(255,255,255,0.06);
    }}

    .green-text {{
        color: #22c55e;
        font-weight: bold;
    }}

    .red-text {{
        color: #ef4444;
        font-weight: bold;
    }}

    .blue-text {{
        color: #60a5fa;
        font-weight: bold;
    }}

    .footer-note {{
        margin-top: 28px;
        padding-top: 18px;
        border-top:
            1px solid rgba(255,255,255,0.15);
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
            padding: 18px;
            border-radius: 16px;
        }}

        .analysis-title {{
            font-size: 30px;
            line-height: 1.3;
        }}

        .analysis-subtitle {{
            font-size: 17px;
            line-height: 1.7;
        }}

        .analysis-grid {{
            grid-template-columns: 1fr;
            gap: 18px;
        }}

        .analysis-box,
        .wide-box {{
            padding: 18px;
        }}

        .analysis-box h3,
        .wide-box h3 {{
            font-size: 24px;
        }}

        .analysis-box ul,
        .analysis-box p,
        .wide-box p {{
            font-size: 16px;
            line-height: 1.8;
        }}

        .prediction-table {{
            font-size: 14px;
            min-width: 680px;
        }}

        .footer-note {{
            font-size: 13px;
        }}
    }}

    </style>

    <div class="analysis-wrapper">

        <div class="analysis-title">
            📊 Bitcoin Cycle Prediction
        </div>


        <div class="analysis-subtitle">

        <div style="
            font-size:18px;
            color:#93c5fd;
            margin-bottom:14px;
            font-weight:bold;
        ">
            Bitcoin price data through: {last_data_date}
        </div>

        This interactive chart analyzes
        <strong>Bitcoin's historical price cycles</strong>
        and projects possible future movements using the same logic
        described in the book: halvings reduce new supply, the upward
        phase tends to last several years, and very large price increases
        are often followed by a shorter correction.

    </div>

        <div class="analysis-grid">

            <div class="analysis-box">

                <h3>🔍 What the Figure Shows</h3>

                <ul>
                    <li>
                        <span style="color:#ef4444;">
                        Red vertical lines
                        </span>
                        mark halving events.
                    </li>

                    <li>
                        <span style="color:#ef4444;">
                        Red circles
                        </span>
                        indicate historical cycle peaks.
                    </li>

                    <li>
                        <span style="color:#60a5fa;">
                        Blue X markers
                        </span>
                        show historical cycle bottoms.
                    </li>

                    <li>
                        Green arrows show upward cycle movements, and red arrows show downward corrections.
                    </li>

                    <li>
                        <span style="color:#22c55e;">
                        Green circles
                        </span>
                        show possible future scenarios.
                    </li>
                </ul>

            </div>

            <div class="analysis-box">

                <h3>📘 Book Logic</h3>

                <p>
                    The prediction follows two central ideas from the book.
                    First, the mining reward is the main source of new Bitcoin
                    supply. Every halving cuts that flow in half, which may
                    create upward pressure if demand remains strong.
                </p>

                <p>
                    Second, mining cost tends to follow Bitcoin price. When the
                    price rises too much, the implied mining cost becomes very
                    large and may create pressure for a correction.
                </p>

            </div>

            <div class="analysis-box">

                <h3>🧭 Prediction Steps</h3>

                <ul>
                    <li>
                        Step 1: find each cycle top before the next halving.
                    </li>

                    <li>
                        Step 2: find the following bottom after each top.
                    </li>

                    <li>
                        Step 3: estimate possible future bottoms using
                        historical top-to-bottom decline ratios.
                    </li>

                    <li>
                        Step 4: estimate possible future tops using annual
                        growth scenarios that reflect diminishing returns.
                    </li>
                </ul>

            </div>

        </div>

        <div class="wide-box">
            <h3>1. Historical Downward Phases</h3>

            <p>
                This table shows how much Bitcoin declined from each historical
                cycle top to the following cycle bottom. These declines are used
                to choose possible future bottom scenarios.
            </p>

            <div class="table-wrapper">
                {down_table_html}
            </div>
        </div>

        <div class="wide-box">
            <h3>2. Historical Upward Phases</h3>

            <p>
                This table shows the rise from each cycle bottom to the next
                cycle top. The general pattern is that the percentage gains
                become smaller over time, which is the diminishing-returns
                effect discussed in the book.
            </p>

            <div class="table-wrapper">
                {up_table_html}
            </div>
        </div>

        <div class="wide-box">
            <h3>3. Future Bottom Scenarios</h3>

            <p>
                The future bottom is estimated by applying several historical
                top-to-bottom decline ratios to the current projected cycle top.
                The dotted downward lines in the chart correspond to these
                scenarios.
            </p>

            <div class="table-wrapper">
                {future_bottom_table_html}
            </div>
        </div>

        <div class="wide-box">
            <h3>4. Future Top Scenarios</h3>

            <p>
                After a possible bottom is selected, the next top is projected
                using several annual growth assumptions. These assumptions are
                intentionally lower than the early Bitcoin cycles because the
                book argues that Bitcoin exhibits diminishing returns as the
                market becomes larger.
            </p>

            <div class="table-wrapper">
                {future_top_table_html}
            </div>
        </div>

        <div class="footer-note">

            <strong>⚠ Disclaimer:</strong>
            This analysis is for educational purposes only and is not financial advice.
            The cycle may break because of regulation, demand collapse,
            macroeconomic shocks, technological risks, or black swan events.

        </div>

    </div>
    """,
    sizing_mode="stretch_width",
)
# ============================================================
# RESPONSIVE PAGE STYLE
# ============================================================

page_style = Div(
    text="""
    <style>

    /* Desktop: figure centered with margins,
         explanation stretches full width */
    @media (min-width: 901px) {

        .main-page {
            width: 100% !important;
            max-width: 100% !important;
        }
    
        /* Figure area */
        .bk-plot-layout {
            max-width: 1250px !important;
            width: 92% !important;
            margin-left: auto !important;
            margin-right: auto !important;
        }
    
        /* Bottom text stretches */
        .explanation-container {
            width: 96% !important;
            max-width: 96% !important;
            margin: 40px auto 60px auto !important;
        }
    }

    /* Mobile: keep full width */
    @media (max-width: 900px) {
        .main-page {
            width: 100% !important;
            max-width: 100% !important;
        }
    }

    </style>
    """,
    sizing_mode="stretch_width",
)

# ============================================================
# FINAL LAYOUT
# ============================================================

layout = column(
    page_style,
    controls,
    p,
    explanation,

    sizing_mode="stretch_width",
    css_classes=["main-page"],
)


# # ============================================================
# # RESPONSIVE FIGURE WRAPPER
# # ============================================================
#
# # Wrap the figure in a responsive container
# figure_wrapper = Div(
#     text="""
#     <style>
#     /* Desktop: Limit figure width and center it */
#     @media (min-width: 701px) {
#         .bk-root > .bk-layout-row > .bk-layout-column {
#             max-width: 85% !important;
#             margin: 0 auto !important;
#         }
#     }
#
#     /* Mobile: Keep full width */
#     @media (max-width: 700px) {
#         .bk-root > .bk-layout-row > .bk-layout-column {
#             max-width: 100% !important;
#         }
#     }
#     </style>
#     """,
#     sizing_mode="stretch_width",
# )
#
# # ============================================================
# # FINAL LAYOUT
# # ============================================================
#
# layout = column(
#     figure_wrapper,  # Responsive CSS wrapper
#     controls,
#     p,
#     explanation,
#     sizing_mode="stretch_width",
# )
#
# # ============================================================
# # FINAL LAYOUT
# # ============================================================
#
# layout = column(
#     controls,
#     p,
#
#     sizing_mode="stretch_width",
# )



# # ============================================================
# # SAVE HTML
# # ============================================================
#
# os.makedirs("site", exist_ok=True)
#
# output_file(
#     "site/index.html",
#     title="Bitcoin Cycle Prediction",
# )
#
# save(layout)
#
# print("\nSaved: site/index.html")
#
# show(layout)


# ============================================================
# SAVE HTML
# ============================================================

os.makedirs("figures", exist_ok=True)

output_file(
    "figures/f_pred.html",
    title="Bitcoin Cycle Prediction",
)

save(layout)

print("\nSaved: figures/f_pred.html")

show(layout)

print("DONE!")


# ============================================================
# GIT PUSH
# ============================================================

def run(cmd):
    print(" ".join(cmd))
    return subprocess.run(cmd, check=True)


def git_push():
    from github_publish import publish_to_github

    publish_to_github(
        add_paths=["index.html", ".nojekyll", "figures", "book", "images"],
        message=f"update website {datetime.now()}",
        log_file="run_log.txt",
    )


if os.environ.get("SKIP_GITHUB_PUSH") == "1":
    print("Skipping per-script GitHub push; runner will publish once at the end.")
else:
    git_push()
print("DONE!")
