import plotly.express as px
import pandas as pd
import plotly.graph_objects as go

def budget_allocation_treemap_v2(df, path=[], values="", color_columns=[], title="default title"):
    df = df
    values = values if values else None
    path = path if path else None
    color_columns = color_columns if color_columns else None
    title = title
    if not (path or values or color_columns):
        return None
    
    df_all_trees = build_hierarchical_dataframe(df, path[::-1], values, color_columns)
    
    fig = go.Figure()
    average_score = df_all_trees['color'].mean() 
    fig.add_trace(go.Treemap(
    labels=df_all_trees['id'],
    parents=df_all_trees['parent'],
    values=df_all_trees['value'],
    customdata=df_all_trees[['total_points_total','selected','percent_budget']],
    branchvalues='total',
    marker=dict(
        colors=df_all_trees['color'],
        colorscale='RdBu',
        showscale=True,
        colorbar=dict(title="Pts/Million"),
        cmid=average_score),
    hovertemplate="""
    <b>%{label} </b> <br>
    Cost: $%{value}M<br>
    Points/Million: %{color:.2f} <br>
    Total Points: %{customdata[0]} <br>
    Selected by: %{customdata[1]:.2s} players <br>
    Percentage of Budget: %{customdata[2]:.2f}%
    """,
    name=title
    ))

    return fig

def build_hierarchical_dataframe(df, levels, value_column, color_columns=None):
    """
    Build a hierarchy of levels for Sunburst or Treemap charts.

    Levels are given starting from the bottom to the top of the hierarchy,
    ie the last level corresponds to the root.
    """
    df_list = []
    for i, level in enumerate(levels):
        df_tree = pd.DataFrame(columns=['id', 'parent', 'value', 'color', 
                                        'total_points_total','selected',
                                        'now_cost'])
        dfg = df.groupby(levels[i:]).sum()
        dfg = dfg.reset_index()
        df_tree['id'] = dfg[level].copy()
        if i < len(levels) - 1:
            df_tree['parent'] = dfg[levels[i+1]].copy()
        else:
            df_tree['parent'] = 'total'
        df_tree['value'] = dfg[value_column]
        df_tree['total_points_total'] = dfg['total_points_total']
        df_tree['selected'] = dfg['selected']
        df_tree['percent_budget'] = dfg['now_cost']/df['now_cost'].sum()*100
        df_tree['color'] = dfg[color_columns[0]] / dfg[color_columns[1]]
        df_list.append(df_tree)
    total = pd.Series(dict(id='total', parent='',
                              value=df[value_column].sum(),
                              color=df[color_columns[0]].sum() / df[color_columns[1]].sum(),
                              selected=df['selected'].sum()), name=0)
    df_list.append(total)
    df_all_trees = pd.concat(df_list, ignore_index=True)
    return df_all_trees

