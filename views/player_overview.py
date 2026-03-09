import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go
from utils.load_fpl_features import load_player_data, load_fpl_points_prediction
from utils.scatter_plot import scatter_plot
from utils.scaling import percentile_scaling


def show(filtered_df):
    st.header("Player Performance Overview")

    if 'fetched_fpl_data_overview' not in st.session_state:
        st.session_state.fetched_fpl_data_overview = None
    if 'filtered_player_data' not in st.session_state:
        st.session_state.filtered_player_data = None
    if 'fetched_fpl_points_prediction' not in st.session_state:
        st.session_state.fetched_fpl_points_prediction = None
    if 'filtered_predicted_points' not in st.session_state:
        st.session_state.filtered_predicted_points = None

    df_fpl_features = load_player_data()
    if st.session_state.fetched_fpl_data_overview is None:
        st.session_state.fetched_fpl_data_overview = df_fpl_features.copy()

    df_fpl_points_prediction = load_fpl_points_prediction()
    
    if st.session_state.fetched_fpl_points_prediction is None:
        st.session_state.fetched_fpl_points_prediction = df_fpl_points_prediction.copy()


    st.subheader("HTB Target Database")
    # 1. Create a dictionary to map ID -> Display Label
    # This makes lookups instant and clean
    player_options = st.session_state.fetched_fpl_data_overview.set_index('player_id').apply(
        lambda x: f"{x['player_name']} ({x['team']})", axis=1
        ).to_dict()
    # Use selectbox as a search bar
    # index=None ensures it starts empty
    # 2. The Search Bar
    selected_id = st.selectbox(
        "Search for a player:",
        options=player_options.keys(), # This stores the player_id
        format_func=lambda x: player_options[x], # This shows "Name (Team)"
        index=None,
        placeholder="Type a name (e.g., 'Virgil')..."
        )
    # 3. Action based on selection
    if selected_id:
        # Pull the specific row for the unique ID
        player_data = st.session_state.fetched_fpl_data_overview[
            st.session_state.fetched_fpl_data_overview['player_id'] == selected_id].reset_index(
                drop=True)
        predicted_data = st.session_state.fetched_fpl_points_prediction[
            st.session_state.fetched_fpl_points_prediction[
                'player_id'] == selected_id].reset_index(
                drop=True)
        st.session_state.filtered_player_data = player_data
        
        st.session_state.filtered_predicted_points = predicted_data

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Player Name", player_data.loc[0,'player_name'])
            st.caption(f"ID: {selected_id}")
        with col2:
            st.metric("Team", player_data.loc[0,'team'])
            st.write(f"**Team:** {player_data.loc[0,'team']}")

    if (
        st.session_state.filtered_player_data is not None
        ):
        col1, col2, col3, col4 = st.columns(4)
        player_data = st.session_state.filtered_player_data.copy()
    
        with col1:
            st.metric("Total Points", 
                      f"{st.session_state.filtered_player_data['total_points'].sum():,}")
        with col2:
            st.metric("Goals Scored", 
                      f"{st.session_state.filtered_player_data['goals_scored'].sum():,}")
        with col3:
            st.metric("Assists", 
                      f"{st.session_state.filtered_player_data['assists'].sum():,}")
        with col4:
            st.metric("Games over 60 mins", 
                      f"{st.session_state.filtered_player_data['played_60'].sum():,}")
        
        st.markdown("---")
        st.subheader("Residual Performance Analysis")
        player_data['goals_assists'] = player_data['goals_scored'] + player_data['assists']
        
        fig_rpa = go.Figure()
        fig_rpa.add_trace(
            go.Scatter(
                x=player_data['gw'],
                y=player_data['goals_assists'],
                mode='markers+lines',
                name='Goals/Assists',
            )
        )
        fig_rpa.add_trace(
            go.Scatter(
                x=player_data['gw'],
                y=player_data['expected_goal_involvements'],
                mode='markers+lines',
                name='Expected Goal Involvement',
            )
        )

        st.plotly_chart(fig_rpa, width='stretch', key="rpa_chart")
        st.write("This is mainly used for attacking players")
        st.write("- The Overperformer: If we see a player's points being consistently" \
        "above that of the expected goals involvement then this player is overperforming." \
        " The player is returning more points than the quality of their chances suggests." \
        " This indicates a strong finishing ability. If the player hasn't been consistent" \
        " like Haaland then expect a regression to the mean. The streak may be unsustainable" \
        " and you should consider transferring out the player as soon as there is a dip in" \
        " form")
        st.write("- The Underperfromer: This is shown by the expected goals and assists" \
        " line being consistently above the actual goals+assits lines. This indicates that" \
        " the player is getting into good positions but is not scoring. If this is unusual" \
        " behavior expect the player to eventually 'come good' and they are a candidate" \
        " as a differential buy.")
        st.write("- The Reliable Asset: The player is scoring the points we expect them" \
        " they are consistent and we can count on their points.")

        st.markdown("---")
        st.subheader("Noise vs Signal")

        fig_nsv = go.Figure()
        fig_nsv.add_trace(
            go.Scatter(
                x=player_data['gw'],
                y=player_data['total_points'],
                mode='markers+lines',
                name='Total Points',
            )
        )
        fig_nsv.add_trace(
            go.Scatter(
                x=player_data['gw'],
                y=player_data['pts_ewma'],
                mode='markers+lines',
                name='Weighted Moving Average',
            )
        )
        fig_nsv.add_trace(
            go.Scatter(
                x=player_data['gw'],
                y=player_data['pts_roll_5'],
                mode='markers+lines',
                name='Rolling 5',
            )
        )

        st.plotly_chart(fig_nsv, width='stretch', key="nsv_chart")
        st.write(" We use Total Points to see the ceiling, the Rolling 5 to capture the" \
        " current player's current form, and the EWMA to provide a weighted baseline that" \
        " filters out the chaos of a single gameweek.")
        st.write("- The Breakout: the Rolling 5 crosses above the Weighted Moving Average" \
        " The player is in a hot streak. Their current form is better than their season" \
        " average.")
        st.write("- The Slump: the Rolling 5 crosses below the Weighted Moving Average." \
        " The player's form has dropped below their baseline. They may be a good candidate" \
        " to bench.")
        st.write("- The Trap: the weighted moving average is steady but we see actual points" \
        " spikes. Don't chase this player unless their Weighted Moving Average is also" \
        " increasing.")

        st.markdown("---")
        st.subheader("Contextual Value")

        fig_context = go.Figure()
        fig_context.add_trace(
            go.Scatter(
                x=5*(
                    player_data['opp_strength_defence']/player_data['opp_strength_defence'].max()
                ),
                y=player_data['expected_goal_involvements'],
                mode='markers',
                name='Contextual Value'
            )
        )

        fig_context_1, r2 = scatter_plot(
            main_df=player_data,
            hover_template_dict={
                'total_points': ("Points: ", None),
                'opponent_team_name': ("Opponent: ", None),
                'selected': (
                    "Selected By: ",
                    lambda x: f"{round(x/1e6,1)}M"
                    ),
                'gw': ("GW: ", None),
            },
            x_column = 'opp_strength_defence',
            y_column = 'expected_goal_involvements',
            marker_column="total_points",
            category_column='player_name',
            trendline_bool=True,
            x_title="Opponent Defensive Strength",
            y_title="Expected Goal Involvements"
        )
        st.caption(f"**$R^2$** = **{r2}%**")

        st.plotly_chart(fig_context_1,width='stretch', key='context_chart')
        st.write(" Here we measure player consistency against opponent difficulty." \
        " This chart is also attacker oriented and will not be useful for goalkeeper" \
        " analysis or defenders who you don't expect to be much attack oriented." \
        " Finally a player may be overperfoming their xGI, having a purple season/patch," \
        " take this into consideration.")
        st.write("- The Flat Track Bully: The player thrives against weak opposition" \
        " while finding opportunities difficult to come by against tougher teams." \
        " Consider difficulty of the fixture and rotate this player as needed.")
        st.write("- The Big Game Player: This player does well as the opponent gets" \
        " tougher. This is a set and forget asset. However, ensure that the expected" \
        " goal involvements are high and not something between 0-0.5. As the trend may" \
        " be upward but the underlying expectations are pretty poor.")
        st.write("- High Volatility: Be careful with this. The trendline may be steep" \
        " but the player is very inconsistent. Look at the $R^2$ value.")
        st.write("- $R^2$ Value: Here we represent the R^2 value as percentage." \
        " Strictly speaking this value tells us if the trendline is useful in decision" \
        " making. A high $R^2$ value means that the trendline is a good indicator while" \
        " a low $R^2$ value indicates that the trendline/opposition strength is a" \
        " secondary indicator of performance indicator.")
        dict_R_2 = {
            "$R^2$": [f"70% - 100%", f"40% - 70%", f"10% - 40%", f"<10%"],
            "Strength": ["High", "Moderate", "Low", "Negligible"],
            "Description": ["This would mean a player is almost perfectly predictable "
            "based on the opponent's strength", "This is a reliable trend you can use "
            "to plan transfers weeks in advance.", "It shows a trend exists, but luck "
            "plays a big role.", "The metric has almost no impact on the outcome."]
            }
        st.table(dict_R_2)

        st.markdown("---")
        st.subheader("Efficiency Radar")
        metrics = [
            'bps_per90',
            'points_per90', 
            'expected_goal_involvements', # Use the season avg version
            'defensive_contribution',     # You may need to avg your 'form' columns
            'ict_index'
        ]

        df_fpl_features_scaled = percentile_scaling(
            st.session_state.fetched_fpl_data_overview[
                st.session_state.fetched_fpl_data_overview[
                    'rolling_minutes_total'
                    ] > 400],
            metrics).copy()
    
        df_fpl_features_scaled_player = df_fpl_features_scaled[
            df_fpl_features_scaled['player_id'] == selected_id
            ].copy()
        
        season_avg = df_fpl_features_scaled_player[
            metrics
            ].mean().tolist()
        recent_form = df_fpl_features_scaled_player.sort_values(
            'gw'
            ).dropna().tail(5)[metrics].mean().tolist()

        metrics_closed = metrics + [metrics[0]]
        season_avg += [season_avg[0]]
        recent_form += [recent_form[0]]

        fig_der = go.Figure()
        fig_der.add_trace(go.Scatterpolar(
            r=season_avg,
            theta=metrics_closed,
            fill='toself',
            name='Season Average',
            line_color='rgba(150, 150, 150, 0.5)',
            fillcolor='rgba(150, 150, 150, 0.2)'
            ))
        
        # Add Recent Form Trace
        fig_der.add_trace(go.Scatterpolar(
            r=recent_form,
            theta=metrics_closed,
            fill='toself',
            name='Last 5 GWs (Form)',
            line_color='deepskyblue',
            fillcolor='rgba(0, 191, 255, 0.3)'
        ))

        fig_der.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        showlegend=True,
        title=f"Player DNA: Season vs. Recent Form"
        )

        st.plotly_chart(fig_der, width='stretch', key='fig_der')

        st.markdown("---")
        st.subheader("Player Expected Points Next GW")
        st.dataframe(st.session_state.filtered_predicted_points)
