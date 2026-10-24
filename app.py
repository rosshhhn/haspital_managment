
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Coffee Shop Analytics",
    page_icon="☕",
    layout="wide"
)

st.title("☕ Coffee Shop Business Analytics")
st.caption("Sales performance, customer behavior, and product insights")

# Load project data
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "reports" / "coffee_shop_powerbi.xlsx"

@st.cache_data
def load_data():
    sales = pd.read_excel(DATA_FILE, sheet_name="Sales")
    customers = pd.read_excel(DATA_FILE, sheet_name="Customers")
    inventory = pd.read_excel(DATA_FILE, sheet_name="Inventory")

    sales["order_date"] = pd.to_datetime(sales["order_date"])
    sales["revenue"] = (
        sales["quantity"]
        * sales["unit_price"]
        * (1 - sales["discount_pct"] / 100)
    )
    sales["profit"] = sales["quantity"] * (
        sales["unit_price"]
        * (1 - sales["discount_pct"] / 100)
        - sales["unit_cost"]
    )
    return sales, customers, inventory

try:
    sales, customers, inventory = load_data()
except Exception as e:
    st.error(f"Could not load the project data: {e}")
    st.info(
        "Check that reports/coffee_shop_powerbi.xlsx exists "
        "and contains Sales, Customers, and Inventory sheets."
    )
    st.stop()

# Sidebar filters
st.sidebar.header("Dashboard Filters")

min_date = sales["order_date"].min().date()
max_date = sales["order_date"].max().date()

date_range = st.sidebar.date_input(
    "Select date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

filtered = sales.copy()

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
    filtered = filtered[
        (filtered["order_date"].dt.date >= start_date)
        & (filtered["order_date"].dt.date <= end_date)
    ]

categories = sorted(filtered["category"].dropna().unique())
selected_categories = st.sidebar.multiselect(
    "Product categories",
    categories,
    default=categories
)

if selected_categories:
    filtered = filtered[filtered["category"].isin(selected_categories)]
else:
    filtered = filtered.iloc[0:0]

# Key metrics
total_revenue = filtered["revenue"].sum()
total_orders = filtered["order_id"].nunique()
unique_customers = filtered["customer_id"].nunique()
total_profit = filtered["profit"].sum()
average_order_value = total_revenue / total_orders if total_orders else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Revenue", f"₹{total_revenue:,.2f}")
c2.metric("Total Orders", f"{total_orders:,}")
c3.metric("Unique Customers", f"{unique_customers:,}")
c4.metric("Gross Profit", f"₹{total_profit:,.2f}")

st.metric("Average Order Value", f"₹{average_order_value:,.2f}")

st.divider()

# Charts
left, right = st.columns(2)

with left:
    st.subheader("Revenue by Product")
    product_sales = (
        filtered.groupby("product_name", as_index=False)["revenue"]
        .sum()
        .sort_values("revenue", ascending=False)
    )
    fig = px.bar(
        product_sales,
        x="revenue",
        y="product_name",
        orientation="h",
        title="Products ranked by revenue",
        labels={"revenue": "Revenue (₹)", "product_name": "Product"}
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Revenue by Category")
    category_sales = (
        filtered.groupby("category", as_index=False)["revenue"]
        .sum()
        .sort_values("revenue", ascending=False)
    )
    fig = px.pie(
        category_sales,
        names="category",
        values="revenue",
        hole=0.45,
        title="Share of revenue"
    )
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Monthly Revenue")
monthly = (
    filtered.assign(month=filtered["order_date"].dt.to_period("M").astype(str))
    .groupby("month", as_index=False)["revenue"]
    .sum()
)
fig = px.line(
    monthly,
    x="month",
    y="revenue",
    markers=True,
    labels={"month": "Month", "revenue": "Revenue (₹)"},
    title="Revenue trend over time"
)
st.plotly_chart(fig, use_container_width=True)

left, right = st.columns(2)

with left:
    st.subheader("Revenue by Hour")
    if "order_time" in filtered.columns:
        times = pd.to_datetime(
            filtered["order_time"].astype(str),
            format="%H:%M",
            errors="coerce"
        )
        hourly_data = filtered.assign(
            hour=times.dt.hour
        ).dropna(subset=["hour"])
        hourly = (
            hourly_data.groupby("hour", as_index=False)["revenue"]
            .sum()
        )
        fig = px.bar(
            hourly,
            x="hour",
            y="revenue",
            labels={"hour": "Hour of day", "revenue": "Revenue (₹)"}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("The sales data does not contain an order_time column.")

with right:
    st.subheader("Revenue by Weekday")
    if "order_date" in filtered.columns:
        weekday_data = filtered.assign(
            weekday=filtered["order_date"].dt.day_name()
        )
        weekday = (
            weekday_data.groupby("weekday", as_index=False)["revenue"]
            .sum()
        )
        weekday_order = [
            "Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday"
        ]
        weekday["weekday"] = pd.Categorical(
            weekday["weekday"],
            categories=weekday_order,
            ordered=True
        )
        weekday = weekday.sort_values("weekday")
        fig = px.bar(
            weekday,
            x="weekday",
            y="revenue",
            labels={"weekday": "Day", "revenue": "Revenue (₹)"}
        )
        st.plotly_chart(fig, use_container_width=True)

st.divider()

# Tables
st.subheader("Top 10 Products")
st.dataframe(
    product_sales.head(10),
    use_container_width=True,
    hide_index=True
)

st.subheader("Inventory Overview")
st.dataframe(inventory, use_container_width=True, hide_index=True)

st.caption(
    "This dashboard uses simulated project data. "
    "Revenue and profit are calculated from the available sales records."
)
