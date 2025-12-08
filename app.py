import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import numpy as np
from datetime import datetime
import requests

# Import view modules
from views import manager_analysis, value_analysis

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
        "👤 Manager Team Analysis"  # Add this line
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
    st.header("Player Performance Overview")
    
    # Top row: Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_points = filtered_df['total_points'].sum()
        st.metric("Total Points", f"{total_points:,}")
    
    with col2:
        total_goals = filtered_df['goals_scored'].sum()
        st.metric("Total Goals", f"{total_goals:,}")
    
    with col3:
        total_assists = filtered_df['assists'].sum()
        st.metric("Total Assists", f"{total_assists:,}")
    
    with col4:
        avg_points = filtered_df['total_points'].mean()
        st.metric("Avg Points/GW", f"{avg_points:.1f}")
    
    st.markdown("---")
    
    # Middle row: Two charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Top Performers (Total Points)")
        
        # Aggregate by player
        player_totals = filtered_df.groupby('player_name').agg({
            'total_points': 'sum',
            'goals_scored': 'sum',
            'assists': 'sum',
            'now_cost': 'mean'
        }).reset_index()
        
        # Top 10 players
        top_players = player_totals.nlargest(10, 'total_points')
        
        fig = px.bar(
            top_players,
            x='player_name',
            y='total_points',
            color='total_points',
            color_continuous_scale='Viridis',
            title="Top 10 Players by Total Points",
            labels={'player_name': 'Player', 'total_points': 'Total Points'}
        )
        st.plotly_chart(fig, width='stretch')
    
    with col2:
        st.subheader("Points Distribution by Player")
        
        # Box plot of points distribution
        fig = px.box(
            filtered_df,
            x='player_name',
            y='total_points',
            color='player_name',
            points="all",
            title="Points Distribution (Box Plot)",
            labels={'player_name': 'Player', 'total_points': 'Points'}
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, width='stretch')
    
    # Bottom row: Data table
    st.subheader("Detailed Player Data")
    
    # Aggregate for table view
    summary_df = filtered_df.groupby('player_name').agg({
        'total_points': ['sum', 'mean', 'max'],
        'goals_scored': 'sum',
        'assists': 'sum',
        'now_cost': 'mean',
        'gw': 'count'
    }).round(1)
    
    # Flatten column names
    summary_df.columns = ['Total Points', 'Avg Points', 'Best GW', 'Goals', 'Assists', 'Avg Value', 'GWs Played']
    summary_df = summary_df.sort_values('Total Points', ascending=False)
    
    # Display with formatting
    st.dataframe(
        summary_df.style.format({
            'Total Points': '{:.0f}',
            'Avg Points': '{:.1f}',
            'Best GW': '{:.0f}',
            'Goals': '{:.0f}',
            'Assists': '{:.0f}',
            'Avg Value': '${:.0f}'
        }).background_gradient(subset=['Total Points'], cmap='YlOrRd'),
        width='stretch',
        height=400
    )

# View 2: Performance Trends
elif view == "📈 Performance Trends":
    st.header("Performance Trends Over Time")
    
    # Player selector for trend view
    trend_players = st.multiselect(
        "Select players for trend analysis:",
        options=filtered_df['player_name'].unique(),
        default=filtered_df['player_name'].unique()[:3]
    )
    
    if trend_players:
        trend_df = filtered_df[filtered_df['player_name'].isin(trend_players)]
        
        # Create tabs for different trends
        trend_tab1, trend_tab2, trend_tab3 = st.tabs(["Points Trend", "Goal Contributions", "Form Tracker"])
        
        with trend_tab1:
            st.subheader("Total Points Per Gameweek")
            
            fig = px.line(
                trend_df,
                x='gw',
                y='total_points',
                color='player_name',
                markers=True,
                title="Points Progression by Gameweek",
                labels={'gw': 'Gameweek', 'total_points': 'Points'}
            )
            st.plotly_chart(fig, width='stretch')
        
        with trend_tab2:
            st.subheader("Goal Contributions (Goals + Assists)")
            
            # Create stacked bar chart
            trend_melted = trend_df.melt(
                id_vars=['player_name', 'gw'],
                value_vars=['goals_scored', 'assists'],
                var_name='contribution_type',
                value_name='count'
            )
            
            fig = px.bar(
                trend_melted,
                x='gw',
                y='count',
                color='contribution_type',
                facet_row='player_name',
                title="Goal Contributions Breakdown",
                labels={'gw': 'Gameweek', 'count': 'Count'},
                category_orders={'contribution_type': ['goals_scored', 'assists']},
                color_discrete_map={'goals_scored': '#FF6B6B', 'assists': '#4ECDC4'}
            )
            st.plotly_chart(fig, width='stretch')
        
        with trend_tab3:
            st.subheader("Player Form (3-GW Rolling Average)")
            
            # Calculate form for selected players
            form_data = []
            for player in trend_players:
                player_data = trend_df[trend_df['player_name'] == player].copy()
                player_data['form'] = player_data['total_points'].rolling(3, min_periods=1).mean()
                form_data.append(player_data)
            
            form_df = pd.concat(form_data)
            
            fig = px.line(
                form_df,
                x='gw',
                y='form',
                color='player_name',
                markers=True,
                title="Form Tracker (3-Gameweek Rolling Average)",
                labels={'gw': 'Gameweek', 'form': 'Average Points'}
            )
            st.plotly_chart(fig, width='stretch')
    
    else:
        st.info("Please select at least one player to view trends.")

# View 3: Value Analysis
elif view == "💰 Value Analysis":
    value_analysis.show(filtered_df)

# View 4: Manager Team Analysis
# ========== MANAGER TEAM ANALYZER VIEW WITH AUTO-DETECT ==========
elif view == "👤 Manager Team Analysis":
    manager_analysis.show(df)

# ========== FOOTER ==========
st.markdown("---")
st.caption(f"Fantasy Football Dashboard • Data updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("Use the sidebar to navigate between different views and apply filters.")