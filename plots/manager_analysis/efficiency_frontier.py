import pandas as pd
import plotly.express as px
import numpy as np
import plotly.graph_objects as go

def efficiency_frontier(df, df_manager=None):
    df = df
    df_manager = df_manager
    
    hovertext = []
    for i in range(len(df)):
        hovertext.append(
            f"Player: {df.loc[i,'player_name']}<br>" +
            f"Selected by: {round(int(df.loc[i,'selected']/1000000),1)}M players<br>" +
            f"PPM: {df.loc[i,'ppm']:.2f}<br>" +
            f"Cost: £{df.loc[i,'now_cost']/10}M<br>"
        )

    df['text'] = hovertext
    positions = df['position_label'].unique()
    fig = go.Figure()
    for position in positions:
        fig.add_trace(go.Scatter(
            x = df.loc[df['position_label']==position, 'now_cost'],
            y = df.loc[df['position_label']==position, 'ppm'],
            name=position,
            marker_size = df.loc[df['position_label']==position, 'total_points']/10,
            text=df.loc[df['position_label']==position, 'text'],
            mode='markers',
            opacity=0.5
        ))

    x_1 = df['now_cost']
    y_1 = df['ppm']
    m, b = np.polyfit(x_1, y_1, 1) # 1 means linear (degree 1)

    # 3. Create the trendline coordinates
    x_range = np.linspace(x_1.min(), x_1.max(), 100)
    y_range = m * x_range + b
    
    # 4. Add the line to your existing figure
    fig.add_trace(go.Scatter(
        x=x_range, 
        y=y_range, 
        mode='lines', 
        name='Trendline (OLS)',
        line=dict(color='white', dash='dash')
        ))
    
    hovertext_mng = []
    for i in range(len(df_manager)):
        hovertext_mng.append(
            f"Player: {df_manager.loc[i,'player_name']}<br>" +
            f"Selected by: {round(int(df_manager.loc[i,'selected']/1000000),1)}M players<br>" +
            f"PPM: {df_manager.loc[i,'ppm']:.2f}<br>" +
            f"Cost: £{df_manager.loc[i,'now_cost']/10}M<br>"
        )
    df_manager['text'] = hovertext_mng
    for position in positions:
        fig.add_trace(go.Scatter(
            x = df_manager.loc[df_manager['position_label']==position, 'now_cost'],
            y = df_manager.loc[df_manager['position_label']==position, 'ppm'],
            name=position,
            marker_size = df_manager.loc[df_manager['position_label']==position, 
                                         'rolling_points_total']/10,
            mode='markers',
            text=df_manager.loc[df_manager['position_label']==position, 'text'],
            marker=dict(symbol='star')
        ))

    return fig