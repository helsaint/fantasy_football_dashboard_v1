import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
from utils.load_fpl_features import load_player_data

# Import view modules
from views import manager_analysis, value_analysis, performance_trends, player_overview
from views import test_view

# ========== PAGE CONFIGURATION ==========
st.set_page_config(
    page_title="Fantasy Football Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ========== SIDEBAR NAVIGATION ==========
st.sidebar.image("https://img.icons8.com/color/96/000000/football.png", width=80)
st.sidebar.title("⚽ Navigation")

# Navigation radio buttons
view = st.sidebar.radio(
    "Select Dashboard View:",
    [
        "📊 Player Overview", 
        #"📈 Performance Trends", 
        #"💰 Value Analysis",
        "👤 Manager Analysis",
        #"🧪 Test View",
    ],
    index=0
)

# Global filters in sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Global Filters")

# ========== DATA LOADING WITH CACHING ==========
df = load_player_data()

# Player multi-select
all_players = sorted(df['player_name'].unique())
selected_players = st.sidebar.multiselect(
    "Select Players:",
    options=all_players,
    default=all_players[:5]  # First 5 players by default
)

# Gameweek range slider
min_gw, max_gw = int(df['gw'].min()), int(df['gw'].max())
gw_range = st.sidebar.slider(
    "Gameweek Range:",
    min_value=min_gw,
    max_value=max_gw,
    value=(min_gw, max_gw)
)

# Filter data based on selections

if selected_players:
    filtered_df = df[
        (df['player_name'].isin(selected_players)) & 
        (df['gw'] >= gw_range[0]) & 
        (df['gw'] <= gw_range[1])
    ].copy()
else:
    filtered_df = df[
        (df['gw'] >= gw_range[0]) & 
        (df['gw'] <= gw_range[1])
    ].copy()

# Display data stats in sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("📁 Data Summary")
st.sidebar.metric("Players Selected", len(selected_players) if selected_players else "All")
st.sidebar.metric("Gameweeks", f"{gw_range[0]} - {gw_range[1]}")
st.sidebar.metric("Total Records", len(filtered_df))

# Download filtered data
st.sidebar.markdown("---")
csv = filtered_df.to_csv(index=False)
st.sidebar.download_button(
    label="📥 Download Filtered Data",
    data=csv,
    file_name=f"filtered_fantasy_data_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)

# ========== DASHBOARD VIEWS ==========
st.title("⚽ Fantasy Football Performance Dashboard")
st.markdown("Analyze player performance, trends, and value across gameweeks")

# View 1: Player Overview Dashboard
if view == "📊 Player Overview":
    player_overview.show(df)

# View 2: Performance Trends
elif view == "📈 Performance Trends":
    performance_trends.show(filtered_df)

# View 3: Value Analysis
elif view == "💰 Value Analysis":
    value_analysis.show(filtered_df)

# View 4: Manager Team Analysis
# ========== MANAGER TEAM ANALYZER VIEW WITH AUTO-DETECT ==========
elif view == "👤 Manager Analysis":
    manager_analysis.show(df)
# ========== TEST VIEW ==========
elif view == "🧪 Test View":
    test_view.show(filtered_df)
# ========== FOOTER ==========
st.markdown("---")
st.caption(f"Fantasy Football Dashboard • Data updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("Use the sidebar to navigate between different views and apply filters.")
