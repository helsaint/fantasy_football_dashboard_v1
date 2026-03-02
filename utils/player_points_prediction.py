import pandas as pd

def points_prediction(df: pd.DataFrame):
    df = df
    xg_p90 = 90*df['expected_goals_roll_total_5'] / df['minutes_roll_total_5']
    xa_p90 = 90*df['expected_assits_roll_total_5'] / df['minutes_roll_total_5']
    xgc_p90 = 90*df['expected_gc_roll_total_5']/df['minutes_roll_total_5']

    exp_minutes = df['minutes_roll_total_3']
    opp_xgc = df['opp_xGC_roll_5']
    league_avg_xgc = df['opp_xGC_roll_5'].sum()/20
    attack_adj = opp_xgc/league_avg_xgc
    adj_xG = xg_p90*attack_adj
    adj_xA = xa_p90*attack_adj