import streamlit as st

dashboard = st.Page(
    "pages/dashboard.py",
    title="Dashboard",
    icon="📊",
    default=True
)

order_explorer = st.Page(
    "pages/order_explorer.py",
    title="Order Explorer",
    icon="🔍"
)

navigation = st.navigation(
    [dashboard, order_explorer],
    position="sidebar"
)

navigation.run()
