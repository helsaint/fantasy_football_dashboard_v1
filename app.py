import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import numpy as np
from datetime import datetime
import requests

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
        df['points_per_million'] = df['total_points'] / (df['now_cost'] / 1000000)
        
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
    print(filtered_df.columns)
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
    st.header("Player Value Analysis")
    # Calculate value metrics
    value_metrics = filtered_df.groupby('player_name').agg({
        'total_points': 'sum',
        'now_cost': 'mean',
        'points_per_million': 'mean',
        'gw': 'count'
    }).reset_index()
    
    value_metrics['value_millions'] = value_metrics['now_cost'] / 10
    value_metrics = value_metrics.rename(columns={'gw': 'games_played'})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Points per Million ($)")
        
        # Sort by value efficiency
        value_efficiency = value_metrics.nlargest(15, 'points_per_million')
        
        fig = px.bar(
            value_efficiency,
            x='player_name',
            y='points_per_million',
            color='points_per_million',
            color_continuous_scale='Teal',
            title="Most Efficient Players (Points per $M)",
            labels={'player_name': 'Player', 'points_per_million': 'Points per $M'}
        )
        st.plotly_chart(fig, width='stretch')
    
    with col2:
        st.subheader("Value vs Performance Scatter")
        
        fig = px.scatter(
            value_metrics,
            x='value_millions',
            y='total_points',
            size='games_played',
            color='points_per_million',
            hover_name='player_name',
            hover_data=['points_per_million'],
            title="Player Value vs Total Points",
            labels={
                'value_millions': 'Value (£M)',
                'total_points': 'Total Points',
                'points_per_million': 'Points/£M'
            },
            color_continuous_scale='Sunset'
        )
        
        # Add trend line
        z = np.polyfit(value_metrics['value_millions'], value_metrics['total_points'], 1)
        p = np.poly1d(z)
        
        fig.add_trace(
            go.Scatter(
                x=value_metrics['value_millions'],
                y=p(value_metrics['value_millions']),
                mode='lines',
                line=dict(color='gray', dash='dash'),
                name='Trend Line'
            )
        )
        
        st.plotly_chart(fig, width='stretch')
    
    # Value over time analysis
    st.subheader("Player Value Changes Over Gameweeks")
    
    # Pivot for heatmap
    value_pivot = filtered_df.pivot_table(
        index='player_name',
        columns='gw',
        values='now_cost',
        aggfunc='mean'
    )
    
    # Select top 10 players by total points for heatmap
    top_players_value = filtered_df.groupby('player_name')['total_points'].sum().nlargest(10).index
    value_pivot_top = value_pivot[value_pivot.index.isin(top_players_value)]
    
    if not value_pivot_top.empty:
        fig = px.imshow(
            value_pivot_top,
            labels=dict(x="Gameweek", y="Player", color="Value"),
            title="Player Value Heatmap (Top 10 Players)",
            aspect="auto",
            color_continuous_scale='RdBu_r'
        )
        st.plotly_chart(fig, width='stretch')
    
    # Value recommendations
    st.subheader("💰 Value Recommendations")
    
    # Identify underpriced players (high points per million, low value)
    value_metrics['recommendation_score'] = (
        value_metrics['points_per_million'] / value_metrics['value_millions']
    )
    
    # Get top 5 recommendations
    recommendations = value_metrics.nlargest(5, 'recommendation_score')
    
    for idx, row in recommendations.iterrows():
        with st.container():
            cols = st.columns([1, 3, 2, 2])
            with cols[0]:
                st.metric("Rank", f"#{idx+1}")
            with cols[1]:
                st.write(f"**{row['player_name']}**")
            with cols[2]:
                print(row['value_millions'])
                st.metric("Value", f"£{row['value_millions']:.1f}M")
            with cols[3]:
                st.metric("Pts/£M", f"{row['points_per_million']:.1f}")
            st.markdown("---")

