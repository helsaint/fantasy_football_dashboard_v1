import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

def show(filtered_df):
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