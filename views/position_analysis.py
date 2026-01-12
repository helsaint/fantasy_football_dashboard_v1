import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import requests
from pathlib import Path
from PIL import Image, ImageDraw,ImageFont
from utils.load_player_data import fetch_fpl_bootstrap
from utils.load_manager_data import fetch_manager_data
from utils.load_fpl_features import load_player_data
from config.position_config import POSITION_COORDINATES
from config.text import TEXT_FONT
from ui.fpl_search import fpl_search_inputs
from ui.text_field_display import player_text_display, text_heading_display

def show(df):
    """Display a simple football pitch image"""
    
    st.header("⚽ Football Pitch")
    st.markdown("This is a basic football pitch display.")
    
    # Simple pitch image display
    #pitch_url = "images/fpl_pitch.png"
    pitch_url = Path(__file__).parent.parent / "images" / "fpl_pitch.png"
    pitch_image = Image.open(pitch_url)
    draw = ImageDraw.Draw(pitch_image)
    #st.image(pitch_image, caption="My beautiful team", width="stretch")
    
    st.markdown("---")
    st.write("Next step: Add player positioning to this pitch.")
    manager_id, gw = fpl_search_inputs()
    
    if manager_id and st.button("🔍 Fetch & Analyze Team", type="primary"):
        with st.spinner(f"Fetching manager {manager_id}'s team for GW{gw}..."):
            manager_data = fetch_manager_data(manager_id, gw)
            df_manager_team = pd.DataFrame(manager_data['picks']) if manager_data else pd.DataFrame()
            dict_manager_history = manager_data['entry_history']
            
            df_fpl_features = load_player_data()
            gw_latest = df_fpl_features['gw'].max()
            gw_data_available = 0 if df_fpl_features.loc[df_fpl_features['gw'] == gw, 'now_cost'].sum() == 0 else 1
            if gw_data_available == 0:
                st.warning(f"Data for GW{gw} is not available yet. Displaying data for GW{gw_latest-1} instead.")
                gw = gw_latest-1
            df_manager_team_detailed = pd.merge(
                df_manager_team,
                df_fpl_features[df_fpl_features['gw'] == gw],
                left_on='element',
                right_on='player_id',
                how='left'
            )

            position_map = {1: ('GK',2), 2: ('DEF',5), 3: ('MID', 5), 4: ('FWD', 3)}


            font_family = TEXT_FONT["font_family"]
            font_size_name = TEXT_FONT["font_size_names"]
            font_size_value = TEXT_FONT["font_size_values"]
            font_name = ImageFont.truetype(font_family, font_size_name)
            font_value = ImageFont.truetype(font_family, font_size_value)
            font_size_team_value = TEXT_FONT["font_size_team_value"]
            font_team_value = ImageFont.truetype(font_family, font_size_team_value)

            # Team Value
            pos_key = "TEAM_VALUE"
            team_value = df_manager_team_detailed['now_cost'].sum()
            text = f"£{team_value/10}m"
            text_heading_display(pos_key, text, draw, font_team_value)
            
            # GW
            pos_key = "GW"
            text = f"{gw}"
            text_heading_display(pos_key, text, draw, font_team_value)

            # Bank
            pos_key = "BANK"
            text = f"{dict_manager_history['bank']/10}m"
            text_heading_display(pos_key, text, draw, font_team_value)

            # Goalkeeper
            player_text_display(pitch_image, "GK", 1, df_manager_team_detailed, draw, 
                         font_name, font_value, 0)

            # Defenders
            for i in range(5):
                position = 2
                player_text_display(pitch_image, "DEF", position, df_manager_team_detailed, draw, 
                             font_name, font_value, i)
            
            # Midfielders
            for i in range(5):
                position = 3
                player_text_display(pitch_image, "MID", position, df_manager_team_detailed, draw, 
                             font_name, font_value, i)
            
            # Forwards
            for i in range(3):
                position = 4
                player_text_display(pitch_image, "FWD", position, df_manager_team_detailed, draw, 
                             font_name, font_value, i)
            
           
            st.image(pitch_image, caption="My beautiful team", width="stretch")