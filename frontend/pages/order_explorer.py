
import duckdb
import streamlit as st
from fsspec import filesystem
import os


GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME', 'quickcommerce-data-platform-salil')

GOLD_FILE = f"gcs://{GCS_BUCKET_NAME}/gold/gold_order_summary.parquet"


def get_gcs_filesystem():
    return filesystem("gcs", token="anon")

st.set_page_config(
    page_title="Order Explorer",
    page_icon="📦",
    layout="wide"
)

st.title("Detailed Order Explorer")
st.caption("Search, explore and inspect QuickCommerce order records")

@st.cache_data
def load_filter_options(file_path):
    con = duckdb.connect()
    gcs = get_gcs_filesystem()
    con.register_filesystem(gcs)

    cities = con.execute(
        "SELECT DISTINCT city FROM read_parquet(?) ORDER BY city",
        [file_path]
    ).fetchdf()["city"].tolist()

    platforms = con.execute(
        "SELECT DISTINCT platform FROM read_parquet(?) ORDER BY platform",
        [file_path]
    ).fetchdf()["platform"].tolist()

    statuses = con.execute(
        "SELECT DISTINCT order_status FROM read_parquet(?) ORDER BY order_status",
        [file_path]
    ).fetchdf()["order_status"].tolist()

    con.close()

    return cities, platforms, statuses



@st.cache_data
def load_vehicle_analysis(file_path, city, platform, status, order_id):
    con = duckdb.connect()
    gcs = get_gcs_filesystem()
    con.register_filesystem(gcs)

    conditions = ["vehicle_type IS NOT NULL"]
    params = [file_path]

    if city != "All":
        conditions.append("city = ?")
        params.append(city)

    if platform != "All":
        conditions.append("platform = ?")
        params.append(platform)

    if status != "All":
        conditions.append("order_status = ?")
        params.append(status)

    if order_id:
        conditions.append("CAST(order_id AS VARCHAR) LIKE ?")
        params.append(f"%{order_id}%")

    where_clause = " AND ".join(conditions)

    vehicle_data = con.execute(
        f"""
        SELECT
            vehicle_type,
            COUNT(*) AS total_orders,
            COUNT(*) FILTER (
                WHERE delivery_status = 'Delivered'
            ) AS delivered_orders,
            ROUND(
                AVG(delivery_duration_minutes) FILTER (
                    WHERE delivery_status = 'Delivered'
                ),
                2
            ) AS average_delivery_minutes,
            ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE delivery_status = 'Delivered'
                ) / COUNT(*),
                2
            ) AS delivery_rate
        FROM read_parquet(?)
        WHERE {where_clause}
        GROUP BY vehicle_type
        ORDER BY total_orders DESC
        """,
        params
    ).fetchdf()

    con.close()

    return vehicle_data

cities, platforms, statuses = load_filter_options(str(GOLD_FILE))

if "active_filters" not in st.session_state:
    st.session_state.active_filters = {
        "city": "All",
        "platform": "All",
        "status": "All",
        "order_id": ""
    }

if "current_page" not in st.session_state:
    st.session_state.current_page = 1

if "page_size" not in st.session_state:
    st.session_state.page_size = 100

st.subheader("Filter Orders")

col1, col2, col3 = st.columns(3)

with col1:
    selected_city = st.selectbox("City", ["All"] + cities)

with col2:
    selected_platform = st.selectbox("Platform", ["All"] + platforms)

with col3:
    selected_status = st.selectbox("Order Status", ["All"] + statuses)

order_id = st.text_input("Search by Order ID")

page_size = st.selectbox(
    "Records per page",
    [50, 100, 200, 500],
    index=1
)

if st.button("Search Orders"):
    st.session_state.active_filters = {
        "city": selected_city,
        "platform": selected_platform,
        "status": selected_status,
        "order_id": order_id.strip()
    }

    st.session_state.current_page = 1
    st.session_state.page_size = page_size

filters = st.session_state.active_filters
page_size = st.session_state.page_size

conditions = []
params = []

if filters["city"] != "All":
    conditions.append("city = ?")
    params.append(filters["city"])

if filters["platform"] != "All":
    conditions.append("platform = ?")
    params.append(filters["platform"])

if filters["status"] != "All":
    conditions.append("order_status = ?")
    params.append(filters["status"])

if filters["order_id"]:
    conditions.append("CAST(order_id AS VARCHAR) LIKE ?")
    params.append(f"%{filters['order_id']}%")

where_clause = ""

if conditions:
    where_clause = " WHERE " + " AND ".join(conditions)

con = duckdb.connect()
gcs = get_gcs_filesystem()
con.register_filesystem(gcs)

if not conditions:
    total_records = con.execute(
        "SELECT num_rows FROM parquet_file_metadata(?) LIMIT 1",
        [str(GOLD_FILE)]
    ).fetchone()[0]
else:
    count_query = (
        "SELECT COUNT(*) FROM read_parquet(?)" + where_clause
    )

    total_records = con.execute(
        count_query,
        [str(GOLD_FILE)] + params
    ).fetchone()[0]

