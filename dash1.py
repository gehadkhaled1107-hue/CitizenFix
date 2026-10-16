import pandas as pd
import plotly.express as px
import streamlit as st


# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="CitizenFix Dashboard",
    page_icon="📊",
    layout="wide"
)


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------
# Make sure complaints_1000.csv is in the same folder
df = pd.read_csv("complaints_1000.csv")


# ---------------------------------------------------------
# PREPARE DATA
# ---------------------------------------------------------
df["created_at"] = pd.to_datetime(df["created_at"])
df["deadline"] = pd.to_datetime(df["deadline"])

df["date_only"] = df["created_at"].dt.date

now = pd.Timestamp.now()

df["hours_to_deadline"] = (
    (df["deadline"] - now).dt.total_seconds() / 3600
)


# Priority labels
priority_labels = {
    1: "Urgent",
    2: "Medium",
    3: "Normal"
}

df["priority_label"] = df["priority"].map(priority_labels)


# ---------------------------------------------------------
# TITLE
# ---------------------------------------------------------
st.title("📊 CitizenFix Dashboard")
st.caption("Complaint Analytics and Data Visualization")


# ---------------------------------------------------------
# FILTERS
# ---------------------------------------------------------
st.sidebar.header("🔎 Filters")


categories = sorted(df["category"].dropna().unique())
statuses = sorted(df["status"].dropna().unique())
neighborhoods = sorted(df["neighborhood"].dropna().unique())


selected_categories = st.sidebar.multiselect(
    "Category",
    categories,
    default=categories
)

selected_statuses = st.sidebar.multiselect(
    "Status",
    statuses,
    default=statuses
)

selected_neighborhoods = st.sidebar.multiselect(
    "Neighborhood",
    neighborhoods,
    default=neighborhoods
)


# ---------------------------------------------------------
# FILTER DATA
# ---------------------------------------------------------
filtered_df = df[
    (df["category"].isin(selected_categories)) &
    (df["status"].isin(selected_statuses)) &
    (df["neighborhood"].isin(selected_neighborhoods))
].copy()


# ---------------------------------------------------------
# KPI CALCULATIONS
# ---------------------------------------------------------
total_complaints = len(filtered_df)

active_statuses = [
    "Pending",
    "Assigned",
    "In Progress"
]

active_complaints = len(
    filtered_df[
        filtered_df["status"].isin(active_statuses)
    ]
)

resolved_complaints = len(
    filtered_df[
        filtered_df["status"] == "Resolved"
    ]
)

urgent_complaints = len(
    filtered_df[
        filtered_df["priority"] == 1
    ]
)

overdue_complaints = len(
    filtered_df[
        (filtered_df["status"].isin(active_statuses)) &
        (filtered_df["deadline"] < now)
    ]
)


# ---------------------------------------------------------
# KPI CARDS
# ---------------------------------------------------------
k1, k2, k3, k4, k5 = st.columns(5)

k1.metric(
    "Total Complaints",
    f"{total_complaints:,}"
)

k2.metric(
    "Active Cases",
    f"{active_complaints:,}"
)

resolved_rate = (
    resolved_complaints / total_complaints * 100
    if total_complaints > 0
    else 0
)

k3.metric(
    "Resolved Cases",
    f"{resolved_complaints:,}",
    f"{resolved_rate:.1f}%"
)

k4.metric(
    "Urgent Cases",
    f"{urgent_complaints:,}"
)

k5.metric(
    "Overdue Active",
    f"{overdue_complaints:,}"
)


st.divider()


# =========================================================
# CHART 1 - LINE CHART
# =========================================================

st.subheader("📈 Complaints Volume Over Time")

daily_counts = (
    filtered_df
    .groupby(["date_only", "priority_label"])
    .size()
    .reset_index(name="count")
)

fig_line = px.line(
    daily_counts,
    x="date_only",
    y="count",
    color="priority_label",
    markers=True,
    title="Daily Complaints by Priority",
    labels={
        "date_only": "Date",
        "count": "Complaints",
        "priority_label": "Priority"
    }
)

fig_line.update_layout(height=400)

st.plotly_chart(
    fig_line,
    use_container_width=True
)


# =========================================================
# CHART 2 - PIE CHART
# =========================================================

st.subheader("🥧 Complaint Status Distribution")

status_counts = (
    filtered_df["status"]
    .value_counts()
    .reset_index()
)

status_counts.columns = [
    "status",
    "count"
]

fig_pie = px.pie(
    status_counts,
    names="status",
    values="count",
    hole=0.4,
    title="Complaints by Status"
)

fig_pie.update_traces(
    textposition="inside",
    textinfo="percent+label"
)

st.plotly_chart(
    fig_pie,
    use_container_width=True
)


# =========================================================
# CHART 3 - BAR CHART
# =========================================================

st.subheader("📊 Complaints by Category and Status")

category_status = (
    filtered_df
    .groupby(["category", "status"])
    .size()
    .reset_index(name="count")
)

fig_bar = px.bar(
    category_status,
    x="category",
    y="count",
    color="status",
    barmode="group",
    title="Category Workload by Status"
)

fig_bar.update_layout(height=450)

st.plotly_chart(
    fig_bar,
    use_container_width=True
)


# =========================================================
# CHART 4 - SCATTER PLOT
# =========================================================

st.subheader("🔵 Creation Time vs Remaining SLA Hours")

fig_scatter = px.scatter(
    filtered_df,
    x="created_at",
    y="hours_to_deadline",
    color="priority_label",
    symbol="status",
    hover_data=[
        "ticket_id",
        "citizen_name",
        "category",
        "neighborhood",
        "team"
    ],
    title="Creation Time vs SLA Deadline",
    labels={
        "created_at": "Created At",
        "hours_to_deadline": "Hours to Deadline",
        "priority_label": "Priority"
    }
)

fig_scatter.add_hline(
    y=0,
    line_dash="dash",
    annotation_text="SLA Deadline"
)

fig_scatter.update_layout(height=450)

st.plotly_chart(
    fig_scatter,
    use_container_width=True
)


# =========================================================
# DATAFRAME
# =========================================================

st.divider()

st.subheader("📋 Complaint Data")

st.caption(
    "You can edit the data directly in the table."
)


# Select important columns
display_columns = [
    "ticket_id",
    "apartment_id",
    "citizen_name",
    "phone",
    "category",
    "priority",
    "priority_label",
    "neighborhood",
    "status",
    "team",
    "created_at",
    "deadline"
]

display_df = filtered_df[display_columns].copy()


# Interactive editable dataframe
edited_df = st.data_editor(
    display_df,
    num_rows="dynamic",
    use_container_width=True,
    height=500
)


# ---------------------------------------------------------
# DOWNLOAD UPDATED DATA
# ---------------------------------------------------------

st.download_button(
    "📥 Download Updated Data",
    data=edited_df.to_csv(index=False).encode("utf-8"),
    file_name="complaints_updated.csv",
    mime="text/csv"
)