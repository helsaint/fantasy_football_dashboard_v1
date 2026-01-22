import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

@st.cache_data
def create_fixture_adjusted_chart(df, player_name):
    # Filter data for specific player
    player_df = df[df['player_name'] == player_name]
    
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # 1. Add FDR as Background Bars (Secondary Axis)
    fig.add_trace(
        go.Bar(
            x=player_df['gw'],
            y=player_df['fdr'],
            name="Fixture Difficulty",
            marker_color=player_df['fdr'].map({1: 'green', 2: 'lightgreen', 3: 'yellow', 4: 'orange', 5: 'red'}),
            opacity=0.3,
            width=0.8
        ),
        secondary_y=True,
    )

    # 2. Add xGI (xG + xA) as a Line (Primary Axis)
    fig.add_trace(
        go.Scatter(
            x=player_df['gw'],
            y=player_df['expected_goal_involvements'],
            mode='lines+markers',
            name="Expected Goal Involvement (xGI)",
            line=dict(color='blue', width=3),
            hovertemplate="GW %{x}<br>xGI: %{y:.2f}"
        ),
        secondary_y=False,
    )

    # Styling for efficiency and clean UI
    fig.update_layout(
        title=f"Fixture-Adjusted Performance: {player_name}",
        hovermode="x unified",
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    # Set axis titles
    fig.update_yaxes(title_text="<b>Performance</b> (xGI)", secondary_y=False)
    fig.update_yaxes(title_text="<b>Difficulty</b> (FDR)", secondary_y=True, range=[0, 5])

    return fig