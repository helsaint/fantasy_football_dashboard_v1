import pandas as pd
import plotly.express as px

def ownership_value_differential(df):
    fig = px.scatter(
        df, x='now_cost', y='ppm', size='selected', color='position',
    )

    return fig