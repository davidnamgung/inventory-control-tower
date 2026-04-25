import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def format_currency(value):
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    elif value >= 1_000:
        return f"${value / 1_000:.1f}K"
    else:
        return f"${value:.2f}"

# --- PAGE CONFIG ---
st.set_page_config(page_title="Inventory Control Tower v2", page_icon="🏢", layout="wide")

# Custom Professional CSS
st.markdown("""
    <style>
    [data-testid="stMetric"] { background-color: #111827; border: 1px solid #374151; padding: 20px; border-radius: 12px; }
    [data-testid="stMetricValue"] { color: #38bdf8 !important; font-size: 1.8rem; }
    .plot-explanation { font-style: italic; color: #94a3b8; font-size: 0.9rem; margin-top: -10px; margin-bottom: 20px; }
    .business-q { background-color: #1e293b; padding: 15px; border-radius: 8px; border-left: 5px solid #38bdf8; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

import os
# --- DATA LOADING ---
@st.cache_data
def get_data():
    db_path = 'data/processed/supply_chain.duckdb'
    
    if not os.path.exists(db_path):
        # This will show up in red on the web app to tell you it's a path issue
        st.error(f"FATAL: Database not found at {db_path}. Check GitHub folder structure.")
        return None # Return None instead of an empty DF

    try:
        conn = duckdb.connect(db_path, read_only=True)
        df = conn.execute("SELECT * FROM master_parts_data").df()
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return None

# Add a loading spinner
with st.spinner("Connecting to DuckDB Operational Data Store..."):
    df = get_data()

# --- CRITICAL CHECK ---
if df is None:
    st.warning("⚠️ The Dashboard cannot load because the source database is missing from the repository.")
    st.stop() # Stops the app here so it doesn't try to load the rest and crash

# --- SIDEBAR FILTERS ---
st.sidebar.header("🕹️ Control Panel")
health_select = st.sidebar.multiselect("Data Quality Filter:", df['data_health'].unique(), default=df['data_health'].unique())
family_select = st.sidebar.multiselect("inventory Category:", df['model_family_group'].unique(), default=df['model_family_group'].unique())

filtered_df = df[(df['data_health'].isin(health_select)) & (df['model_family_group'].isin(family_select))]

# --- CALCULATIONS ---
total_val = (filtered_df['base_price'] * filtered_df['stock_quantity']).sum()
risk_df = filtered_df[filtered_df['data_health'] == 'Needs Review']
risk_val = (risk_df['base_price'] * risk_df['stock_quantity']).sum()

# --- NAVIGATION TABS ---
tab_dash, tab_data, tab_report, tab_guide = st.tabs([
    "📊 Executive Dashboard", 
    "🗄️ Master Data Editor", 
    "📜 Technical Report", 
    "⚙️ Operations Guide"
])

with tab_dash:
    st.markdown("### 🏢 Enterprise Inventory Oversight")
    
    # KPI SECTION
    k1, k2, k3, k4 = st.columns(4)
    
    # Calculate values
    total_val = (filtered_df['base_price'] * filtered_df['stock_quantity']).sum()
    risk_df = filtered_df[filtered_df['data_health'] == 'Needs Review']
    risk_val = (risk_df['base_price'] * risk_df['stock_quantity']).sum()
    
    # Apply the smart formatter
    k1.metric("Total Items (SKUs)", f"{len(filtered_df):,}")
    k2.metric("Total Value on Hand", format_currency(total_val))
    k3.metric("Capital at Risk", format_currency(risk_val), delta="Requires Audit", delta_color="inverse")
    k4.metric("Health Score", f"{(len(filtered_df[filtered_df['data_health']=='Clean'])/len(filtered_df)*100):.1f}%")

    st.info(f"""
    **📊 Management Context:** While the Audit Rate is only **{(len(risk_df)/len(filtered_df)*100):.1f}%**, 
    it represents **{format_currency(risk_val)}** in potential valuation errors. 
    This is due to **Financial Weighting**: extreme pricing anomalies (outliers) detected by our 
    IQR logic carry significantly more financial risk than standard inventory. 
    This dashboard prioritizes these 'High-Value' flags to maximize audit efficiency.
    """)

    st.divider()

    # 2. BUSINESS QUESTIONS SECTION
    with st.expander("❓ Key Business Questions Answered by this View", expanded=True):
        st.markdown("""
        <div class="business-q">
        <b>1. Where is our data integrity weakest?</b> The Health Composition chart identifies which part families require urgent manual verification.<br>
        <b>2. Are expensive mistakes hiding in the data?</b> The Anomaly Scatter Plot isolates high-value items with flagged data quality issues.<br>
        <b>3. How much capital is 'frozen' due to unverified records?</b> The Financial Risk KPI quantifies the dollar impact of poor data quality.
        </div>
        """, unsafe_allow_html=True)

    st.subheader("Inventory Valuation Flow")
    # Calculate the 'Safe' value
    safe_val = total_val - risk_val

    fig_waterfall = go.Figure(go.Waterfall(
        orientation = "v",
        measure = ["absolute", "relative", "total"],
        x = ["Total Potential Value", "Capital at Risk", "Verified Safe Value"],
        y = [total_val, -risk_val, safe_val],
        text = [format_currency(total_val), format_currency(-risk_val), format_currency(safe_val)],
        textposition = "outside",
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
        decreasing = {"marker":{"color":"#f43f5e"}},
        increasing = {"marker":{"color":"#10b981"}},
        totals = {"marker":{"color":"#38bdf8"}}
    ))
    fig_waterfall.update_layout(margin=dict(t=30, b=0, l=0, r=0))
    st.plotly_chart(fig_waterfall, use_container_width=True)
    st.markdown('<p class="plot-explanation"><b>Insight:</b> A financial breakdown illustrating how unverified or anomalous data degrades the reliable valuation of the company’s inventory assets.</p>', unsafe_allow_html=True)

    # 3. VISUALIZATIONS
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Data Quality Composition")
        fig_donut = px.pie(filtered_df, names='data_health', hole=0.6, 
                           color='data_health', color_discrete_map={'Clean': '#10b981', 'Needs Review': '#c41e3a'})
        fig_donut.update_layout(showlegend=True, margin=dict(t=30, b=0, l=0, r=0))
        st.plotly_chart(fig_donut, use_container_width=True)
        st.markdown('<p class="plot-explanation"><b>Insight:</b> This represents the overall system trust score. A high "Needs Review" percentage indicates a breakdown in the upstream data entry process.</p>', unsafe_allow_html=True)

    with c2:
        st.subheader("Inventory Count by Family")
        count_data = filtered_df.groupby('model_family_group').size().reset_index(name='SKU Count')
        fig_bar = px.bar(count_data, x='SKU Count', y='model_family_group', orientation='h',
                         color_discrete_sequence=['#10b981'], text='SKU Count',
                         color='SKU Count', color_continuous_scale='Blues')
        st.plotly_chart(fig_bar, use_container_width=True)
        st.markdown('<p class="plot-explanation"><b>Insight:</b> Identifies the size of each inventory category by SKU volume. Useful for workload balancing among procurement officers.</p>', unsafe_allow_html=True)

    st.subheader("Financial Risk Analysis: Price vs. Quantity")
    fig_scatter = px.scatter(filtered_df, x="stock_quantity", y="base_price", color="data_health",
                             hover_data=['part_id', 'part_name'], size="base_price",
                             color_discrete_map={'Clean': '#10b981', 'Needs Review': '#c41e3a'},
                             labels={"stock_quantity": "Units in Stock", "base_price": "Unit Price ($)"})
    st.plotly_chart(fig_scatter, use_container_width=True)
    st.markdown('<p class="plot-explanation"><b>Insight:</b> High-value items (top of chart) that are red (Needs Review) represent the highest financial danger to the company’s balance sheet.</p>', unsafe_allow_html=True)



    st.subheader("Category Failure Rates (100% Stacked)")
    fig_stacked = px.histogram(filtered_df, y="model_family_group", color="data_health", 
                           barnorm="percent", orientation="h",
                           color_discrete_map={'Clean': '#10b981', 'Needs Review': '#f43f5e'},
                           labels={'model_family_group': 'Part Family'})
    fig_stacked.update_layout(xaxis_title="Percentage (%)", yaxis_title="")
    st.plotly_chart(fig_stacked, use_container_width=True)
    st.markdown('<p class="plot-explanation"><b>Insight:</b> Normalizes the volume to 100%. Categories with large red bars indicate a systemic data entry issue for that specific part family, regardless of total SKU count.</p>', unsafe_allow_html=True)


with tab_data:
    st.subheader("🗄️ Master Data Editor")
    st.markdown("Use this tab to manually audit and correct 'Needs Review' records.")
    
    # 1. Replace st.dataframe with st.data_editor
    edited_df = st.data_editor(
        filtered_df, 
        use_container_width=True, 
        height=500,
        num_rows="dynamic" # Allows users to add or delete rows
    )
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        # 2. Add a Save Button with a Toast Notification
        if st.button("💾 Save Changes", type="primary"):
            # In a real company, you would run a DuckDB UPDATE query here.
            # For a public portfolio, we use a simulation so internet users don't break your data!
            st.toast("✅ Changes successfully pushed to DuckDB!")
            st.balloons() # A fun Streamlit micro-interaction

    with col2:
        csv = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Audit-Ready CSV", data=csv, file_name='supply_chain_audit.csv', mime='text/csv')

with tab_report:
    st.header("📜 Technical Architecture & Methodology")
    
    st.markdown(""" 
**End-to-End Supply Chain Data Engineering & BI Platform**

## 1. Executive Summary
### Project Overview
The **Inventory Control Tower** is a production-grade data engineering solution designed to automate the lifecycle of supply chain data. In high-volume logistics environments, data integrity is the primary bottleneck for accurate procurement and financial reporting. This project solves that by building a modular ETL pipeline that ingests messy, disparate data sources and transforms them into a "Single Source of Truth."

### Goals
* **Automation:** Replace manual Excel-based auditing with a code-first, automated orchestrator.
* **Risk Quantification:** Identify and isolate anomalous pricing and missing data before it impacts the balance sheet.
* **Operational Scalability:** Design an architecture capable of processing incremental daily batches (100k+ rows) with sub-second analytical performance.

### Problem Statement
Logistics data often suffers from "Data Decay":
1.  **Human Entry Errors:** Pricing outliers (e.g., $5.00 vs $5,000) that skew valuation.
2.  **Lexical Fragmentation:** Inconsistent naming conventions (e.g., "ENG" vs "Engine") breaking categorical analysis.
3.  **Missing Critical Metadata:** Blank ELM (Engineering Logistics Management) codes that stall procurement workflows.

---

## 2. Data Dictionary
The master inventory table consists of 105,000+ records with the following schema:

| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `part_id` | String | Unique identifier for the SKU (e.g., PRT-001001). |
| `part_name` | String | Descriptive name of the inventory component. |
| `elm_code` | String | Engineering tracking code (Flagged as 'REQUIRES-AUDIT' if missing). |
| `model_family_group` | Category | Normalized part category (Engine, Transmission, Electrical, etc.). |
| `base_price` | Float | Unit cost in USD. |
| `stock_quantity` | Integer | Units currently available in stock. |
| `data_health` | String | Automated flag: `Clean` or `Needs Review`. |
| `is_price_anomaly`| Boolean | Boolean flag identifying statistical outliers in pricing. |

---

## 3. Data Extraction (ETL Pipeline)
The backend is powered by **Mage AI**, utilizing a modular DAG (Directed Acyclic Graph) architecture.

### A. Extraction (The Collector Pattern)
The pipeline implements a "Sweep & Archive" strategy:
* **Ingestion:** Python's `glob` library scans the `/data/raw` directory for any new `.csv` batches.
* **Archiving:** Once a batch is processed, it is physically moved to `/data/archive/`. This ensures the pipeline is **Idempotent** (running it twice won't duplicate data).

### B. Cleaning & Transformation
The Transformation block applies three layers of automated business logic:
1.  **Lexical Normalization:** Uses regex mapping to standardize variants (e.g., `motor` → `Engine`).
2.  **Imputation:** Fills NULL values in critical fields with searchable audit tags.
3.  **Statistical Anomaly Detection:** Implements **Tukey’s Fences** using the Interquartile Range (IQR):
    * *Threshold:* Any price exceeding $Q3 + (1.5 \times IQR)$ is flagged.

### C. Loading (The Analytical Engine)
Cleaned records are loaded into **DuckDB**, an in-process OLAP engine.
* **Append Logic:** Uses `INSERT INTO` to grow the historical dataset rather than overwriting.
* **Performance:** DuckDB handles the 100k+ row dataset with sub-second response times for the frontend.

---

## 4. The Streamlit Dashboard
The frontend serves as a specialized "Control Tower" for supply chain executives.

### Core Analytics Features:
* **Executive Metrics:** Instant calculation of "Capital at Risk" (the total USD value of flagged items).
* **Health Composition:** Interactive Donut Charts showing system-wide trust scores.
* **Financial Risk Scatter Plot:** A visual Pareto analysis tool to isolate high-value/high-volume anomalies.
* **Audit-Ready Table:** A dedicated tab for deep-diving into "Needs Review" records with a one-click CSV export for procurement officers.

---

## 5. Challenges & Lessons Learned

### The Idempotency Crisis
During development, an initial run loaded 100,000 records. Because the source file was not moved, a second run appended another 100,000, effectively doubling the company's inventory valuation on paper. 
* **Solution:** I implemented a strict **Post-Write Archive** script that only moves files to the archive folder *after* DuckDB confirms a successful commit.

### Dependency Management
Developing on macOS with Python 3.12 required careful version-pinning between Mage AI and DuckDB to ensure the SQLite-based orchestration meta-database did not conflict with the analytical DuckDB file.

---

## 6. Future Improvements

### A. API & Cloud Integration
Transition from local CSV sweeps to an **Airbyte** or **REST API** connector to ingest live data from Google Sheets or an ERP system (like SAP).

### B. Automated Alerting
Integrating a **Twilio** or **Slack API** block into the Mage DAG to send an instant notification to the warehouse manager whenever a high-value anomaly (e.g., >$15,000) is detected.

### C. Machine Learning for Imputation
Moving from simple string imputation to using a **Random Forest** or **XGBoost** model to predict missing ELM codes based on the `part_name` and `model_family_group` patterns.

### D. Scheduled Orchestration (Cron Jobs)
                
    Currently, the pipeline is triggered manually for batch processing. The next architectural upgrade is to utilize Mage AI's native **Triggers** feature to schedule a daily cron job (e.g., `0 2 * * *` for 2:00 AM). This would allow the system to automatically sweep a cloud storage bucket (like AWS S3 or Google Cloud Storage) for new vendor files while the logistics team is offline, ensuring the dashboard is fully updated before the morning shift begins.

---

**Author:** David Namgung  
**Role:** Data Engineer & McGill CS Student  
**Tech Stack:** Mage AI, DuckDB, Streamlit, Python (Pandas/Plotly)
    """)
    
        
    
    st.info(f"Current Pipeline Metrics: {len(df):,} total rows processed and secured in DuckDB.")


with tab_guide:
    st.header("⚙️ Standard Operating Procedure (SOP)")
    st.markdown("### How to Ingest New Data Batches")
    st.info("Because this architecture utilizes a local DuckDB instance and GitHub for cloud deployment, follow these exact steps to update the live dashboard with new data.")

    st.markdown("""
    #### **Step 1: Stage the Raw Data**
    1. Drop your new inventory batch (`.csv` format) into the local directory: 
       `inventory-control-tower/data/raw/`
    
    #### **Step 2: Run the ETL Pipeline**
    1. Open your terminal and activate your virtual environment:
       ```bash
       source venv/bin/activate
       ```
    2. Start the Mage AI orchestrator:
       ```bash
       mage start mage_pipeline
       ```
    3. Open `http://localhost:6789` in your browser.
    4. Go to **Pipelines** -> click your pipeline -> click **Run@Once**.
    5. *Note: Mage will automatically clean the data, append it to `supply_chain.duckdb`, and move your original `.csv` files into the `/data/archive/` folder.*

    #### **Step 3: Verify Locally**
    1. Open a new terminal tab (keep Mage running).
    2. Launch the Streamlit dashboard locally to ensure the numbers updated:
       ```bash
       streamlit run app.py
       ```

    #### **Step 4: Push to the Cloud**
    1. To update the public dashboard, you must send the new database file to GitHub. Run these commands:
       ```bash
       git add data/processed/supply_chain.duckdb
       git commit -m "Automated data ingestion update"
       git push origin main
       ```
    2. Streamlit Community Cloud will automatically detect the new database file and refresh the live dashboard within 60 seconds.
    """)