import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

def show(df):
    st.header("👤 Manager Team Analysis")
    
    # Explanation of what this does
    st.markdown("""
    This tool fetches your Fantasy Premier League team and analyzes each player's performance.
    Enter your FPL Manager ID below (you can find this in your FPL profile URL).
    """)
    
    # Cache the bootstrap-static endpoint which contains current gameweek
    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def fetch_fpl_bootstrap():
        """Fetch bootstrap-static data from FPL API"""
        try:
            url = "https://fantasy.premierleague.com/api/bootstrap-static/"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching FPL data: {e}")
            return None
    
    # Get current gameweek from API
    fpl_data = fetch_fpl_bootstrap()
    
    if fpl_data:
        # Extract current gameweek
        events = fpl_data.get('events', [])
        current_gw = None
        
        # Find the current event (gameweek)
        for event in events:
            if event.get('is_current'):
                current_gw = event.get('id')
                break
        
        # If no current event found, use the next event
        if not current_gw:
            for event in events:
                if event.get('is_next'):
                    current_gw = event.get('id')
                    break
        
        # Fallback to the last event
        if not current_gw and events:
            current_gw = max(event.get('id', 1) for event in events)
        
        # Get event details for display
        current_event_name = None
        if current_gw:
            for event in events:
                if event.get('id') == current_gw:
                    current_event_name = event.get('name', f'Gameweek {current_gw}')
                    break
        
        # Display current gameweek info
        if current_gw:
            st.success(f"✅ **Current Gameweek Detected:** {current_event_name}")
        else:
            st.warning("⚠️ Could not detect current gameweek. Defaulting to GW1.")
            current_gw = 1
            current_event_name = "Gameweek 1"
    else:
        st.warning("⚠️ Could not fetch FPL data. Defaulting to GW1.")
        current_gw = 1
        current_event_name = "Gameweek 1"
    
    # Create input columns with auto-detected gameweek
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        manager_id = st.text_input(
            "Enter your FPL Manager ID:",
            placeholder="e.g., 1234567",
            help="Find this in your FPL profile URL: fantasy.premierleague.com/entry/1234567/event/15"
        )
    
    with col2:
        # Let user choose between current GW or specific GW
        gw_mode = st.radio(
            "Gameweek:",
            ["Current", "Specific"],
            horizontal=True,
            help="Choose whether to analyze current or specific gameweek"
        )
    
    with col3:
        if gw_mode == "Current":
            gw = current_gw
            st.metric("Gameweek", f"GW{gw}")
        else:
            # Show slider for specific gameweek selection
            gw = st.number_input(
                "Select GW:",
                min_value=1,
                max_value=38,
                value=current_gw,
                key="gw_specific",
                help="Select a specific gameweek"
            )
    
    # Add position mapping
    POSITION_MAP = {
        1: "GK",
        2: "DEF", 
        3: "MID",
        4: "FWD"
    }
    
    # Cache the API calls to avoid rate limiting
    @st.cache_data(ttl=300)  # Cache for 5 minutes (shorter for manager data)
    def fetch_manager_data(manager_id, gameweek):
        """Fetch manager team data from FPL API"""
        try:
            url = f"https://fantasy.premierleague.com/api/entry/{manager_id}/event/{gameweek}/picks/"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if response.status_code == 404:
                st.error(f"Manager ID {manager_id} not found or no data for GW{gameweek}.")
            else:
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
            
            # Create mapping from element id to player info
            player_map = {}
            for player in data['elements']:
                player_map[player['id']] = {
                    'web_name': player['web_name'],
                    'team_code': player['team_code'],
                    'element_type': player['element_type']
                }
            
            # Team mapping for display
            teams = {team['code']: team['name'] for team in data['teams']}
            
            return player_map, teams
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching player mapping: {e}")
            return {}, {}
    
    # Add gameweek status indicator
    if fpl_data and 'events' in fpl_data:
        for event in fpl_data['events']:
            if event.get('id') == gw:
                deadline_passed = event.get('deadline_time_epoch', 0) < datetime.now().timestamp()
                if event.get('is_current'):
                    if deadline_passed:
                        st.info(f"⏳ GW{gw} is in progress. Next deadline: {event.get('deadline_time_formatted', 'N/A')}")
                    else:
                        st.info(f"⏰ GW{gw} deadline: {event.get('deadline_time_formatted', 'N/A')}")
                break
    
    if manager_id and st.button("🔍 Fetch & Analyze Team", type="primary"):
        with st.spinner(f"Fetching manager {manager_id}'s team for GW{gw}..."):
            # Fetch data from FPL API
            manager_data = fetch_manager_data(manager_id, gw)
            
            if manager_data:
                # Show team summary
                entry_history = manager_data.get('entry_history', {})
                picks = manager_data.get('picks', [])
                chip_used = manager_data.get('active_chip', 'None')
                
                # Display team summary metrics in expandable section
                with st.expander("📊 Team Summary", expanded=True):
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        st.metric("GW Points", entry_history.get('points', 'N/A'))
                    with col2:
                        st.metric("Total Points", entry_history.get('total_points', 'N/A'))
                    with col3:
                        st.metric("Team Value", f"${entry_history.get('value', 0)/10:.1f}M")
                    with col4:
                        st.metric("Chip Used", chip_used if chip_used else "None")
                    with col5:
                        rank = entry_history.get('overall_rank', 'N/A')
                        if rank != 'N/A':
                            st.metric("Overall Rank", f"{rank:,}")
                        else:
                            st.metric("Overall Rank", "N/A")
                
                st.markdown("---")
                
                # Fetch player name mapping
                player_map, teams = fetch_player_mapping()
                
                if player_map:
                    # Process picks and merge with our data
                    team_analysis = []
                    
                    for pick in picks:
                        element_id = pick['element']
                        player_info = player_map.get(element_id, {})
                        player_name = player_info.get('web_name', f"Player_{element_id}")
                        
                        # Find this player in our dataframe for this gameweek
                        player_gw_data = df[
                            (df['player_name'] == player_name) & 
                            (df['gw'] == gw)
                        ]
                        
                        if not player_gw_data.empty:
                            # Get the most recent row for this player/gw
                            player_stats = player_gw_data.iloc[0].to_dict()
                        else:
                            # If no data found, check for any historical data for this player
                            player_history = df[df['player_name'] == player_name]
                            if not player_history.empty:
                                # Use average of last 3 games or overall average
                                recent_games = player_history.nlargest(3, 'gw')
                                player_stats = {
                                    'goals_scored': recent_games['goals_scored'].mean(),
                                    'assists': recent_games['assists'].mean(),
                                    'total_points': recent_games['total_points'].mean(),
                                    'value': player_history['now_cost'].iloc[-1] if len(player_history) > 0 else 0,
                                    'goal_contributions': recent_games['goals_scored'].mean() + recent_games['assists'].mean()
                                }
                            else:
                                # No data at all
                                player_stats = {
                                    'goals_scored': 0,
                                    'assists': 0,
                                    'total_points': 0,
                                    'value': 0,
                                    'goal_contributions': 0
                                }
                        
                        # Get team name
                        team_code = player_info.get('team_code', 0)
                        team_name = teams.get(team_code, "Unknown")
                        
                        # Create analysis row
                        analysis_row = {
                            'element_id': element_id,
                            'player_name': player_name,
                            'team': team_name,
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
                    st.subheader(f"📊 Team Analysis - GW{gw}")
                    
                    # Create tabs for different views
                    summary_tab, detailed_tab, captain_tab, insights_tab = st.tabs(
                        ["🎯 Summary", "📋 Detailed", "⭐ Captain", "💡 Insights"]
                    )
                    
                    with summary_tab:
                        # Display starting XI and bench separately
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.write("### Starting XI")
                            starting_xi = analysis_df[analysis_df['in_squad']].copy()
                            
                            if not starting_xi.empty:
                                # Create a visually appealing display
                                for idx, player in starting_xi.iterrows():
                                    # Create columns for player card
                                    player_col1, player_col2, player_col3 = st.columns([1, 3, 2])
                                    
                                    with player_col1:
                                        # Position badge with color coding
                                        pos_colors = {'GK': '#4CAF50', 'DEF': '#2196F3', 'MID': '#FF9800', 'FWD': '#F44336'}
                                        pos_color = pos_colors.get(player['position'], '#757575')
                                        st.markdown(f"""
                                        <div style='background-color:{pos_color}; color:white; padding:5px; 
                                                    border-radius:5px; text-align:center; font-weight:bold;'>
                                            {player['position']}
                                        </div>
                                        """, unsafe_allow_html=True)
                                    
                                    with player_col2:
                                        # Player name with captaincy indicator
                                        captain_indicator = ""
                                        if player['is_captain']:
                                            captain_indicator = "C"
                                        elif player['is_vice_captain']:
                                            captain_indicator = " VC"
                                        
                                        st.markdown(f"**{player['player_name']}**{captain_indicator}")
                                        st.caption(f"{player['team']}")
                                    
                                    with player_col3:
                                        # Points with multiplier
                                        base_points = player['gw_points']
                                        multiplier = player['multiplier']
                                        total_points = base_points * multiplier
                                        
                                        if multiplier > 1:
                                            st.markdown(f"**{total_points:.1f}** pts")
                                            st.caption(f"{base_points:.1f} × {multiplier}")
                                        else:
                                            st.markdown(f"**{base_points:.1f}** pts")
                                        
                                        # Goal contributions
                                        if player['goal_contributions'] > 0:
                                            st.caption(f"⚽ {player['goals']:.1f} 🅰️ {player['assists']:.1f}")
                                    
                                    st.markdown("---")
                        
                        with col2:
                            st.write("### Bench")
                            bench = analysis_df[~analysis_df['in_squad']].copy()
                            if not bench.empty:
                                for idx, player in bench.iterrows():
                                    st.write(f"**{player['player_name']}**")
                                    st.caption(f"{player['position']} | {player['gw_points']:.1f} pts")
                                    if player['goal_contributions'] > 0:
                                        st.caption(f"⚽{player['goals']:.1f} 🅰️{player['assists']:.1f}")
                                    st.markdown("---")
                    
                    with detailed_tab:
                        # Show full detailed table
                        print(analysis_df.columns)
                        detailed_df = analysis_df[['player_name', 'team', 'position', 'is_captain', 'is_vice_captain', 
                                                  'multiplier', 'gw_points', 'goals', 'assists', 
                                                  'goal_contributions', 'value', 'in_squad']].copy()
                        
                        # Format values
                        detailed_df['is_captain'] = detailed_df['is_captain'].map({True: 'C', False: ''})
                        detailed_df['is_vice_captain'] = detailed_df['is_vice_captain'].map({True: 'VC', False: ''})
                        detailed_df['value'] = detailed_df['value'].apply(lambda x: f"${x/10:.1f}M" if x > 0 else "N/A")
                        detailed_df['multiplier'] = detailed_df['multiplier'].apply(lambda x: f"{x}×")
                        
                        # Style and display
                        st.dataframe(
                            detailed_df.style.apply(
                                lambda row: ['background-color: #FFC10733' if row['is_captain'] == 'C' else '' for _ in row],
                                axis=1
                            ).apply(
                                lambda row: ['background-color: #2196F333' if row['is_vice_captain'] == 'VC' else '' for _ in row],
                                axis=1
                            ).apply(
                                lambda row: ['background-color: #9E9E9E1A' if not row['in_squad'] else '' for _ in row],
                                axis=1
                            ),
                            width='stretch',
                            height=400
                        )
                    
                    with captain_tab:
                        # Enhanced captain analysis
                        captain_data = analysis_df[analysis_df['is_captain']]
                        
                        if not captain_data.empty:
                            captain = captain_data.iloc[0]
                            
                            # Captain card
                            st.subheader("Captain Analysis")
                            
                            col1, col2 = st.columns([1, 2])
                            
                            with col1:
                                st.markdown(f"""
                                <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                            padding: 20px; border-radius: 10px; color: white; text-align: center;'>
                                    <h3>{captain['player_name']}</h3>
                                    <p style='font-size: 48px; margin: 10px 0;'>{captain['gw_points'] * captain['multiplier']:.1f}</p>
                                    <p>Total Points (×{captain['multiplier']})</p>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Captain stats
                                st.metric("Base Points", f"{captain['gw_points']:.1f}")
                                st.metric("Multiplier", f"{captain['multiplier']}×")
                                st.metric("Team", captain['team'])
                            
                            with col2:
                                # Get captain's historical performance
                                captain_history = df[df['player_name'] == captain['player_name']]
                                
                                if not captain_history.empty:
                                    # Plot captain's form with enhanced visualization
                                    fig = go.Figure()
                                    
                                    # Line for points
                                    fig.add_trace(go.Scatter(
                                        x=captain_history['gw'],
                                        y=captain_history['total_points'],
                                        mode='lines+markers',
                                        name='Points',
                                        line=dict(color='#FF6B6B', width=3),
                                        marker=dict(size=8)
                                    ))
                                    
                                    # Bar for goal contributions
                                    fig.add_trace(go.Bar(
                                        x=captain_history['gw'],
                                        y=captain_history.get('goal_contributions', 0),
                                        name='Goal Contributions',
                                        marker_color='rgba(255, 193, 7, 0.7)',
                                        yaxis='y2'
                                    ))
                                    
                                    # Highlight current gameweek
                                    if gw in captain_history['gw'].values:
                                        gw_points = captain_history[captain_history['gw'] == gw]['total_points'].iloc[0]
                                        fig.add_trace(go.Scatter(
                                            x=[gw],
                                            y=[gw_points],
                                            mode='markers',
                                            marker=dict(size=12, color='#4CAF50'),
                                            name='Current GW'
                                        ))
                                    
                                    fig.update_layout(
                                        title=f"{captain['player_name']}'s Performance History",
                                        xaxis_title="Gameweek",
                                        yaxis_title="Points",
                                        yaxis2=dict(
                                            title="Goal Contributions",
                                            overlaying='y',
                                            side='right'
                                        ),
                                        hovermode='x unified'
                                    )
                                    
                                    st.plotly_chart(fig, width='stretch')
                                    
                                    # Average stats
                                    avg_points = captain_history['total_points'].mean()
                                    st.metric("Season Average", f"{avg_points:.1f} pts/GW")
                                    
                                    # Compare with current performance
                                    if gw in captain_history['gw'].values:
                                        current_points = captain_history[captain_history['gw'] == gw]['total_points'].iloc[0]
                                        diff = current_points - avg_points
                                        st.metric("vs Season Avg", f"{current_points:.1f}", f"{diff:+.1f}")
                                else:
                                    st.info(f"No historical data found for {captain['player_name']}")
                        
                        else:
                            st.info("No captain selected for this gameweek")
                    
                    with insights_tab:
                        # Advanced insights
                        st.subheader("Team Insights & Recommendations")
                        
                        # 1. Points distribution
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Points by position
                            points_by_pos = analysis_df.groupby('position')['gw_points'].sum()
                            if not points_by_pos.empty:
                                fig = px.pie(
                                    values=points_by_pos.values,
                                    names=points_by_pos.index,
                                    title="Points Distribution by Position",
                                    color_discrete_sequence=px.colors.qualitative.Set3
                                )
                                st.plotly_chart(fig, width='stretch')
                        
                        with col2:
                            # Value efficiency
                            analysis_df['value_efficiency'] = analysis_df['gw_points'] / (analysis_df['value'] / 10 + 0.001)
                            efficient_players = analysis_df.nlargest(3, 'value_efficiency')
                            
                            st.write("**Most Value-Efficient Players:**")
                            for _, player in efficient_players.iterrows():
                                efficiency = player['value_efficiency']
                                st.write(f"✅ **{player['player_name']}**: {efficiency:.2f} pts/$M")
                        
                        # 2. Transfer suggestions
                        st.subheader("💡 Transfer Recommendations")
                        
                        # Identify underperformers
                        starting_players = analysis_df[analysis_df['in_squad']]
                        if not starting_players.empty:
                            avg_points = starting_players['gw_points'].mean()
                            underperformers = starting_players[starting_players['gw_points'] < avg_points * 0.7]
                            
                            if not underperformers.empty:
                                st.write("Consider replacing these underperforming players:")
                                for _, player in underperformers.iterrows():
                                    st.write(f"""
                                    - **{player['player_name']}** ({player['position']}, {player['team']}):
                                      {player['gw_points']:.1f} pts (avg: {avg_points:.1f} pts)
                                    """)
                            else:
                                st.success("🎉 All your starters are performing at or above 70% of team average!")
                        
                        # 3. Optimal lineup check
                        st.subheader("📋 Optimal Lineup Check")
                        
                        # Check if bench has players who outscored starters
                        bench_players = analysis_df[~analysis_df['in_squad']]
                        worst_starter = starting_players.nsmallest(1, 'gw_points')
                        
                        if not bench_players.empty and not worst_starter.empty:
                            best_bench = bench_players.nlargest(1, 'gw_points')
                            
                            if not best_bench.empty:
                                bench_points = best_bench.iloc[0]['gw_points']
                                starter_points = worst_starter.iloc[0]['gw_points']
                                
                                if bench_points > starter_points:
                                    st.warning(f"""
                                    ⚠️ **Suboptimal Lineup Alert!**
                                    
                                    {best_bench.iloc[0]['player_name']} on bench scored **{bench_points:.1f} pts**
                                    while {worst_starter.iloc[0]['player_name']} started with **{starter_points:.1f} pts**
                                    
                                    You missed out on **{bench_points - starter_points:.1f} points**!
                                    """)
                                else:
                                    st.success("✅ Your starting lineup is optimal!")
                
                else:
                    st.error("Could not fetch player information from FPL API.")
            else:
                st.error("Could not fetch manager data. Please check your Manager ID.")
    
    else:
        # Show instructions when no input
        st.info("👆 Enter your FPL Manager ID above to analyze your team.")
        
        # Example with auto-detection
        st.markdown("### 📱 How It Works")
        st.markdown("""
        1. **Enter your Manager ID** (from your FPL profile URL)
        2. **Choose gameweek mode**: Current (auto-detected) or Specific
        3. **Click "Fetch & Analyze Team"** to see detailed insights
        
        The system automatically:
        - Detects the current gameweek from FPL API
        - Fetches your team data
        - Merges with historical performance data
        - Provides actionable insights
        """)
        
        # Quick example
        with st.expander("🔍 Example Analysis"):
            st.code("""
            Manager ID: 1234567 (from URL: fantasy.premierleague.com/entry/1234567/)
            
            Auto-detected: GW15 (Current Gameweek)
            
            Analysis includes:
            - Starting XI with points breakdown
            - Captain performance analysis
            - Bench evaluation
            - Transfer recommendations
            - Value efficiency metrics
            """)