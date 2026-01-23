import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import numpy as np
from utils.scatter_plot import create_hover_text
from plotly.subplots import make_subplots

@st.cache_data
def create_fixture_adjusted_chart(**kwargs):
    
    manager_df = kwargs.get("manager_df", pd.DataFrame())
    player_id = kwargs.get("player_id", 1)
    player_name = kwargs.get("player_name", "Player")
    #fig = kwargs.get("fig", go.Figure())
    fig = kwargs.get("fig", make_subplots(specs=[[{"secondary_y": True}]]))

    player_df = manager_df[manager_df['player_id'] == player_id].copy()
    player_df.sort_values(by='gw', inplace=True)
    player_df.reset_index(drop=True, inplace=True)

    player_df['def_score'] = (
        1 - (
            player_df['expected_goals_conceded'] / player_df['expected_goals_conceded'].max()
            )).clip(lower=0)
    
    # Create the Universal Metric
    conditions = [
        (player_df['position_label'] == 'GK'),
        (player_df['position_label'] == 'DEF'),
        (player_df['position_label'] == 'MID'),
        (player_df['position_label'] == 'FWD')
    ]
    values = [
        player_df['def_score'],                               # GKP: Only defense
        (player_df['def_score'] * 0.7) + (player_df['expected_goal_involvements'] * 0.3),    # DEF: Heavy defense, light attack
        (player_df['expected_goal_involvements'] * 0.8) + (player_df['def_score'] * 0.2),    # MID: Heavy attack, light defense
        player_df['expected_goal_involvements']                                       # FWD: Only attack
        ]

    player_df['expected_performance'] = np.select(conditions, values)
    
    x = player_df['gw']
    y_1 = player_df['opp_dificulty_rating']
    y_2 = player_df['expected_performance']
    y_3 = 5*(player_df['total_points']/player_df['total_points'].max())

    colors = ['green' if val == 1 
              else 'lightgreen' if val == 2 
              else 'yellow' if val ==3
              else 'orange' if val ==4
              else 'red' for val in y_1]
    
    
    hovertext_bar = create_hover_text({
        'opponent_team_name': ('Opponent:', None),
        'was_home': ('Home/Away:', lambda x: 'Home' if x == 1 else 'Away'),
        'total_points': ('Points Scored:', None),
        'minutes': ('Minutes Played:', None),}, 
        player_df)
    hovertext_point = create_hover_text({
        'total_points': ('Points Scored:', None),
    }, player_df)
    fig.add_trace(go.Bar(
        x=x,
        y=y_1,
        marker_color=colors,
        yaxis='y2',
        name='Opponent Difficulty',
        hovertext=hovertext_bar,
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=x,
        y=y_2,
        mode='lines+markers',
        yaxis='y1',
        name='Expected Performance',
    ), secondary_y=True)

    fig.add_trace(go.Scatter(
        x=x,
        y=y_3,
        mode='lines+markers',
        yaxis='y2',
        name='Adjusted Points',
        hovertext=hovertext_point,
    ), secondary_y=True)

    # Add figure title
    fig.update_layout(
        title_text="Expected Performance & Difficulty Rating Over Gameweeks for {}".format(player_name)
    )

    # Set x-axis title
    fig.update_xaxes(title_text="Game Week")

    # Set y-axes titles
    fig.update_yaxes(title_text="<b>Points Scored</b>", 
                     secondary_y=True,
                     range=[0, 5])
    fig.update_yaxes(title_text="<b>Difficulty Rating</b>", 
                     secondary_y=False,
                     range=[0, 5])
    fig.update_yaxes(title_text="<b>Expected Performance</b>", 
                     secondary_y=True,
                     range=[0, 5])

    '''
    fig.update_layout(
    title=f"{player_name} - Difficulty Rating & Expected Performance Over Gameweeks",
    xaxis_title="Gameweek",
    yaxis=dict(
        title="Points Scored",
        side='left',
        range=[0, 100]
    ),
    yaxis2=dict(
        title="Expected Performance",
        overlaying='y',
        side='right',
        range=[0, 5]
    ),
    legend=dict(x=0, y=1.1, orientation='h'))
    '''
    return fig

    '''
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add traces
    fig.add_trace(
        go.Bar(x=[1,2,3], y=[40,50,60], name="yaxis2 data"
               ), secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=[1, 2, 3], y=[40, 50, 60], name="yaxis data"),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=[2, 3, 4], y=[4, 5, 6], name="yaxis2 data"),
        secondary_y=True,
    )

    # Add figure title
    fig.update_layout(
        title_text="Double Y Axis Example"
    )

    # Set x-axis title
    fig.update_xaxes(title_text="xaxis title")

    # Set y-axes titles
    fig.update_yaxes(title_text="<b>primary</b> yaxis title", secondary_y=False)
    fig.update_yaxes(title_text="<b>secondary</b> yaxis title", secondary_y=True)
        # Filter for the specific player
    return fig
    '''