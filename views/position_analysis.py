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
            df_fpl_features = load_player_data()
            df_manager_team_detailed = pd.merge(
                df_manager_team,
                df_fpl_features[df_fpl_features['gw'] == gw],
                left_on='element',
                right_on='player_id',
                how='left'
            )
            print(df_manager_team_detailed.position_y.unique())
            pos_key = "GK_NAME_1"
            x, y, w, h = POSITION_COORDINATES[pos_key]
            font_family = TEXT_FONT["font_family"]
            font_size = TEXT_FONT["font_size_names"]
            font = ImageFont.truetype(font_family, font_size)
            text = df_manager_team_detailed[df_manager_team_detailed['position_y']==1]['player_name'].values[0]
            draw.text((x, y), text, fill="white", font=font)

            for i in range(5):
                position = 2
                font_family = TEXT_FONT["font_family"]
                font_size = TEXT_FONT["font_size_names"]
                font = ImageFont.truetype(font_family, font_size)
                # Player Name
                text = df_manager_team_detailed[df_manager_team_detailed['position_y']==position]['player_name'].values[i]
                pos_key = f"DEF_NAME_{i+1}"
                x, y, w, h = POSITION_COORDINATES[pos_key]
                draw.text((x, y), text, fill=TEXT_FONT["font_color_names"], font=font)
                # Player Value
                pos_key = f"DEF_VALUE_{i+1}"
                x, y, w, h = POSITION_COORDINATES[pos_key]
                text = df_manager_team_detailed[df_manager_team_detailed['position_y']==position]['now_cost'].values[i]
                draw.text((x, y), f"£{text/10}m", fill=TEXT_FONT["font_color_values"], font=font)
                # Player GW Points
                pos_key = f"DEF_POINTS_{i+1}"
                x, y, w, h = POSITION_COORDINATES[pos_key]
                text = df_manager_team_detailed[df_manager_team_detailed['position_y']==position]['total_points'].values[i]
                draw.text((x, y), f"Pts: {text}", fill=TEXT_FONT["font_color_values"], font=font)
                # Player Photo
                pos_key = f"DEF_{i+1}"
                x, y, w, h = POSITION_COORDINATES[pos_key]
                text = df_manager_team_detailed[df_manager_team_detailed['position_y']==position]['photo'].values[i]
                text = text.replace('.jpg','').replace('.png','')
                try:
                    photo_url = f"https://resources.premierleague.com/premierleague/photos/players/110x140/p{text}.png"
                    player_image = Image.open(requests.get(photo_url, stream=True).raw).resize((w, h))
                    pitch_image.paste(player_image, (x, y))
                except Exception as e:
                    print(f"Error loading image for player {text}: {e}")

            for i in range(5):
                position = 3
                font_family = TEXT_FONT["font_family"]
                font_size = TEXT_FONT["font_size_names"]
                font = ImageFont.truetype(font_family, font_size)
                # Player Name
                text = df_manager_team_detailed[df_manager_team_detailed['position_y']==position]['player_name'].values[i]
                pos_key = f"MID_NAME_{i+1}"
                x, y, w, h = POSITION_COORDINATES[pos_key]
                draw.text((x, y), text, fill=TEXT_FONT["font_color_names"], font=font)
                # Player Value
                pos_key = f"MID_VALUE_{i+1}"
                x, y, w, h = POSITION_COORDINATES[pos_key]
                text = df_manager_team_detailed[df_manager_team_detailed['position_y']==position]['now_cost'].values[i]
                draw.text((x, y), f"£{text/10}m", fill=TEXT_FONT["font_color_values"], font=font)
                # Player GW Points
                pos_key = f"MID_POINTS_{i+1}"
                x, y, w, h = POSITION_COORDINATES[pos_key]
                text = df_manager_team_detailed[df_manager_team_detailed['position_y']==position]['total_points'].values[i]
                draw.text((x, y), f"Pts: {text}", fill=TEXT_FONT["font_color_values"], font=font)
                # Player Photo
                pos_key = f"MID_{i+1}"
                x, y, w, h = POSITION_COORDINATES[pos_key]
                text = df_manager_team_detailed[df_manager_team_detailed['position_y']==position]['photo'].values[i]
                text = text.replace('.jpg','').replace('.png','')
                try:
                    photo_url = f"https://resources.premierleague.com/premierleague/photos/players/110x140/p{text}.png"
                    player_image = Image.open(requests.get(photo_url, stream=True).raw).resize((w, h))
                    pitch_image.paste(player_image, (x, y))
                except Exception as e:
                    print(f"Error loading image for player {text}: {e}")
            st.image(pitch_image, caption="My beautiful team", width="stretch")