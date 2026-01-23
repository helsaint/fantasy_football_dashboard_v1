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
from plots.manager_analysis.efficiency_frontier import efficiency_frontier
from plots.manager_analysis.fixture_adjusted_performance import create_fixture_adjusted_chart
from utils.scatter_plot import scatter_plot

@st.fragment
def show(df):
    """Display a simple football pitch image"""
    
    st.header("⚽ Football Pitch")
    st.markdown("This is a basic football pitch display.")

    # Initializing session state for fetched data
    if 'fetched_manager_data' not in st.session_state:
        st.session_state.fetched_manager_data = None
    if 'fetched_fpl_data' not in st.session_state:
        st.session_state.fetched_fpl_data = None
    if 'fetched_histrory_data' not in st.session_state:
        st.session_state.fetched_history_data = None
    if 'pitch_image' not in st.session_state:
        st.session_state.pitch_image = None

    '''
    # Debug: Display session state
    st.write("### Current Session State:")
    st.write(st.session_state)
    '''

    # Simple pitch image display
    #pitch_url = "images/fpl_pitch.png"
    pitch_url = Path(__file__).parent.parent / "images" / "fpl_pitch.png"
    pitch_image = Image.open(pitch_url)
    draw = ImageDraw.Draw(pitch_image)
    
    st.markdown("---")
    st.write("Next step: Add player positioning to this pitch.")
    manager_id, gw = fpl_search_inputs()

    if manager_id and st.button("🔍 Fetch & Analyze Team", type="primary"):
        with st.spinner(f"Fetching manager {manager_id}'s team for GW{gw}..."):
            st.session_state.fetched_manager_data = None
            st.session_state.fetched_fpl_data = None
            st.session_state.fetched_histrory_data = None
            st.session_state.pitch_image = None

            manager_data = fetch_manager_data(manager_id, gw)
            st.session_state.fetched_manager_data = manager_data
            df_manager_team = pd.DataFrame(manager_data['picks']) if manager_data else pd.DataFrame()
            dict_manager_history = manager_data['entry_history']
            
            df_fpl_features = load_player_data()
            
            df_fpl_features = df_fpl_features.sort_values(
                by=['player_id', 'gw', 'selected'], 
                ascending=[True, True, True], 
                na_position='last'
                )
            df_fpl_features = df_fpl_features.drop_duplicates(
                subset=['player_id', 'gw'], 
                keep='first'
                )
            df_fpl_features['rolling_minutes_played'] = df_fpl_features.groupby(
                'player_id')['minutes'].cumsum()
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
            
            
            position_map = {1: 'GK', 2: 'DEF', 3: 'MID', 4: 'FWD'}
            multiplier_map = {0: 'BENCH', 1: 'STARTER', 2: 'CAPTAIN'}
            df_manager_team_detailed['position_label'] = df_manager_team_detailed['position_y'].map(position_map)
            df_manager_team_detailed['multiplier_label'] = df_manager_team_detailed['multiplier'].map(multiplier_map)
            df_fpl_features['position_label'] = df_fpl_features['position'].map(position_map)

            # Set session states
            st.session_state.fetched_fpl_data = df_fpl_features.copy()
            st.session_state.fetched_manager_data = df_manager_team_detailed.copy()
            st.session_state.fetched_histrory_data = dict_manager_history.copy()

    st.markdown("---")
    st.subheader("My Beautiful Team")
    ''' Display the manager's team on the pitch image 
     with player photos and stats.
     if the pitch image hasn't alredy been created in this session.
     If it has, just display the saved image.
     '''
    if (
        st.session_state.fetched_manager_data is not None
        ) and (
            st.session_state.fetched_histrory_data is not None
            ) and (st.session_state.pitch_image is None):
        font_family = TEXT_FONT["font_family"]
        font_size_name = TEXT_FONT["font_size_names"]
        font_size_value = TEXT_FONT["font_size_values"]
        font_name = ImageFont.truetype(font_family, font_size_name)
        font_value = ImageFont.truetype(font_family, font_size_value)
        font_size_team_value = TEXT_FONT["font_size_team_value"]
        font_team_value = ImageFont.truetype(font_family, font_size_team_value)

        # Team Value
        pos_key = "TEAM_VALUE"
        team_value = st.session_state.fetched_manager_data['now_cost'].sum()
        text = f"£{team_value/10}M"
        text_heading_display(pos_key, text, draw, font_team_value)
            
        # GW
        pos_key = "GW"
        text = f"{gw}"
        text_heading_display(pos_key, text, draw, font_team_value)

        # Bank
        pos_key = "BANK"
        text = f"{st.session_state.fetched_histrory_data['bank']/10}M"
        text_heading_display(pos_key, text, draw, font_team_value)

        # Goalkeeper
        player_text_display(pitch_image, "GK", 1, st.session_state.fetched_manager_data, draw, 
                            font_name, font_value, 0)

        # Defenders
        for i in range(5):
            position = 2
            player_text_display(pitch_image, "DEF", position, 
                                st.session_state.fetched_manager_data, draw, 
                                font_name, font_value, i)
            
        # Midfielders
        for i in range(5):
            position = 3
            player_text_display(pitch_image, "MID", position, 
                                st.session_state.fetched_manager_data, draw, 
                                font_name, font_value, i)
            
        # Forwards
        for i in range(3):
            position = 4
            player_text_display(pitch_image, "FWD", position, 
                                st.session_state.fetched_manager_data, draw, 
                                font_name, font_value, i)
        
        # Save pitch image to session state
        st.session_state.pitch_image = pitch_image.copy()

        st.image(pitch_image, caption="My beautiful team", width="stretch")
    elif st.session_state.pitch_image is not None:
        # Display saved pitch image from session state
        st.image(st.session_state.pitch_image, caption="My beautiful team", width="stretch")
    else:
        st.warning("No manager data fetched yet. Please fetch a manager's team to analyze.")
        
    st.markdown("---")        
    st.subheader("Ownership Value Differential Analysis")
    if st.session_state.fetched_manager_data is not None:
        fig_ovd = ownership_value_differential(
            st.session_state.fetched_manager_data)
        st.plotly_chart(fig_ovd, width='stretch', key="ownership_value_differential_plot")
        st.write("The plot shows the relationship between player ownership" \
            "and total points scored. The size of the markers represents the player's cost."
            " This analysis helps identify players who are potentially undervalued or overvalued"
            " based on their ownership and performance. Overvalued players will be found" \
            " in the lower right quadrant, while undervalued players will be in the upper " \
            "left quadrant. The top right quadrant indicates popular high performers," \
            " while having players here means that you are keeping up with popular picks," \
            " but you aren't seperating yourself from the crowd. For that you" \
            " need to be looking for undervalued players in the upper left quadrant." )
    else:
        st.warning("No manager data fetched yet. Please fetch a manager's team to analyze.")
    
    st.markdown("---")
    st.subheader("Budget Allocation Breakdown")
    if st.session_state.fetched_manager_data is not None:
        temp_columns = ['player_name', 'position_label', 'now_cost', 
                        'rolling_points_total', 'selected',
                        'multiplier_label']
        df_temp = st.session_state.fetched_manager_data[temp_columns].copy()
        df_temp['now_cost'] = df_temp['now_cost']/10  # convert to millions
        df_temp['position_label_1'] = df_temp['position_label'] + "_" + df_temp['multiplier_label']
        fig_budget_allocation = budget_allocation_treemap_v2(
            df_temp, 
            path=[
                'multiplier_label',
                'position_label_1',
                'player_name'
                ],
                values='now_cost',
                color_columns=[
                    'rolling_points_total',
                    'now_cost'
                    ],
                    title='Budget Allocation Treemap')
        st.plotly_chart(fig_budget_allocation, width='stretch', 
                        key='budget_allocation_treemap_plot')
        
        st.write("""
                     The treemap shows how the manager has allocated their budget across
                     different positions. A very good team will have a lot of players in the 
                     'STARTER' category with a bluish hue. This indicates that the
                     manager has invested in high-performing players who contribute
                     significantly to the team's total points. If you have players
                     with deep red hues consider transferring them. Players in the 
                     'BENCH' category should ideally have a reddish hue as they
                     are not expected to contribute significantly to the team's points.
                     
                     With regards to dark red players. If this is a premium
                     player in the 'CAPTAINCY' category, it might be justifiable.
                     
                     Finally for starters with deep red hues, consider the following two triggers:
                     Trigger 1: The "Ceiling" check. If there is another player in that price bracket 
                     who has a higher raw points total, the red color is a valid warning sign. 
                     He is underperforming his price peers.
                     Trigger 2: The "Structure" check. If a premium player is red and you have holes elsewhere 
                     in your team (like a 4.0m defender who doesn't play), 
                     transferring the premium player down to a "Blue" value mid 
                     (like a £6.5m - £7.5m option) to fix your bench is a smart move.
                     """)
    else:
        st.warning("No manager data fetched yet. Please fetch a manager's team to analyze.")

    st.markdown("---")
    st.subheader("Efficiency Frontier Analysis")
    if st.session_state.fetched_fpl_data is not None:
        df_temp_ef = pd.pivot_table(
            data=st.session_state.fetched_fpl_data[['player_id', 'total_points']],
            index='player_id',
            values='total_points',
            aggfunc='sum').reset_index().sort_values(by='total_points', 
                                                     ascending=False
                                                     ).head(100).copy()
        
        df_temp_ef = pd.merge(
            df_temp_ef,
            st.session_state.fetched_fpl_data.loc[
                st.session_state.fetched_fpl_data['gw'] == gw, 
                ['player_id','player_name', 'now_cost',
                 'position', 'selected']],
                 on='player_id', how='left')
        
        df_temp_ef['ppm'] = df_temp_ef['total_points'] / gw

        df_temp_ef['position_label'] = df_temp_ef[
            'position'
            ].map(
                {
                    1: 'GK', 2: 'DEF', 3: 'MID', 4: 'FWD'
                    }
                    )
        
        df_temp_mg = st.session_state.fetched_manager_data[
            [
                'player_id','player_name','rolling_points_total',
                'position_label', 'now_cost', 'selected'
                ]].copy()
        df_temp_mg['ppm'] = df_temp_mg['rolling_points_total'] / gw
        fig_ef = efficiency_frontier(df_temp_ef, df_temp_mg)
        st.plotly_chart(fig_ef, width='stretch',key="efficiency_frontier_plot")
        st.write("""
                        The efficiency frontier plot illustrates the relationship between
                        player cost and points per million (PPM). The trendline indicates
                        the average efficiency across all players. Players positioned above
                        the trendline are considered more efficient, providing better value
                        for their cost, while those below the line are less efficient.
                     
                        When analyzing your team, look for your players that are below
                        the trendline. These players are underperforming relative to their cost
                        and may be candidates for transfer. You are paying a premium without
                        getting any use.
                     
                        Look for players who are way below the trendline and transfer them 
                        for players who are above.
                     """)
    else:
        st.warning("No FPL data fetched yet. Please fetch a manager's team to analyze.")
    
    st.markdown("---")
    st.subheader("CBIT Defense Analysis")
    if st.session_state.fetched_fpl_data is not None:

        selected_positions = st.multiselect(
            "Choose positions to display:",
            options=['DEF', 'MID', 'FWD'],
            default=['DEF', 'MID', 'FWD']
        )

        filtered_fpl_cbit_data = st.session_state.fetched_fpl_data[
            st.session_state.fetched_fpl_data['position_label'].isin(selected_positions)
        ]

        df_temp_cbit = filtered_fpl_cbit_data.loc[(filtered_fpl_cbit_data['gw'] == gw) &
                                                (
                                                    filtered_fpl_cbit_data[
                                                        'rolling_minutes_played'
                                                        ] >= 45*gw
                                                        ),
                                                        ['player_id','player_name', 
                                                         'now_cost', 'position_label', 
                                                         'selected', 'rolling_points_total',
                                                         'rolling_defensive_points',
                                                         'rolling_minutes_played',
                                                         'total_points',
                                                         'team_name']]
        df_temp_cbit['per_cbit'] = 100*(df_temp_cbit['rolling_defensive_points']/(2*gw))
        filtered_mng_cbit_data = st.session_state.fetched_manager_data[
            st.session_state.fetched_manager_data['position_label'].isin(selected_positions)
        ].copy()
        filtered_mng_cbit_data.reset_index(drop=True, inplace=True)
        temp = 100*(filtered_mng_cbit_data['rolling_defensive_points']/(2*gw))
        filtered_mng_cbit_data.loc[:,'per_cbit'] = temp

        df_temp_cbit.reset_index(drop=True, inplace=True)
        filtered_mng_cbit_data.reset_index(drop=True, inplace=True)
        
        fig_cbit_1 = scatter_plot(df_temp_cbit, 
                                hover_template_dict={"selected": 
                                                     (
                                                         "Selected By: ",
                                                         lambda x: f"{round(x/1e6,1)}M"),
                                                         "rolling_points_total": (
                                                             "Total Points: ", None
                                                             ),
                                                         "per_cbit": (
                                                             "CBIT %: ", 
                                                                      lambda x: round(x, 1)
                                                                      ),
                                                         "player_name": (
                                                             "Player: ", None
                                                             ),
                                                         "now_cost": (
                                                             "Cost: ", 
                                                                      lambda x: f"£{x/10}M"
                                                                      ),
                                                         "team_name": (
                                                             "Team: ", None
                                                             )},
                                                             x_column="rolling_points_total",
                                                             y_column="per_cbit",
                                                             category_column="position_label",
                                                             marker_column="rolling_points_total",
                                                             trendline_bool=True, 
                                                             df2=filtered_mng_cbit_data,
                                                             x_title="Total Points Gained",
                                                             y_title="Defensive Points Contribution per CBIT (%)")
        st.plotly_chart(fig_cbit_1, width='stretch', key="cbit_defense_plot")
        st.write("""
The CBIT (Clearances, Blocks, Interceptions, Tackles) Defense Aanalysis plot visualizes the
                     relationship between player cost and their defensive contributions
                     as a percentage of games where CBIT actions resulted in the 2+ points
                     bonus. Since the system does not rewards goalkeepers for CBIT actions
                     these are excluded from the plot.

To maximize your team's points haul we want to identify players that
                     provide strong defensive contributions relative to their cost. Players
                     positioned above the trendline are delivering better defensive value.
                     Players in the tope left quadrant (low cost/high % CBIT games) are
                     ideal as they provide strong defensive contributions at a lower cost.

The data points representing your team are highlighted with the star
                     symbol. Evaluate your players' positions relative to the trendline. 
                     The size of the markers indicates the total points scored 
                     by each player, providing additional context on their overall performance.
""")
    else:
        st.warning("No FPL data fetched yet. Please fetch a manager's team to analyze.")

    st.markdown("---")
    st.subheader("Fixture Adjusted Performance Analysis")
    if (
        st.session_state.fetched_manager_data is not None
        ) and (
            st.session_state.fetched_fpl_data is not None
            ):
        players_names = st.session_state.fetched_manager_data['player_name'].tolist()
        player_id_name_map = dict()
        for _, row in st.session_state.fetched_manager_data.iterrows():
            player_id_name_map[row['player_name']] = row['player_id']

        print(player_id_name_map)
        # Create player selection
        selected_player = st.selectbox(
            "Select Player:",
            options=players_names,
            index=0 if players_names else None,
            help="Choose a player from your team to view their fixture difficulty"
            )

        fig_fac = create_fixture_adjusted_chart(
            manager_df=st.session_state.fetched_fpl_data,
            player_id=player_id_name_map[selected_player],
            player_name=selected_player)
        st.plotly_chart(fig_fac, width='stretch', key="fixture_adjusted_performance_plot")
    else:
        st.warning("No manager data fetched yet. Please fetch a manager's team to analyze.")
    
        