
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    st.error("DATABASE_URL not found. Check the .env file.")
    st.stop()

st.set_page_config(
    page_title="QuickCommerce Analytics",
    page_icon="📊",
    layout="wide"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

st.title("🛒 QuickCommerce Analytics")
st.caption("Interactive analytics dashboard powered by synthetic data to explore real-world business scenarios — not real production data.")


try:
    with engine.connect() as connection:

        date_range = pd.read_sql(
            text("""
                SELECT
                    MIN(order_date) AS earliest_order,
                    MAX(order_date) AS latest_order
                FROM quickcommerce.gold_sales_summary
            """),
            connection
        )

    earliest_date = pd.to_datetime(
        date_range.loc[0, "earliest_order"]
    ).date()

    latest_date = pd.to_datetime(
        date_range.loc[0, "latest_order"]
    ).date()

    st.divider()
    st.subheader("📅 Sales Period")

    selected_period = st.selectbox(
        "Select Date Range",
        [
            "Last 1 Month",
            "Last 3 Months",
            "Last 6 Months",
            "Last 1 Year",
            "Custom Range",
            "All Time"
        ]
    )

    months = {
        "Last 1 Month": 1,
        "Last 3 Months": 3,
        "Last 6 Months": 6,
        "Last 1 Year": 12
    }

    if selected_period == "All Time":
        start_date = earliest_date
        end_date = latest_date

    elif selected_period == "Custom Range":
        col1, col2 = st.columns(2)

        with col1:
            start_date = st.date_input(
                "Start Date",
                value=earliest_date,
                min_value=earliest_date,
                max_value=latest_date
            )

        with col2:
            end_date = st.date_input(
                "End Date",
                value=latest_date,
                min_value=earliest_date,
                max_value=latest_date
            )

    else:
        start_date = (
                pd.Timestamp(latest_date)
                - pd.DateOffset(months=months[selected_period])
        ).date()

        end_date = latest_date

    params = {
        "start_date": start_date,
        "end_date": end_date
    }

    st.caption(
        f"Showing data from {start_date} to {end_date}"
    )

    with engine.connect() as connection:

        kpis = pd.read_sql(
            text("""
                SELECT
                    SUM(total_orders) AS total_orders,
                    SUM(total_revenue) AS total_revenue,
                    SUM(delivered_orders) AS delivered_orders,
                    SUM(cancelled_orders) AS cancelled_orders,
                    SUM(processing_orders) AS processing_orders,
                    SUM(total_revenue) /
                    NULLIF(SUM(total_orders), 0) AS average_order_value
                FROM quickcommerce.gold_sales_summary
                WHERE order_date BETWEEN :start_date AND :end_date
            """),
            connection,
            params=params
        )

        daily_sales = pd.read_sql(
            text("""
                SELECT
                    order_date,
                    SUM(total_revenue) AS total_revenue
                FROM quickcommerce.gold_sales_summary
                WHERE order_date BETWEEN :start_date AND :end_date
                GROUP BY order_date
                ORDER BY order_date
            """),
            connection,
            params=params
        )

        payment_data = pd.read_sql(
            text("""
                SELECT
                    payment_method,
                    SUM(total_transactions) AS total_transactions,
                    SUM(successful_payment_amount) AS successful_amount
                FROM quickcommerce.gold_payment_summary
                WHERE payment_date BETWEEN :start_date AND :end_date
                GROUP BY payment_method
                ORDER BY payment_method
            """),
            connection,
            params=params
        )

        delivery_city_data = pd.read_sql(
            text("""
                SELECT
                    city,
                    SUM(total_orders) AS total_orders,
                    SUM(delivered_orders) AS delivered_orders,
                    SUM(completed_deliveries) AS completed_deliveries,
                    ROUND(
                        (
                        SUM(average_delivery_minutes * completed_deliveries) /
                        NULLIF(SUM(completed_deliveries), 0)
                        )::NUMERIC,
                        2
                    ) AS average_delivery_minutes
                FROM quickcommerce.gold_delivery_summary
                WHERE delivery_date BETWEEN :start_date AND :end_date
                GROUP BY city
                ORDER BY total_orders DESC
                LIMIT 5
            """),
            connection,
            params=params
        )

        delivery_condition_data = pd.read_sql(
            text("""
                SELECT
                    traffic_condition,
                    weather_condition,
                    SUM(completed_deliveries) AS completed_deliveries,
                    ROUND(
                        (
                        SUM(average_delivery_minutes * completed_deliveries) /
                        NULLIF(SUM(completed_deliveries), 0)
                        )::NUMERIC,
                        2
                    ) AS average_delivery_minutes
                FROM quickcommerce.gold_delivery_summary
                WHERE delivery_date BETWEEN :start_date AND :end_date
                GROUP BY traffic_condition, weather_condition
            """),
            connection,
            params=params
        )




    data = kpis.iloc[0]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Orders", f"{int(data['total_orders']):,}")
    col2.metric("Total Revenue", f"₹{data['total_revenue'] / 10000000:,.2f} Cr")
    col3.metric("Delivered Orders", f"{int(data['delivered_orders']):,}")
    col4.metric("Average Order Value", f"₹{data['average_order_value']:,.2f}")

    st.divider()

    st.subheader("📈 Daily Sales Trend")

    fig = px.line(
        daily_sales,
        x="order_date",
        y="total_revenue",
        title="Revenue Over Time",
        labels={
            "order_date": "Order Date",
            "total_revenue": "Revenue (₹)"
        }
    )

    fig.update_layout(template="plotly_dark", height=400)

    st.plotly_chart(fig, use_container_width=True)

    col1, col2, col3 = st.columns(3)

    col1.metric("Cancelled Orders", f"{int(data['cancelled_orders']):,}")
    col2.metric("Processing Orders", f"{int(data['processing_orders']):,}")
    col3.metric(
        "Delivered Rate",
        f"{data['delivered_orders'] / data['total_orders'] * 100:.2f}%"
    )


    st.divider()

    st.subheader("💳 Payment Analysis")

    col1, col2 = st.columns(2)

    payment_revenue = px.bar(
        payment_data,
        x="payment_method",
        y="successful_amount",
        title="Successful Payment Amount by Method",
        labels={
            "payment_method": "Payment Method",
            "successful_amount": "Successful Amount (₹)"
        },
        text_auto=".2s"
    )

    payment_revenue.update_layout(
        template="plotly_dark",
        height=400
    )

    col1.plotly_chart(payment_revenue, use_container_width=True)

    payment_transactions = px.pie(
        payment_data,
        names="payment_method",
        values="total_transactions",
        title="Transactions by Payment Method",
        hole=0.45
    )

    payment_transactions.update_layout(
        template="plotly_dark",
        height=400
    )

    col2.plotly_chart(payment_transactions, use_container_width=True)

    st.subheader("Payment Data")
    st.dataframe(payment_data, use_container_width=True)

    st.divider()

    st.subheader("🏙️ City-wise Delivery Performance")

    col1, col2 = st.columns(2)

    delivery_time_chart = px.bar(
        delivery_city_data,
        x="city",
        y="average_delivery_minutes",
        title="Average Delivery Time by City",
        labels={
            "city": "City",
            "average_delivery_minutes": "Average Delivery Time (Minutes)"
        },
        text_auto=".2f"
    )

    delivery_time_chart.update_layout(
        template="plotly_dark",
        height=400
    )

    col1.plotly_chart(delivery_time_chart, use_container_width=True)

    delivered_chart = px.bar(
        delivery_city_data,
        x="city",
        y="delivered_orders",
        title="Delivered Orders by City",
        labels={
            "city": "City",
            "delivered_orders": "Delivered Orders"
        },
        text_auto=True
    )

    delivered_chart.update_layout(
        template="plotly_dark",
        height=400
    )

    col2.plotly_chart(delivered_chart, use_container_width=True)

    st.subheader("Delivery City Data")
    st.dataframe(delivery_city_data, use_container_width=True)

    st.divider()

    st.subheader("🌦️ Traffic and Weather Impact on Deliveries")

    col1, col2 = st.columns(2)

    traffic_chart = px.bar(
        delivery_condition_data,
        x="traffic_condition",
        y="average_delivery_minutes",
        title="Average Delivery Time by Traffic",
        labels={
            "traffic_condition": "Traffic Condition",
            "average_delivery_minutes": "Average Delivery Time (Minutes)"
        },
        text_auto=".2f"
    )

    traffic_chart.update_layout(
        template="plotly_dark",
        height=400
    )

    col1.plotly_chart(traffic_chart, use_container_width=True)

    weather_chart = px.bar(
        delivery_condition_data,
        x="weather_condition",
        y="average_delivery_minutes",
        title="Average Delivery Time by Weather",
        labels={
            "weather_condition": "Weather Condition",
            "average_delivery_minutes": "Average Delivery Time (Minutes)"
        },
        text_auto=".2f"
    )

    weather_chart.update_layout(
        template="plotly_dark",
        height=400
    )

    col2.plotly_chart(weather_chart, use_container_width=True)

    st.subheader("Delivery Condition Data")
    st.dataframe(delivery_condition_data, use_container_width=True)

    st.divider()

    st.subheader("✅ Data Validation")

    validation_query = """
    SELECT
        COUNT(*) AS summary_rows,
        SUM(total_orders) AS total_orders,
        ROUND(SUM(total_revenue)::NUMERIC, 2) AS total_revenue,
        MIN(order_date) AS first_order_date,
        MAX(order_date) AS last_order_date
    FROM quickcommerce.gold_sales_summary
    WHERE order_date BETWEEN :start_date AND :end_date
    """

    validation_data = pd.read_sql(
        text(validation_query),
        engine,
        params=params
    )



    if (
            validation_data.iloc[0]["total_orders"] == kpis.iloc[0]["total_orders"]
            and round(float(validation_data.iloc[0]["total_revenue"]), 2)
            == round(float(kpis.iloc[0]["total_revenue"]), 2)
    ):
        st.success("All data validation checks passed.")
    else:
        st.error("Data validation failed. Please check the Gold dataset.")

    st.dataframe(validation_data, use_container_width=True)

except Exception as e:
    st.error(f"Unable to load dashboard data: {e}")

finally:
    engine.dispose()
