import streamlit as st
from pathlib import Path
import pandas as pd
import numpy as np
# ========== DATA LOADING WITH CACHING ==========
@st.cache_data
def load_player_data():
    """Load and preprocess the player performance data"""
    try:
        # Try to load from the data folder
        data_path = Path(__file__).parent.parent / "data" / "fpl_features.csv"
        
        df = pd.read_csv(data_path)
        print(data_path)
        # Basic data validation
        required_cols = ['player_name', 'gw', 'goals_scored', 'assists', 
                        'total_points', 'clean_sheets', 'now_cost',
                        'goals_conceded', 'saves']
        
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.error(f"Missing columns: {missing_cols}")
            # Create sample data if file doesn't have required columns
            return create_sample_data()
        
        # Data cleaning
        df['player_name'] = df['player_name'].astype(str)
        df['gw'] = pd.to_numeric(df['gw'], errors='coerce')
        df['goals_scored'] = pd.to_numeric(df['goals_scored'], errors='coerce').fillna(0)
        df['assists'] = pd.to_numeric(df['assists'], errors='coerce').fillna(0)
        df['total_points'] = pd.to_numeric(df['total_points'], errors='coerce').fillna(0)
        df['now_cost'] = pd.to_numeric(df['now_cost'], errors='coerce').fillna(0)
        
        # Calculate additional metrics
        df['goal_contributions'] = df['goals_scored'] + df['assists']
        df['points_per_million'] = df['total_points'] / (df['now_cost'] / 10)
        
        # Calculate form (average points over last 3 games)
        df = df.sort_values(['player_name', 'gw'])
        df['form'] = df.groupby('player_name')['total_points'].rolling(3, min_periods=1).mean().reset_index(level=0, drop=True)
        
        return df
        
    except FileNotFoundError:
        st.warning("⚠️ CSV file not found. Using sample data for demonstration.")
        return create_sample_data()
    
def create_sample_data():
    """Create sample data if CSV file is missing"""
    players = ['Haaland', 'Salah', 'Kane', 'De Bruyne', 'Son', 'Rashford', 
               'Bruno Fernandes', 'Saka', 'Martinez', 'Foden']
    
    data = []
    for player in players:
        for gw in range(1, 31):  # 30 gameweeks
            goals = np.random.poisson(0.7) if player in ['Haaland', 'Salah', 'Kane'] else np.random.poisson(0.3)
            assists = np.random.poisson(0.4) if player in ['De Bruyne', 'Bruno Fernandes'] else np.random.poisson(0.2)
            total_points = goals * 4 + assists * 3 + np.random.randint(0, 3)
            now_cost = np.random.randint(10000000, 15000000) if player in ['Haaland', 'Salah'] else np.random.randint(7000000, 10000000)
            
            data.append({
                'player_name': player,
                'gw': gw,
                'goals_scored': goals,
                'assists': assists,
                'total_points': total_points,
                'now_cost': now_cost
            })
    
    df = pd.DataFrame(data)
    df['goal_contributions'] = df['goals_scored'] + df['assists']
    df['points_per_million'] = df['total_points'] / (df['now_cost'] / 1000000)
    
    return df