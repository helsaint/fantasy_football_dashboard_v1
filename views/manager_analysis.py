import streamlit as st
import pandas as pd
from pathlib import Path
from PIL import Image, ImageDraw,ImageFont
from utils.load_player_data import fetch_fpl_bootstrap
from utils.load_manager_data import fetch_manager_data
from utils.load_fpl_features import load_player_data
from config.position_config import POSITION_COORDINATES
from config.text import TEXT_FONT
from ui.fpl_search import fpl_search_inputs
from ui.text_field_display import player_text_display, text_heading_display
from plots.manager_analysis.ownership_value_differnetial import ownership_value_differential
from plots.manager_analysis.budget_allocation_treemap import budget_allocation_treemap_v2

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

            df_temp = pd.pivot_table(
                data=df_fpl_features[df_fpl_features['player_name'].isin(
                    list(df_manager_team_detailed['player_name']))],
                    index='player_name',
                    values='total_points',
                    aggfunc='sum').reset_index()
            df_manager_team_detailed = pd.merge(
                df_manager_team_detailed,
                df_temp,
                on='player_name',
                how='left',
                suffixes=('', '_total'))
            
            position_map = {1: ('GK',2), 2: ('DEF',5), 3: ('MID', 5), 4: ('FWD', 3)}
            multiplier_map = {0: 'BENCH', 1: 'STARTER', 2: 'CAPTAIN'}
            df_manager_team_detailed['position'] = df_manager_team_detailed['position_y'].map(lambda x: position_map[x][0])
            df_manager_team_detailed['multiplier_label'] = df_manager_team_detailed['multiplier'].map(multiplier_map)

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

            st.markdown("---")

            st.subheader("Ownership Value Differential Analysis")
            fig_ovd = ownership_value_differential(df_manager_team_detailed)
            st.plotly_chart(fig_ovd, width='stretch')
            st.write("The plot shows the relationship between player ownership" \
            "and total points scored. The size of the markers represents the player's cost."
            " This analysis helps identify players who are potentially undervalued or overvalued"
            " based on their ownership and performance. Overvalued players will be found" \
            " in the lower right quadrant, while undervalued players will be in the upper " \
            "left quadrant. The top right quadrant indicates popular high performers," \
            " while having players here means that you are keeping up with popular picks," \
            " but you aren't seperating yourself from the crowd. For that you" \
            " need to be looking for undervalued players in the upper left quadrant." )
            
            st.markdown("---")
            st.subheader("Budget Allocation Breakdown")
            temp_columns = ['player_name', 'position', 'now_cost', 
                            'total_points_total', 'selected',
                            'multiplier_label']
            df_temp = df_manager_team_detailed[temp_columns].copy()
            df_temp['now_cost'] = df_temp['now_cost']/10  # convert to millions
            df_temp['position_label'] = df_temp['position'] + "_" + df_temp['multiplier_label']
            fig_budget_allocation = budget_allocation_treemap_v2(df_temp, 
                                                                path=['multiplier_label', 'position_label', 'player_name'],
                                                                values='now_cost',
                                                                color_columns=['total_points_total', 'now_cost'],
                                                                title='Budget Allocation Treemap')
            
            st.plotly_chart(fig_budget_allocation, width='stretch')
            st.write("""The treemap shows how the manager has allocated their budget across
                     different positions. A very good team will have a lot of players in the 
                     'STARTER' category with a bluish hue. This indicates that the
                     manager has invested in high-performing players who contribute
                     significantly to the team's total points. If you have players
                     with deep red hues consider transferring them. Players in the 
                     'BENCH' category should ideally have a reddish hue as they
                     are not expected to contribute significantly to the team's points.""")
            
            st.markdown("---")
            st.subheader("Manager Team Data")