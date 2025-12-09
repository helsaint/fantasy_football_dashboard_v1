import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

def show(filtered_df):
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