total_pages = max(1, (total_records + page_size - 1) // page_size)

st.session_state.current_page = min(
    st.session_state.current_page,
    total_pages
)

offset = (st.session_state.current_page - 1) * page_size

data_query = (
    "SELECT * FROM read_parquet(?)"
    + where_clause
    + " LIMIT ? OFFSET ?"
)

results = con.execute(
    data_query,
    [str(GOLD_FILE)] + params + [page_size, offset]
).fetchdf()

con.close()

st.divider()

st.subheader("🔍 Search Results")

col1, col2, col3 = st.columns(3)

col1.metric("Total Matching Orders", f"{total_records:,}")
col2.metric("Current Page", f"{st.session_state.current_page} / {total_pages}")
col3.metric("Records Per Page", page_size)

st.dataframe(
    results,
    use_container_width=True,
    hide_index=True,
    column_config={
        "order_id": st.column_config.TextColumn("Order ID"),
        "customer_name": st.column_config.TextColumn("Customer"),
        "city": st.column_config.TextColumn("City"),
        "platform": st.column_config.TextColumn("Platform"),
        "order_status": st.column_config.TextColumn("Order Status"),
        "total_items": st.column_config.NumberColumn("Items"),
        "total_quantity": st.column_config.NumberColumn("Quantity"),
        "item_sales_amount": st.column_config.NumberColumn(
            "Sales Amount",
            format="₹%.2f"
        ),
        "payment_method": st.column_config.TextColumn("Payment Method"),
        "delivery_status": st.column_config.TextColumn("Delivery Status"),
        "delivery_duration_minutes": st.column_config.NumberColumn(
            "Delivery Minutes",
            format="%.2f min"
        )
    }
)

if not results.empty:
    csv = results.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download Current Page as CSV",
        data=csv,
        file_name="quickcommerce_orders.csv",
        mime="text/csv"
    )
    st.divider()

    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.button(
                "Previous",
                disabled=st.session_state.current_page <= 1
        ):
            st.session_state.current_page -= 1
            st.rerun()

    with col2:
        st.markdown(
            f"<div style='text-align:center'>Page "
            f"{st.session_state.current_page} of {total_pages}</div>",
            unsafe_allow_html=True
        )

    with col3:
        if st.button(
                "Next",
                disabled=st.session_state.current_page >= total_pages
        ):
            st.session_state.current_page += 1
            st.rerun()

    st.divider()

    st.subheader("📦 Individual Order Details")

    order_options = results["order_id"].astype(str).tolist()

    selected_order = st.selectbox(
        "Select an Order ID",
        order_options
    )

    selected_details = results[
        results["order_id"].astype(str) == selected_order
    ].iloc[0]

    st.markdown(f"### Order ID: {selected_order}")

    st.markdown("#### Order & Customer")

    col1, col2, col3 = st.columns(3)

    col1.metric("Customer ID", str(selected_details["customer_id"]))
    col2.metric("Customer Name", str(selected_details["customer_name"]))
    col3.metric("Loyalty Tier", str(selected_details["loyalty_tier"]))

    col1, col2, col3 = st.columns(3)

    col1.metric("City", str(selected_details["city"]))
    col2.metric("Platform", str(selected_details["platform"]))
    col3.metric("Order Status", str(selected_details["order_status"]))

    st.markdown("#### Product & Sales")

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Items", str(selected_details["total_items"]))
    col2.metric("Total Quantity", str(selected_details["total_quantity"]))
    col3.metric(
        "Item Sales Amount",
        f"₹{selected_details['item_sales_amount']:,.2f}"
    )

    st.markdown("#### Payment")

    col1, col2 = st.columns(2)

    col1.metric(
        "Payment Amount",
        f"₹{selected_details['payment_amount']:,.2f}"
    )
    col2.metric("Payment Method", str(selected_details["payment_method"]))

    st.write("Payment Status:", selected_details["payment_status"])

    st.markdown("#### Store & Delivery")

    col1, col2, col3 = st.columns(3)

    col1.metric("Store", str(selected_details["store_name"]))
    col2.metric("Store Type", str(selected_details["store_type"]))
    col3.metric("Delivery Status", str(selected_details["delivery_status"]))

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Delivery Duration",
        f"{selected_details['delivery_duration_minutes']} min"
    )
    col2.metric(
        "Distance",
        f"{selected_details['distance_km']} km"
    )
    col3.metric("Vehicle Type", str(selected_details["vehicle_type"]))

    st.write("Weather Condition:", selected_details["weather_condition"])
    st.write("Traffic Condition:", selected_details["traffic_condition"])

    st.write("Order Date:", str(selected_details["order_datetime"]))


st.divider()

st.subheader("🚚 Vehicle-wise Delivery Analysis")

if st.button("Run Vehicle Analysis", type="primary"):
    st.session_state["run_vehicle_analysis"] = True

if st.session_state.get("run_vehicle_analysis", False):

    with st.spinner("Analyzing vehicle delivery performance..."):
        vehicle_data = load_vehicle_analysis(
            str(GOLD_FILE),
            filters["city"],
            filters["platform"],
            filters["status"],
            filters["order_id"]
        )

    if not vehicle_data.empty:

        total_vehicles = len(vehicle_data)
        total_vehicle_orders = int(vehicle_data["total_orders"].sum())
        total_delivered_orders = int(vehicle_data["delivered_orders"].sum())

        overall_delivery_rate = (
            total_delivered_orders / total_vehicle_orders * 100
            if total_vehicle_orders > 0 else 0
        )

        st.markdown("#### Vehicle Performance KPIs")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Vehicle Types", total_vehicles)
        col2.metric("Total Orders", f"{total_vehicle_orders:,}")
        col3.metric("Delivered Orders", f"{total_delivered_orders:,}")
        col4.metric("Overall Delivery Rate", f"{overall_delivery_rate:.2f}%")

        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Orders by Vehicle Type")
            st.bar_chart(
                vehicle_data,
                x="vehicle_type",
                y="total_orders"
            )

        with col2:
            st.markdown("#### Average Delivery Time")
            st.bar_chart(
                vehicle_data,
                x="vehicle_type",
                y="average_delivery_minutes"
            )

        st.markdown("#### Vehicle Performance Data")
        st.dataframe(vehicle_data, use_container_width=True)

    else:
        st.info("No vehicle delivery data available.")

else:
    st.info("Click Run Vehicle Analysis when you want to view vehicle performance.")
