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
    
    '''
    # Get current gameweek from API
    fpl_data = fetch_fpl_bootstrap()

    if fpl_data:
        # Extract current gameweek
        events = fpl_data.get('events', [])
        current_gw = None
        
        # Find the current event (gameweek)
        for event in events:
            if event.get('is_current'):
                current_gw = event.get('id')
                break
        
        # If no current event found, use the next event
        if not current_gw:
            for event in events:
                if event.get('is_next'):
                    current_gw = event.get('id')
                    break
        
        # Fallback to the last event
        if not current_gw and events:
            current_gw = max(event.get('id', 1) for event in events)
        
        # Get event details for display
        current_event_name = None
        if current_gw:
            for event in events:
                if event.get('id') == current_gw:
                    current_event_name = event.get('name', f'Gameweek {current_gw}')
                    break
        
        # Display current gameweek info
        if current_gw:
            st.success(f"✅ **Current Gameweek Detected:** {current_event_name}")
        else:
            st.warning("⚠️ Could not detect current gameweek. Defaulting to GW1.")
            current_gw = 1
            current_event_name = "Gameweek 1"
    else:
        st.warning("⚠️ Could not fetch FPL data. Defaulting to GW1.")
        current_gw = 1
        current_event_name = "Gameweek 1"

    # Create input columns with auto-detected gameweek
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        manager_id = st.text_input(
            "Enter your FPL Manager ID:",
            placeholder="e.g., 1234567",
            help="Find this in your FPL profile URL: fantasy.premierleague.com/entry/1234567/event/15"
        )
    
    with col2:
        # Let user choose between current GW or specific GW
        gw_mode = st.radio(
            "Gameweek:",
            ["Current", "Specific"],
            horizontal=True,
            help="Choose whether to analyze current or specific gameweek"
        )
    
    with col3:
        if gw_mode == "Current":
            gw = current_gw
            st.metric("Gameweek", f"GW{gw}")
        else:
            # Show slider for specific gameweek selection
            gw = st.number_input(
                "Select GW:",
                min_value=1,
                max_value=38,
                value=current_gw,
                key="gw_specific",
                help="Select a specific gameweek"
            )

    # Add gameweek status indicator
    if fpl_data and 'events' in fpl_data:
        for event in fpl_data['events']:
            if event.get('id') == gw:
                deadline_passed = event.get('deadline_time_epoch', 0) < datetime.now().timestamp()
                if event.get('is_current'):
                    if deadline_passed:
                        st.info(f"⏳ GW{gw} is in progress. Next deadline: {event.get('deadline_time_formatted', 'N/A')}")
                    else:
                        st.info(f"⏰ GW{gw} deadline: {event.get('deadline_time_formatted', 'N/A')}")
                break
    '''

    
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