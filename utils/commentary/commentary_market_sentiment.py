import pandas as pd

def commentary_market_sentiment(df):
    """
    df must have columns: gw, total_points, net_transfers (or compute it)
    Returns a list of commentary sentences.
    """
    df = df.sort_values('gw').copy()
    df['net_transfers'] = df['transfers_in'] - df['transfers_out']
    
    comments = []
    
    # 1. Overall stats
    max_points = df['total_points'].max()
    max_gw = df.loc[df['total_points'].idxmax(), 'gw']
    min_points = df['total_points'].min()
    min_gw = df.loc[df['total_points'].idxmin(), 'gw']

    player_name = df['player_name'].unique()[0]
    
    comments.append(f"Over the selected period, {player_name}'s best gameweek was GW{max_gw} with {max_points} points, while the worst was GW{min_gw} with {min_points} points.")
    
    # 2. Net transfer extremes
    max_in = df['net_transfers'].max()
    max_in_gw = df.loc[df['net_transfers'].idxmax(), 'gw']
    max_out = df['net_transfers'].min()  # most negative
    max_out_gw = df.loc[df['net_transfers'].idxmin(), 'gw']
    
    comments.append(f"The highest net inflow was {max_in:+,} in GW{max_in_gw}, and the highest net outflow was {max_out:+,} in GW{max_out_gw}.")
    
    # 3. Lag analysis: Did points spike cause transfers next week?
    # Shift net_transfers by -1 to see next week's transfers
    df['next_net'] = df['net_transfers'].shift(-1)
    # Find weeks where points > some threshold (e.g., 10) and next_net > 0
    haul_threshold = 10
    hauls = df[df['total_points'] >= haul_threshold]
    for _, row in hauls.iterrows():
        next_net = row['next_net']
        if pd.notna(next_net):
            if next_net > 0:
                comments.append(f"After a {row['total_points']}-point haul in GW{row['gw']}, managers brought him in ({next_net:+,} net transfers the following week).")
            elif next_net < 0:
                comments.append(f"Despite a {row['total_points']}-point haul in GW{row['gw']}, managers actually sold him ({next_net:+,} net transfers) – perhaps due to injury or fixture congestion.")
    
    # 4. Recent trend (last 3 GWs)
    recent = df.tail(3)
    avg_points_recent = recent['total_points'].mean()
    avg_net_recent = recent['net_transfers'].mean()
    if avg_net_recent > 5000:
        comments.append(f"In the last 3 gameweeks, his average net transfers are +{avg_net_recent:.0f} per week, suggesting growing popularity.")
    elif avg_net_recent < -5000:
        comments.append(f"Recently, managers are losing faith: average net outflows of {avg_net_recent:.0f} per week over the last 3 gameweeks.")
    else:
        comments.append(f"Net transfers have been relatively stable recently (average {avg_net_recent:+.0f} per week).")
    
    # 5. Correlation (optional)
    corr = df['total_points'].corr(df['net_transfers'])
    if abs(corr) > 0.5:
        comments.append(f"There is a {'strong positive' if corr > 0 else 'strong negative'} correlation ({corr:.2f}) between his points and net transfers.")
    
    return comments