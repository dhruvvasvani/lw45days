from __future__ import annotations

from io import BytesIO

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from backend.forecasting import add_inventory_projection, run_forecast
from backend.preprocessing import (
    get_sales_csv_columns,
    guess_sales_columns,
    load_sales_csv,
)

st.set_page_config(
    page_title="Sales Forecast AI",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp { background: #f4f7fb; }
    [data-testid="stSidebar"] { background: #101b32; }
    [data-testid="stSidebar"] * { color: #edf3ff; }
    .hero {
        padding: 1.7rem 2rem;
        margin: 0 0 1.2rem;
        border-radius: 18px;
        color: #f8fbff;
        background: linear-gradient(115deg, #142747 0%, #2455a4 62%, #22a8a1 100%);
    }
    .hero h1 { margin: 0; font-size: 2rem; }
    .hero p { margin: .45rem 0 0; color: #d7e5ff; }
    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e3eaf3;
        border-radius: 14px;
        padding: 1rem 1.1rem;
        box-shadow: 0 5px 16px rgba(20, 39, 71, .04);
    }
    div[data-testid="stMetric"] label { color: #5e6d82; }
    h2, h3 { color: #142747; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def make_demo_data() -> pd.DataFrame:
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=180, freq="D")
    day = np.arange(len(dates))
    weekly_pattern = np.array([3, 5, 6, 8, 12, 18, 14])[day % 7]
    sales = (
        72
        + 0.14 * day
        + weekly_pattern
        + 5 * np.sin(2 * np.pi * day / 30)
        + 2.5 * np.sin(2 * np.pi * day / 11)
    )
    sales = np.maximum(np.round(sales), 1)
    return pd.DataFrame({"Date": dates, "Sales": sales})


def chart_layout(fig: go.Figure, height: int = 380) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=12, r=12, t=48, b=12),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#34445c"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False, linecolor="#e8edf4")
    fig.update_yaxes(gridcolor="#edf1f6", zeroline=False)
    return fig


st.markdown(
    """
    <div class="hero">
      <h1>Sales Forecast AI</h1>
      <p>Demand forecasting and inventory intelligence for your daily sales data</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.title("Forecast setup")
    data_source = st.radio(
        "Choose your data",
        ["Try demo data", "Upload a CSV"],
        help="The demo dataset is synthetic and included so you can explore the dashboard immediately.",
    )
    uploaded_file = None
    uploaded_bytes = None
    selected_date_column = None
    selected_sales_column = None
    if data_source == "Upload a CSV":
        uploaded_file = st.file_uploader(
            "Upload daily sales",
            type=["csv"],
            help=(
                "Required: one date column and one numeric demand column. "
                "Column names such as dteday and cnt are detected automatically; "
                "you can select any columns below."
            ),
        )
        st.caption(
            "**Required columns:** date + numeric demand (sales, quantity, units, "
            "revenue, or similar). **One row per day** is recommended."
        )
        template_csv = make_demo_data().to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download CSV template",
            data=template_csv,
            file_name="sales_forecast_template.csv",
            mime="text/csv",
            help="Includes 180 sample daily rows. Replace the sample values with your own.",
        )
        if uploaded_file is not None:
            uploaded_bytes = uploaded_file.getvalue()
            try:
                csv_columns = get_sales_csv_columns(uploaded_bytes)
            except ValueError as exc:
                st.error(str(exc))
                st.stop()
            guessed_date, guessed_sales = guess_sales_columns(csv_columns)
            st.markdown("**Map your CSV columns**")
            selected_date_column = st.selectbox(
                "Date column",
                options=csv_columns,
                index=(
                    csv_columns.index(guessed_date)
                    if guessed_date in csv_columns
                    else 0
                ),
                key="uploaded_date_column",
                help="The column containing a date for each record.",
            )
            selected_sales_column = st.selectbox(
                "Demand / sales column",
                options=csv_columns,
                index=(
                    csv_columns.index(guessed_sales)
                    if guessed_sales in csv_columns
                    else min(1, len(csv_columns) - 1)
                ),
                key="uploaded_sales_column",
                help="A numeric quantity to forecast, such as sales, demand, units, or cnt.",
            )
    forecast_horizon = st.slider("Forecast horizon (days)", 7, 90, 30)
    seasonal_period = st.selectbox(
        "Seasonal period (days)",
        options=[7, 14, 30],
        index=0,
        help="Choose the number of daily observations in one repeating seasonal cycle.",
    )
    st.caption(
        "Holt-Winters additive trend + seasonality. Accuracy is measured on a "
        "chronological holdout from the uploaded history."
    )

try:
    if data_source == "Try demo data":
        data = make_demo_data()
        sales, data_notes = load_sales_csv(data.to_csv(index=False).encode("utf-8"))
        st.info("Demo mode: results below use synthetic sample sales, not your business data.")
    elif uploaded_bytes is not None:
        sales, data_notes = load_sales_csv(
            uploaded_bytes,
            date_column=selected_date_column,
            sales_column=selected_sales_column,
        )
    else:
        st.info("Upload a CSV to get started, or choose **Try demo data** in the sidebar.")
        st.stop()

    for note in data_notes:
        st.warning(note)

    with st.sidebar:
        st.divider()
        available_stock = st.number_input(
            "Current available stock (units, optional)",
            min_value=0.0,
            value=0.0,
            step=10.0,
            help="Enter stock on hand to estimate whether it covers demand over the selected forecast horizon. Leave at zero to skip.",
        )
        use_inventory = st.checkbox("Include inventory analysis", value=False)

    results = run_forecast(sales, forecast_horizon, seasonal_period)
    stock_value = available_stock if use_inventory else None
    projected_forecast, inventory_status = add_inventory_projection(
        results["forecast"], stock_value
    )
except ValueError as exc:
    st.error(str(exc))
    st.stop()

st.subheader("At a glance")
metrics = st.columns(4)
metrics[0].metric("History", f"{len(sales):,} days")
metrics[1].metric("Forecast", f"{forecast_horizon} days")
metrics[2].metric("Holdout MAE", f"{results['mae']:.2f} units")
metrics[3].metric("Holdout RMSE", f"{results['rmse']:.2f} units")
st.caption(
    f"Data range: {sales.index.min():%b %d, %Y} – {sales.index.max():%b %d, %Y} "
    f"· Accuracy tested on the most recent {results['test_size']} historical days."
)

st.subheader("Demand forecast")
history_window = sales.iloc[-min(len(sales), 90) :]
fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=history_window.index,
        y=history_window.values,
        mode="lines",
        name="Historical sales",
        line=dict(color="#355caa", width=2),
    )
)
evaluation = results["evaluation"]
fig.add_trace(
    go.Scatter(
        x=evaluation.index,
        y=evaluation["Actual"],
        mode="lines",
        name="Holdout actual",
        line=dict(color="#149b8a", width=2),
    )
)
fig.add_trace(
    go.Scatter(
        x=evaluation.index,
        y=evaluation["Predicted"],
        mode="lines",
        name="Holdout forecast",
        line=dict(color="#ee9b35", width=2, dash="dash"),
    )
)
fig.add_trace(
    go.Scatter(
        x=projected_forecast.index,
        y=projected_forecast["Forecast"],
        mode="lines",
        name="Future forecast",
        line=dict(color="#d65367", width=3),
    )
)
fig.add_vline(
    x=sales.index[-1],
    line_width=1,
    line_dash="dot",
    line_color="#7c8798",
    annotation_text="Forecast starts",
)
fig.update_layout(title="Historical demand and future forecast", yaxis_title="Units sold")
st.plotly_chart(chart_layout(fig), width="stretch")

left, right = st.columns([1.2, 1])
with left:
    st.subheader("Model validation")
    st.write(
        "The model is tested on the latest historical period it did not train on. "
        "MAE and RMSE are in sales units; lower values indicate smaller errors."
    )
    validation_fig = go.Figure()
    validation_fig.add_trace(
        go.Scatter(
            x=evaluation.index,
            y=evaluation["Actual"],
            mode="lines+markers",
            name="Actual",
            line=dict(color="#149b8a"),
        )
    )
    validation_fig.add_trace(
        go.Scatter(
            x=evaluation.index,
            y=evaluation["Predicted"],
            mode="lines+markers",
            name="Predicted",
            line=dict(color="#ee9b35", dash="dash"),
        )
    )
    validation_fig.update_layout(title="Holdout: actual vs predicted", yaxis_title="Units")
    st.plotly_chart(chart_layout(validation_fig, 320), width="stretch")

with right:
    st.subheader("Trend & seasonality")
    components = results["components"].tail(90)
    decomposition_fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=("Trend", f"{seasonal_period}-day seasonal pattern", "Residual"),
    )
    for row, column, color in [
        (1, "Trend", "#355caa"),
        (2, "Seasonal", "#ee9b35"),
        (3, "Residual", "#8492a6"),
    ]:
        decomposition_fig.add_trace(
            go.Scatter(
                x=components.index,
                y=components[column],
                mode="lines",
                name=column,
                line=dict(color=color),
                showlegend=False,
            ),
            row=row,
            col=1,
        )
    decomposition_fig.update_layout(title="Sales decomposition")
    st.plotly_chart(chart_layout(decomposition_fig, 320), width="stretch")

st.subheader("Inventory outlook")
if inventory_status is None:
    st.info("Optional: enter current available stock in the sidebar to estimate inventory coverage.")
elif inventory_status == "Stockout risk":
    st.error(
        f"Stockout risk: {available_stock:,.0f} units on hand do not cover the "
        f"forecast demand of {projected_forecast['Forecast'].sum():,.0f} units."
    )
elif inventory_status == "Overstock risk":
    st.warning(
        f"Overstock risk: current stock ({available_stock:,.0f}) is more than "
        "125% of forecast demand for this horizon."
    )
else:
    st.success(
        f"Stock covers forecast demand: {available_stock:,.0f} units on hand vs "
        f"{projected_forecast['Forecast'].sum():,.0f} expected units."
    )

st.subheader("Forecast details")
display_forecast = projected_forecast.copy()
display_forecast.index = display_forecast.index.strftime("%Y-%m-%d")
st.dataframe(
    display_forecast.style.format(
        {
            "Forecast": "{:,.1f}",
            "Cumulative Forecast Demand": "{:,.1f}",
            "Projected Stock Remaining": "{:,.1f}",
        },
        na_rep="—",
    ),
    width="stretch",
)
csv_buffer = BytesIO()
projected_forecast.to_csv(csv_buffer, index_label="Date")
st.download_button(
    "Download forecast CSV",
    data=csv_buffer.getvalue(),
    file_name="sales_demand_forecast.csv",
    mime="text/csv",
    type="primary",
)

with st.expander("Preview cleaned sales data"):
    st.dataframe(
        sales.rename("Sales").to_frame().tail(30),
        width="stretch",
    )