# View 4: Manager Team Analysis
# ========== MANAGER TEAM ANALYZER VIEW ==========
elif view == "👤 Manager Team Analysis":
    st.header("👤 Manager Team Analysis")
    print(df.shape)
    # Explanation of what this does
    st.markdown("""
    This tool fetches your Fantasy Premier League team for a specific gameweek and analyzes each player's performance.
    Enter your FPL Manager ID below (you can find this in your FPL profile URL).
    """)
    
    # Create a two-column layout for inputs
    col1, col2 = st.columns([2, 1])
    
    with col1:
        manager_id = st.text_input(
            "Enter your FPL Manager ID:",
            placeholder="e.g., 1234567",
            help="Find this in your FPL profile URL: fantasy.premierleague.com/entry/1234567/event/15"
        )
    
    with col2:
        gw = st.number_input(
            "Gameweek:",
            min_value=1,
            max_value=38,
            value=15,
            help="Enter the gameweek number to analyze"
        )
    
    # Add position mapping
    POSITION_MAP = {
        1: "GK",
        2: "DEF",
        3: "MID",
        4: "FWD"
    }
    
    # Cache the API calls to avoid rate limiting
    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def fetch_manager_data(manager_id, gameweek):
        """Fetch manager team data from FPL API"""
        try:
            url = f"https://fantasy.premierleague.com/api/entry/{manager_id}/event/{gameweek}/picks/"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching manager data: {e}")
            return None
    
    @st.cache_data(ttl=86400)  # Cache for 24 hours
    def fetch_player_mapping():
        """Fetch player ID to name mapping from FPL API"""
        try:
            url = "https://fantasy.premierleague.com/api/bootstrap-static/"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Create mapping from element id to player name
            player_map = {}
            for player in data['elements']:
                player_map[player['id']] = player['web_name']
            
            return player_map
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching player mapping: {e}")
            return {}
    
    if manager_id and st.button("🔍 Fetch & Analyze Team", type="primary"):
        with st.spinner(f"Fetching manager {manager_id}'s team for GW{gw}..."):
            # Fetch data from FPL API
            manager_data = fetch_manager_data(manager_id, gw)
            
            if manager_data:
                # Show team summary
                entry_history = manager_data.get('entry_history', {})
                picks = manager_data.get('picks', [])
                chip_used = manager_data.get('active_chip', 'None')
                
                # Display team summary metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("GW Points", entry_history.get('points', 'N/A'))
                with col2:
                    st.metric("Total Points", entry_history.get('total_points', 'N/A'))
                with col3:
                    st.metric("Team Value", f"£{entry_history.get('value', 0)/10:.1f}M")
                with col4:
                    st.metric("Chip Used", chip_used if chip_used else "None")
                
                st.markdown("---")
                
                # Fetch player name mapping
                player_map = fetch_player_mapping()
                
                if player_map:
                    # Process picks and merge with our data
                    team_analysis = []
                    
                    for pick in picks:
                        element_id = pick['element']
                        player_name = player_map.get(element_id, f"Player_{element_id}")
                        
                        # Find this player in our dataframe for this gameweek
                        player_gw_data = df[
                            (df['player_name'] == player_name) & 
                            (df['gw'] == gw)
                        ]
                        
                        if not player_gw_data.empty:
                            # Get the most recent row for this player/gw
                            player_stats = player_gw_data.iloc[0].to_dict()
                        else:
                            # If no data found, use zeros
                            player_stats = {
                                'goals_scored': 0,
                                'assists': 0,
                                'total_points': 0,
                                'value': 0,
                                'goal_contributions': 0
                            }
                        
                        # Create analysis row
                        analysis_row = {
                            'element_id': element_id,
                            'player_name': player_name,
                            'position': POSITION_MAP.get(pick['element_type'], 'Unknown'),
                            'position_number': pick['position'],
                            'is_captain': pick['is_captain'],
                            'is_vice_captain': pick['is_vice_captain'],
                            'multiplier': pick['multiplier'],
                            'gw_points': player_stats.get('total_points', 0),
                            'goals': player_stats.get('goals_scored', 0),
                            'assists': player_stats.get('assists', 0),
                            'goal_contributions': player_stats.get('goal_contributions', 0),
                            'value': player_stats.get('value', 0),
                            'in_squad': pick['position'] <= 11  # Starting 11
                        }
                        
                        team_analysis.append(analysis_row)
                    
                    # Create DataFrame for display
                    analysis_df = pd.DataFrame(team_analysis)
                    
                    # Sort by position number (starting lineup first, then bench)
                    analysis_df = analysis_df.sort_values('position_number')
                    
                    # Display the team analysis
                    st.subheader("📊 Team Analysis")
                    
                    # Create tabs for different views
                    summary_tab, detailed_tab, captain_tab = st.tabs(["Summary", "Detailed View", "Captain Analysis"])
                    
                    with summary_tab:
                        # Display starting XI and bench separately
                        st.write("### Starting XI")
                        starting_xi = analysis_df[analysis_df['in_squad']].copy()
                        
                        if not starting_xi.empty:
                            # Format for display
                            display_df = starting_xi[['player_name', 'position', 'gw_points', 'goals', 'assists', 'multiplier']].copy()
                            display_df['multiplier'] = display_df['multiplier'].apply(lambda x: f"{x}×")
                            display_df['captaincy'] = starting_xi.apply(
                                lambda row: "©" if row['is_captain'] else ("VC" if row['is_vice_captain'] else ""),
                                axis=1
                            )
                            
                            # Reorder columns
                            display_df = display_df[['captaincy', 'player_name', 'position', 'gw_points', 'goals', 'assists', 'multiplier']]
                            
                            st.dataframe(
                                display_df.style.format({
                                    'gw_points': '{:.0f}'
                                }).apply(
                                    lambda row: ['background-color: #e8f5e9' if row.name == 0 else '' for _ in row],
                                    axis=1
                                ),
                                width='stretch'
                            )
                            
                            # Calculate team metrics
                            total_points = starting_xi['gw_points'].sum()
                            captain_row = starting_xi[starting_xi['is_captain']]
                            captain_points = 0
                            if not captain_row.empty:
                                captain_multiplier = captain_row.iloc[0]['multiplier']
                                captain_base = captain_row.iloc[0]['gw_points']
                                captain_points = captain_base * captain_multiplier - captain_base
                            
                            st.write(f"**Starting XI Total Points:** {total_points}")
                            if captain_points > 0:
                                st.write(f"**Captain Bonus Points:** +{captain_points}")
                                st.write(f"**Total with Captain Bonus:** {total_points + captain_points}")
                        
                        st.write("### Bench")
                        bench = analysis_df[~analysis_df['in_squad']].copy()
                        if not bench.empty:
                            bench_display = bench[['player_name', 'position', 'gw_points']]
                            st.dataframe(bench_display, width='stretch')
                            bench_points = bench['gw_points'].sum()
                            st.write(f"**Bench Points:** {bench_points}")
                    
                    with detailed_tab:
                        # Show full detailed table
                        detailed_df = analysis_df[['player_name', 'position', 'is_captain', 'is_vice_captain', 
                                                  'multiplier', 'gw_points', 'goals', 'assists', 
                                                  'goal_contributions', 'value']].copy()
                        
                        # Format values
                        detailed_df['is_captain'] = detailed_df['is_captain'].map({True: '✓', False: ''})
                        detailed_df['is_vice_captain'] = detailed_df['is_vice_captain'].map({True: '✓', False: ''})
                        detailed_df['value'] = detailed_df['value'].apply(lambda x: f"£{x/1000000:.1f}M" if x > 0 else "N/A")
                        
                        st.dataframe(
                            detailed_df.style.apply(
                                lambda row: ['font-weight: bold' if row['is_captain'] == '✓' else '' for _ in row],
                                axis=1
                            ).apply(
                                lambda row: ['color: #1e88e5' if row['is_vice_captain'] == '✓' else '' for _ in row],
                                axis=1
                            ),
                            width='stretch',
                            height=400
                        )
                    
                    with captain_tab:
                        st.subheader("Captain Performance Analysis")
                        
                        # Find captain
                        captain_data = analysis_df[analysis_df['is_captain']]
                        
                        if not captain_data.empty:
                            captain = captain_data.iloc[0]
                            
                            col1, col2 = st.columns([1, 2])
                            
                            with col1:
                                st.metric("Captain", captain['player_name'])
                                st.metric("Base Points", captain['gw_points'])
                                st.metric("Multiplier", f"{captain['multiplier']}×")
                                st.metric("Total Points", captain['gw_points'] * captain['multiplier'])
                            
                            with col2:
                                # Get captain's historical performance
                                captain_history = df[df['player_name'] == captain['player_name']]
                                
                                if not captain_history.empty:
                                    # Plot captain's form
                                    fig = px.line(
                                        captain_history,
                                        x='gw',
                                        y='total_points',
                                        markers=True,
                                        title=f"{captain['player_name']}'s Points per Gameweek",
                                        labels={'gw': 'Gameweek', 'total_points': 'Points'}
                                    )
                                    fig.add_hline(y=captain_history['total_points'].mean(), 
                                                line_dash="dash", 
                                                annotation_text=f"Average: {captain_history['total_points'].mean():.1f}")
                                    fig.update_traces(line_color='#FF6B6B', line_width=3)
                                    st.plotly_chart(fig, width='stretch')
                                else:
                                    st.info(f"No historical data found for {captain['player_name']}")
                            
                            # Analyze if captain was optimal choice
                            st.subheader("Was this the optimal captain choice?")
                            
                            # Find highest scoring player in the team
                            highest_scorer = analysis_df.loc[analysis_df['gw_points'].idxmax()]
                            
                            if highest_scorer['player_name'] != captain['player_name']:
                                points_diff = (highest_scorer['gw_points'] * 2) - (captain['gw_points'] * captain['multiplier'])
                                st.warning(f"❌ **Suboptimal Choice:** {highest_scorer['player_name']} scored {highest_scorer['gw_points']} points vs {captain['player_name']}'s {captain['gw_points']} points.")
                                st.write(f"You missed out on **{points_diff}** additional points!")
                            else:
                                st.success(f"✅ **Optimal Choice:** {captain['player_name']} was your highest scoring player!")
                        
                        else:
                            st.info("No captain selected for this gameweek")
                    
                    # Add some insights
                    st.markdown("---")
                    st.subheader("📈 Team Insights")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        # Best performer
                        best_player = analysis_df.loc[analysis_df['gw_points'].idxmax()]
                        st.metric("Best Performer", best_player['player_name'], best_player['gw_points'])
                    
                    with col2:
                        # Points per position
                        points_by_pos = analysis_df.groupby('position')['gw_points'].sum()
                        if not points_by_pos.empty:
                            best_position = points_by_pos.idxmax()
                            st.metric("Best Position", best_position, int(points_by_pos.max()))
                    
                    with col3:
                        # Average points per player
                        avg_points = analysis_df['gw_points'].mean()
                        st.metric("Avg Points/Player", f"{avg_points:.1f}")
                    
                    # Transfer suggestions based on form
                    st.subheader("💡 Transfer Suggestions")
                    
                    # Identify underperforming players (in starting lineup, low points)
                    underperformers = analysis_df[
                        (analysis_df['in_squad']) & 
                        (analysis_df['gw_points'] < analysis_df['gw_points'].median())
                    ]
                    
                    if not underperformers.empty:
                        st.write("Consider replacing these underperforming players:")
                        for _, player in underperformers.iterrows():
                            st.write(f"- **{player['player_name']}** ({player['position']}): {player['gw_points']} points")
                    else:
                        st.success("Your starting XI is performing well above average!")
                
                else:
                    st.error("Could not fetch player information from FPL API.")
            else:
                st.error("Could not fetch manager data. Please check your Manager ID and Gameweek.")
    
    else:
        # Show instructions when no input
        st.info("👆 Enter your FPL Manager ID and Gameweek above to analyze your team.")
        
        # Example data
        st.markdown("### Example")
        st.code("""
        Manager ID: 1234567 (from your FPL profile URL)
        Gameweek: 15
        
        This would fetch: https://fantasy.premierleague.com/api/entry/1234567/event/15/picks/
        """)
        
        # Tips section
        st.markdown("### 💡 Tips")
        st.markdown("""
        1. Find your Manager ID in your FPL profile URL
        2. The API provides real-time team data
        3. Your CSV data adds historical performance context
        4. Use this to make informed transfer decisions
        """)
# ========== FOOTER ==========
st.markdown("---")
st.caption(f"Fantasy Football Dashboard • Data updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("Use the sidebar to navigate between different views and apply filters.")