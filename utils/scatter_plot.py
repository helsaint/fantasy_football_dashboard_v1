import plotly.express as px
import numpy as np
import plotly.graph_objects as go
import pandas as pd
import streamlit as st


def scatter_plot(main_df, **kwargs):
    df2 = kwargs.get("df2", None)
    hover_template_dict=kwargs.get("hover_template_dict", {})
    trendline_bool = kwargs.get("trendline_bool", False)
    x_str = kwargs.get("x_column", "now_cost")
    y_str = kwargs.get("y_column", "total_points")
    marker_str = kwargs.get("marker_column", "total_points")
    fig = kwargs.get("fig", go.Figure())
    category_str = kwargs.get("category_column", "position")
    x_title = kwargs.get("x_title", x_str)
    y_title = kwargs.get("y_title", y_str)
    main_df = main_df.reset_index()

    r2 = 0

    opacity_float= 1.0
    if df2 is not None:
        opacity_float= 0.5

    hovertext = []
    if hover_template_dict:
        hovertext = create_hover_text(hover_template_dict, main_df)
        main_df['text'] = hovertext
    else:
        main_df['text'] = "Missing"
    
    categories = main_df[category_str].unique()
    fig = create_fig(df=main_df, categories=categories, 
                     category_str=category_str,
                     x_str=x_str, y_str=y_str, marker_str=marker_str, 
                     trendline_bool=trendline_bool,
                     fig=fig, opacity=opacity_float,
                     symbol='circle')
    
    if trendline_bool:
        fig, r2 = fig_create_trendline(x_str, y_str, fig, main_df)
    
    fig = fig_title_from_columns(x_title, y_title, fig)

    if df2 is not None:
        hovertext_2 = []
        if hover_template_dict:
            hovertext_2 = create_hover_text(hover_template_dict, df2)
            df2.loc[:,'text'] = hovertext_2
        else:
            df2['text'] = "Missing"
        
        fig = create_fig(df=df2, categories=categories, 
                         category_str=category_str,
                         x_str=x_str, y_str=y_str, marker_str=marker_str, 
                         trendline_bool=False,
                         fig=fig, opacity=1.0,
                         symbol='star')

    return fig, r2

def fig_title_from_columns(x_title: str, y_title: str, fig: go.Figure):
    fig.update_layout(
        title="Scatter Plot: " + x_title + " vs " + y_title,
        xaxis_title=x_title,
        yaxis_title=y_title,
        hovermode='closest',
    )
    return fig

def fig_create_trendline(x_str, y_str, fig: go.Figure, df: pd.DataFrame):
    df_1 = df.copy()
    df_1 = df_1.sort_values(by=x_str, ascending=True)
    df_1.dropna(inplace=True)
    
    x_1 = df_1[x_str]
    y_1 = df_1[y_str]
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
    
    # 5. Get R^2
    df_1['predicted_y'] = (m * x_1) + b
    # Measures the gap between reality and our model
    df_1['residual_sq'] = (y_1 - df_1['predicted_y'])**2
    ss_res = df_1['residual_sq'].sum()
    # Measures how much the data fluctuates from its own average
    y_mean = y_1.mean()
    df_1['variance_sq'] = (y_1 - y_mean)**2
    ss_tot = df_1['variance_sq'].sum()

    # 6. The Final R^2 Score
    r_squared = 0
    try:
        r_squared = np.round(100*(1 - (ss_res / ss_tot)),3)
    except:
        r_squared = 0
    
    return fig, r_squared

def create_hover_text(hover_template_dict: dict, df: pd.DataFrame):
    hovertext = []
    for i in range(len(df)):
        text = ""
        for key, (label, func) in hover_template_dict.items():
            temp_text = df.loc[i, key]
            if func:
                temp_text = func(temp_text)
            
            temp_text = str(temp_text)
            text = text + label + temp_text + "<br>"
        hovertext.append(text)
    return hovertext

def create_fig(df: pd.DataFrame, categories: list,
               category_str: str, 
               x_str: str, y_str: str, 
               marker_str: str, trendline_bool: bool,
               fig: go.Figure,
               opacity: float =0.5,
               symbol: str ='circle'):

    for cat in categories:
        min_size=5 
        max_size=20
        # 1. Filter and clean data (handling the negative size issue from earlier)
        sub_df = df[df[category_str] == cat].copy()
        # 2. Extract raw sizes and handle potential NaNs or negatives
        raw_sizes = sub_df[marker_str].clip(lower=0)
        # 3. Apply Scaling logic
        # We use the global min/max of the WHOLE column so bubbles are comparable across categories
        global_min = df[marker_str].min()
        global_max = df[marker_str].max()
        # Prevent division by zero if all values are the same
        if global_max == global_min:
            scaled_sizes = [min_size] * len(sub_df)
        else:
            scaled_sizes = ((raw_sizes - global_min) / 
                            (global_max - global_min)) * (max_size - min_size) + min_size
        fig.add_trace(go.Scatter(
            x = df.loc[df[category_str]==cat, x_str],
            y = df.loc[df[category_str]==cat, y_str], 
            name=str(cat),
            marker_size = scaled_sizes,
            text=df.loc[df[category_str]==cat, 'text'],
            mode='markers',
            opacity=opacity,
            marker=dict(symbol=symbol)
        ))
        
    return fig

    