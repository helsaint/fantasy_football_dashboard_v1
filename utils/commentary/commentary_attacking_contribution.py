import pandas as pd

def commentary_attacking_contribution(df):
    """
    df must have columns: gw, goals_scored, assists, goals_scored_team, player_name
    Returns a list of commentary sentences.
    """
    df = df.sort_values('gw').copy()
    
    comments = []

    # 1. Overall Statistics
    team_total_goals = df['goals_scored_team'].sum()
    player_goal_involvement = (df['goals_scored'] + df['assists']).sum()
    attacking_contribution = f"{player_goal_involvement/team_total_goals:.0%}"
    best_gw_ga = df.iloc[(df['goals_scored'] + df['assists']).idxmax()]['gw']
    best_3_gws = [str(x) for x in list(df.loc[(df['total_points']).nlargest(3).index]['gw'])]
    gi_per_game = f"{player_goal_involvement/df['gw'].max():.2f}"

    player_name = df['player_name'].unique()[0]
    
    comments.append(f"Best attacking contribution from {player_name} was on game week {best_gw_ga}")
    formatted_gws_list = ", ".join(best_3_gws[:-1]) + " and " + best_3_gws[-1]
    comments.append(f"{player_name}'s best game weeks were {formatted_gws_list}")
    comments.append(f"{player_name}'s goal involvements per gw is {gi_per_game}")
    return comments
    