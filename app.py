import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Inventory Control Tower", 
    page_icon="🏗️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a cleaner, corporate aesthetic
# Custom CSS for a professional Dark Mode aesthetic
st.markdown("""
    <style>
    /* Targeting the metric cards */
    [data-testid="stMetric"] {
        background-color: #1e2130; 
        border: 1px solid #313348;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    /* Ensuring the labels and values are bright and readable */
    [data-testid="stMetricLabel"] {
        color: #94a3b8 !important; /* Muted blue-grey for labels */
        font-weight: 600;
    }
    
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-weight: 700;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🏗️ Inventory Control Tower")
st.markdown("### Master Data Quality & Supply Chain Monitor")

# --- DATA CONNECTION (WITH CACHING) ---
# Using @st.cache_data ensures the database isn't queried from scratch every time you click a button
@st.cache_data
def get_data():
    db_path = 'data/processed/supply_chain.duckdb'
    conn = duckdb.connect(db_path)
    df = conn.execute("SELECT * FROM master_parts_data").df()
    conn.close()
    return df

df = get_data()

# --- SIDEBAR FILTERS ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2830/2830312.png", width=50) # Generic logistics icon
st.sidebar.header("Filter Workspace")

health_filter = st.sidebar.multiselect(
    "Data Health Status:",
    options=df["data_health"].unique(),
    default=df["data_health"].unique()
)

family_filter = st.sidebar.multiselect(
    "Part Family:",
    options=df["model_family_group"].unique(),
    default=df["model_family_group"].unique()
)

# Apply Filters
filtered_df = df[
    (df["data_health"].isin(health_filter)) & 
    (df["model_family_group"].isin(family_filter))
]

# --- KEY PERFORMANCE INDICATORS (KPIs) ---
st.markdown("##### Pipeline Overview")
col1, col2, col3, col4 = st.columns(4)

total_records = len(filtered_df)
flagged_records = len(filtered_df[filtered_df['data_health'] == 'Needs Review'])
clean_rate = ((total_records - flagged_records) / total_records * 100) if total_records > 0 else 0

col1.metric("Total Records", f"{total_records:,}")
col2.metric("Flagged for Audit", f"{flagged_records:,}", delta="-Action Required", delta_color="inverse")
col3.metric("Data Cleanliness", f"{clean_rate:.1f}%")
col4.metric("Avg. Base Price", f"${filtered_df['base_price'].mean():.2f}")

st.divider()

# --- INTERACTIVE TABS ---
tab1, tab2 = st.tabs(["📊 Visual Analytics", "🗄️ Raw Data Explorer"])

with tab1:
    st.subheader("Anomaly Distribution")
    # Group data for the chart
    chart_data = filtered_df.groupby(['model_family_group', 'data_health']).size().reset_index(name='count')
    
    # Create an interactive Plotly bar chart
    fig = px.bar(
        chart_data, 
        x='model_family_group', 
        y='count', 
        color='data_health',
        title="Record Health by Part Family",
        labels={'model_family_group': 'Part Family', 'count': 'Number of Records'},
        color_discrete_map={'Clean': '#2ecc71', 'Needs Review': '#e74c3c'}
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Inventory Master Data")
    # Updated 'width' parameter for the latest Streamlit version
    st.dataframe(filtered_df, width=None, height=400, use_container_width=True)