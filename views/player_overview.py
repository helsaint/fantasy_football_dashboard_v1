import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from utils.load_fpl_features import load_player_data

def show(filtered_df):
    st.header("Player Performance Overview")

    if 'fetched_fpl_data' not in st.session_state:
        st.session_state.fetched_fpl_data = None
    if 'filtered_player_data' not in st.session_state:
        st.session_state.filtered_player_data = None

    df_fpl_features = load_player_data()
    if st.session_state.fetched_fpl_data is None:
        st.session_state.fetched_fpl_data = df_fpl_features

    st.subheader("HTB Target Database")
    # 1. Create a dictionary to map ID -> Display Label
    # This makes lookups instant and clean
    player_options = st.session_state.fetched_fpl_data.set_index('player_id').apply(
        lambda x: f"{x['player_name']} ({x['team']})", axis=1
        ).to_dict()
    # Use selectbox as a search bar
    # index=None ensures it starts empty
    # 2. The Search Bar
    selected_id = st.selectbox(
        "Search for a player:",
        options=player_options.keys(), # This stores the player_id
        format_func=lambda x: player_options[x], # This shows "Name (Team)"
        index=None,
        placeholder="Type a name (e.g., 'Slayer')..."
        )
    # 3. Action based on selection
    if selected_id:
        # Pull the specific row for the unique ID
        player_data = st.session_state.fetched_fpl_data[
            st.session_state.fetched_fpl_data['player_id'] == selected_id].reset_index(drop=True)
        st.session_state.filtered_player_data = player_data

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Player Name", player_data.loc[0,'player_name'])
            st.caption(f"ID: {selected_id}")
        with col2:
            st.metric("Team", player_data.loc[0,'team'])
            st.write(f"**Team:** {player_data.loc[0,'team']}")

    if (
        st.session_state.filtered_player_data is not None
        ):
        col1, col2, col3, col4 = st.columns(4)
        player_data = st.session_state.filtered_player_data.copy()
    
        with col1:
            st.metric("Total Points", 
                      f"{st.session_state.filtered_player_data['total_points'].sum():,}")
        with col2:
            st.metric("Goals Scored", 
                      f"{st.session_state.filtered_player_data['goals_scored'].sum():,}")
        with col3:
            st.metric("Assists", 
                      f"{st.session_state.filtered_player_data['assists'].sum():,}")
        with col4:
            st.metric("Games over 60 mins", 
                      f"{st.session_state.filtered_player_data['played_60'].sum():,}")
        
        st.markdown("---")
        st.subheader("Residual Performance Analysis")
        player_data['goals_assists'] = player_data['goals_scored'] + player_data['assists']
        
        fig_rpa = go.Figure()
        fig_rpa.add_trace(
            go.Scatter(
                x=player_data['gw'],
                y=player_data['goals_assists'],
                mode='markers+lines',
                name='Goals/Assists',
            )
        )
        fig_rpa.add_trace(
            go.Scatter(
                x=player_data['gw'],
                y=player_data['expected_goal_involvements'],
                mode='markers+lines',
                name='Expected Goal Involvement',
            )
        )

        st.plotly_chart(fig_rpa, width='stretch', key="rpa_chart")
        st.write("This is mainly used for attacking players")
        st.write("- The Overperformer: If we see a player's points being consistently" \
        "above that of the expected goals involvement then this player is overperforming." \
        " The player is returning more points than the quality of their chances suggests." \
        " This indicates a strong finishing ability. If the player hasn't been consistent" \
        " like Haaland then expect a regression to the mean. The streak may be unsustainable" \
        " and you should consider transferring out the player as soon as there is a dip in" \
        " form")
        st.write("- The Underperfromer: This is shown by the expected goals and assists" \
        " line being consistently above the actual goals+assits lines. This indicates that" \
        " the player is getting into good positions but is not scoring. If this is unusual" \
        " behavior expect the player to eventually 'come good' and they are a candidate" \
        " as a differential buy.")
        st.write("- The Reliable Asset: The player is scoring the points we expect them" \
        " they are consistent and we can count on their points.")

        st.markdown("---")
        st.subheader("Noise vs Signal")

        fig_nsv = go.Figure()
        fig_nsv.add_trace(
            go.Scatter(
                x=player_data['gw'],
                y=player_data['total_points'],
                mode='markers+lines',
                name='Total Points',
            )
        )
        fig_nsv.add_trace(
            go.Scatter(
                x=player_data['gw'],
                y=player_data['pts_ewma'],
                mode='markers+lines',
                name='Weighted Moving Average',
            )
        )
        fig_nsv.add_trace(
            go.Scatter(
                x=player_data['gw'],
                y=player_data['pts_roll_5'],
                mode='markers+lines',
                name='Rolling 5',
            )
        )

        st.plotly_chart(fig_nsv, width='stretch', key="nsv_chart")
        st.write(" We use Total Points to see the ceiling, the Rolling 5 to capture the" \
        " current player's current form, and the EWMA to provide a weighted baseline that" \
        " filters out the chaos of a single gameweek.")
        st.write("- The Breakout: the Rolling 5 crosses above the Weighted Moving Average" \
        " The player is in a hot streak. Their current form is better than their season" \
        " average.")
        st.write("- The Slump: the Rolling 5 crosses below the Weighted Moving Average." \
        " The player's form has dropped below their baseline. They may be a good candidate" \
        " to bench.")
        st.write("- The Trap: the weighted moving average is steady but we see actual points" \
        " spikes. Don't chase this player unless their Weighted Moving Average is also" \
        " increasing.")


    
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