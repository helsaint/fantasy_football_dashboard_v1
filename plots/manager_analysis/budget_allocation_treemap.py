import plotly.express as px
import pandas as pd

def budget_allocation_treemap():
    vendors = ["A", "B", "C", "D", None, "E", "F", "G", "H", None]
    sectors = ["Tech", "Tech", "Finance", "Finance", "Other",
               "Tech", "Tech", "Finance", "Finance", "Other"]
    regions = ["North", "North", "North", "North", "North",
               "South", "South", "South", "South", "South"]
    sales = [1, 3, 2, 4, 1, 2, 2, 1, 4, 1]
    df = pd.DataFrame(
        dict(vendors=vendors, sectors=sectors, regions=regions, sales=sales)
        )
    df["all"] = "all" # in order to have a single root node
    print(df)
    fig = px.treemap(df, path=['all', 'regions', 'sectors', 'vendors'], values='sales')
    fig.update_traces(root_color="lightgrey")
    fig.update_layout(margin = dict(t=50, l=25, r=25, b=25))

    return fig

def budget_allocation_treemap_v2(df, path=[], values="", title="default title"):
    df = df
    values = values if values else None
    path = path if path else None
    title = title
    if not (path and values):
        return None
    
    fig = px.treemap(
        df,
        path=path,
        values=values,
        title=title,
        labels={values: 'Cunxi (£M)'},
    )
    fig.update_traces(root_color="lightgrey")
    fig.update_layout(margin = dict(t=50, l=25, r=25, b=25))

    return fig