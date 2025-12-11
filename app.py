import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import numpy as np
from datetime import datetime
import requests

# Import view modules
from views import manager_analysis, value_analysis, performance_trends, player_overview
from views import position_analysis

# ========== PAGE CONFIGURATION ==========
st.set_page_config(
    page_title="Fantasy Football Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== DATA LOADING WITH CACHING ==========
@st.cache_data
def load_player_data():
    """Load and preprocess the player performance data"""
    try:
        # Try to load from the data folder
        data_path = Path(__file__).parent / "data" / "fpl_features.csv"
        df = pd.read_csv(data_path)
        
        # Basic data validation
        required_cols = ['player_name', 'gw', 'goals_scored', 'assists', 
                        'total_points', 'clean_sheets', 'now_cost',
                        'goals_conceded', 'saves']
        
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.error(f"Missing columns: {missing_cols}")
            # Create sample data if file doesn't have required columns
            return create_sample_data()
        
        # Data cleaning
        df['player_name'] = df['player_name'].astype(str)
        df['gw'] = pd.to_numeric(df['gw'], errors='coerce')
        df['goals_scored'] = pd.to_numeric(df['goals_scored'], errors='coerce').fillna(0)
        df['assists'] = pd.to_numeric(df['assists'], errors='coerce').fillna(0)
        df['total_points'] = pd.to_numeric(df['total_points'], errors='coerce').fillna(0)
        df['now_cost'] = pd.to_numeric(df['now_cost'], errors='coerce').fillna(0)
        
        # Calculate additional metrics
        df['goal_contributions'] = df['goals_scored'] + df['assists']
        df['points_per_million'] = df['total_points'] / (df['now_cost'] / 10)
        
        # Calculate form (average points over last 3 games)
        df = df.sort_values(['player_name', 'gw'])
        df['form'] = df.groupby('player_name')['total_points'].rolling(3, min_periods=1).mean().reset_index(level=0, drop=True)
        
        return df
        
    except FileNotFoundError:
        st.warning("⚠️ CSV file not found. Using sample data for demonstration.")
        return create_sample_data()

def create_sample_data():
    """Create sample data if CSV file is missing"""
    players = ['Haaland', 'Salah', 'Kane', 'De Bruyne', 'Son', 'Rashford', 
               'Bruno Fernandes', 'Saka', 'Martinez', 'Foden']
    
    data = []
    for player in players:
        for gw in range(1, 31):  # 30 gameweeks
            goals = np.random.poisson(0.7) if player in ['Haaland', 'Salah', 'Kane'] else np.random.poisson(0.3)
            assists = np.random.poisson(0.4) if player in ['De Bruyne', 'Bruno Fernandes'] else np.random.poisson(0.2)
            total_points = goals * 4 + assists * 3 + np.random.randint(0, 3)
            now_cost = np.random.randint(10000000, 15000000) if player in ['Haaland', 'Salah'] else np.random.randint(7000000, 10000000)
            
            data.append({
                'player_name': player,
                'gw': gw,
                'goals_scored': goals,
                'assists': assists,
                'total_points': total_points,
                'now_cost': now_cost
            })
    
    df = pd.DataFrame(data)
    df['goal_contributions'] = df['goals_scored'] + df['assists']
    df['points_per_million'] = df['total_points'] / (df['now_cost'] / 1000000)
    
    return df

# ========== SIDEBAR NAVIGATION ==========
st.sidebar.image("https://img.icons8.com/color/96/000000/football.png", width=80)
st.sidebar.title("⚽ Navigation")

# Navigation radio buttons
view = st.sidebar.radio(
    "Select Dashboard View:",
    [
        "📊 Player Overview", 
        "📈 Performance Trends", 
        "💰 Value Analysis",
        "👤 Manager Team Analysis",
        "📋 Position Distribution Analysis"
    ],
    index=0
)

# Global filters in sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Global Filters")

# Load data
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
    player_overview.show(filtered_df)

# View 2: Performance Trends
elif view == "📈 Performance Trends":
    performance_trends.show(filtered_df)

# View 3: Value Analysis
elif view == "💰 Value Analysis":
    value_analysis.show(filtered_df)

# View 4: Manager Team Analysis
# ========== MANAGER TEAM ANALYZER VIEW WITH AUTO-DETECT ==========
elif view == "👤 Manager Team Analysis":
    manager_analysis.show(df)

elif view == "📋 Position Distribution Analysis":
    position_analysis.show(df)

# ========== FOOTER ==========
st.markdown("---")
st.caption(f"Fantasy Football Dashboard • Data updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("Use the sidebar to navigate between different views and apply filters.")