import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

def show(filtered_df):
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
                'value_millions': 'Value ($M)',
                'total_points': 'Total Points',
                'points_per_million': 'Points/$M'
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
                st.metric("Value", f"${row['value_millions']:.1f}M")
            with cols[3]:
                st.metric("Pts/$M", f"{row['points_per_million']:.1f}")
            st.markdown("---")