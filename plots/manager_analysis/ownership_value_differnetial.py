import pandas as pd
import plotly.graph_objects as go

def ownership_value_differential(df):
    x = df['selected']
    y = df['total_points_total']
    marker_size = df['now_cost']/5
    player_name = df['player_name']
    
    hovertext = []

    for i in range(len(df)):
        hovertext.append(
            f"Player: {player_name[i]}<br>" +
            f"Selected by: {round(x[i]/1000000,1)}M players<br>" +
            f"Total Points: {y[i]}<br>" +
            f"Cost: £{marker_size[i]*5/10}M"
        )
    df['text'] = hovertext
    positions = df['position'].unique()
    position_data = {position:df[df['position']==position]
                              for position in positions}
    fig = go.Figure()
    for position, data in position_data.items():
        fig.add_trace(go.Scatter(
            x = data['selected'],
            y = data['total_points_total'],
            name=position,
            marker_size = data['now_cost']/5,
            text=data['text'],
            mode='markers',
        ))

    fig.update_layout(
        title="Ownership vs Total Points Differential",
        xaxis_title="Ownership numbers (raw)",
        yaxis_title="Total Points",
        hovermode='closest'
    )

    return fig