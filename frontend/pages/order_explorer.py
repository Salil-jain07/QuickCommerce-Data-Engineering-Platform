
import duckdb
import streamlit as st
import os


GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME', 'quickcommerce-data-platform-salil')

GOLD_FILE = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/gold/gold_order_summary.parquet"
FILTER_FILE = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/gold/gold_order_filters.parquet"
VEHICLE_FILE = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/gold/gold_vehicle_summary.parquet"

def connect_duckdb():
    con = duckdb.connect()
    con.execute("INSTALL httpfs")
    con.execute("LOAD httpfs")
    return con


st.set_page_config(
    page_title="Order Explorer",
    page_icon="📦",
    layout="wide"
)

st.title("Detailed Order Explorer")
st.caption("Search, explore and inspect QuickCommerce order records")

@st.cache_data
def load_filter_options(file_path):
    con = connect_duckdb()

    rows = con.execute("""
        SELECT DISTINCT city, platform, order_status
        FROM read_parquet(?)
    """, [file_path]).fetchall()

    con.close()

    cities = sorted({row[0] for row in rows if row[0] is not None})
    platforms = sorted({row[1] for row in rows if row[1] is not None})
    statuses = sorted({row[2] for row in rows if row[2] is not None})

    return cities, platforms, statuses



@st.cache_data
def load_vehicle_analysis(file_path, city, platform, status):
    con = connect_duckdb()

    conditions = []
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

    where_clause = (
        "WHERE " + " AND ".join(conditions)
        if conditions else ""
    )

    vehicle_data = con.execute(
        f"""
        SELECT
            vehicle_type,
            SUM(total_orders) AS total_orders,
            SUM(delivered_orders) AS delivered_orders,
            ROUND(
                SUM(average_delivery_minutes * delivered_orders)
                / NULLIF(SUM(delivered_orders), 0),
                2
            ) AS average_delivery_minutes,
            ROUND(
                100.0 * SUM(delivered_orders)
                / NULLIF(SUM(total_orders), 0),
                2
            ) AS delivery_rate
        FROM read_parquet(?)
        {where_clause}
        GROUP BY vehicle_type
        ORDER BY total_orders DESC
        """,
        params
    ).fetchdf()

    con.close()
    return vehicle_data


cities, platforms, statuses = load_filter_options(str(FILTER_FILE))

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

if "page_cursors" not in st.session_state:
    st.session_state.page_cursors = [None]

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
    st.session_state.page_cursors = [None]

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

con = connect_duckdb()

cursor = st.session_state.page_cursors[
    st.session_state.current_page - 1
]

query_conditions = conditions.copy()
query_params = params.copy()

if cursor is not None:
    query_conditions.append("order_id > ?")
    query_params.append(cursor)

cursor_where = (
    " WHERE " + " AND ".join(query_conditions)
    if query_conditions else ""
)

data_query = (
    "SELECT * FROM read_parquet(?)"
    + cursor_where
    + " LIMIT ?"
)

fetched_results = con.execute(
    data_query,
    [str(GOLD_FILE)] + query_params + [page_size + 1]
).fetchdf()

con.close()

has_next = len(fetched_results) > page_size
results = fetched_results.iloc[:page_size].copy()

st.divider()

st.subheader("🔍 Search Results")

col1, col2, col3 = st.columns(3)

col1.metric("Records on Current Page", f"{len(results):,}")
col2.metric("Current Page", st.session_state.current_page)
col3.metric("More Results Available", "Yes" if has_next else "No")

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
            f"{st.session_state.current_page}</div>",
            unsafe_allow_html=True
        )

    with col3:
        if st.button("Next", disabled=not has_next):
            last_order_id = results["order_id"].iloc[-1]

            st.session_state.page_cursors = (
                st.session_state.page_cursors[
                    :st.session_state.current_page
                ]
            )

            st.session_state.page_cursors.append(last_order_id)
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
        if filters["order_id"]:
            st.warning("Clear the Order ID search to view vehicle-wise analysis.")
            vehicle_data = None
        else:
            vehicle_data = load_vehicle_analysis(
                str(VEHICLE_FILE),
                filters["city"],
                filters["platform"],
                filters["status"]
            )

    if vehicle_data is not None and not vehicle_data.empty:

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
