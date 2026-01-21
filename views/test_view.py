import streamlit as st
import pandas as pd
import numpy as np
from utils.load_fpl_features import load_player_data


def show(df):
    st.header("Test View for Development")
    st.write("This is a placeholder for testing new features and visualizations.")
    st.write("Data sample:")

    # Title
    st.title("Understanding Session State")

    # STEP 1: Initialize session state variables
    if 'data' not in st.session_state:
        st.session_state.data = None
        st.write("✅ Initialized: st.session_state.data = None")

    # STEP 2: Show current session state
    st.write("### Current Session State:")
    st.write(st.session_state)

    # Separator
    st.divider()

    # STEP 3: Button to "fetch" data (simulating API call)
    if st.button("📥 Fetch Data"):
        # Create sample data
        '''
        df = pd.DataFrame({
            'position': ['DEF', 'DEF', 'MID', 'MID', 'FWD', 'FWD'],
            'value': [10, 20, 30, 40, 50, 60]
        })
        '''
        position_map = {1: 'GK', 2: 'DEF', 3: 'MID', 4: 'FWD'}
        df = load_player_data().sample(20)  # Load a sample of FPL
        df['position_label'] = df['position'].map(position_map)
        
        # Store in session state
        st.session_state.data = df[['player_name',
                                    'position_label',
                                    'total_points']].head(20).copy()
        st.success(f"Data fetched! Shape: {df.shape}")
        st.write(df)

    # STEP 4: Only show filter IF data exists
    if st.session_state.data is not None:
        st.divider()
        st.write("### Now Apply Filters")
        
        # Multi-select filter
        selected_positions = st.multiselect(
            "Choose positions to display:",
            options=['GK', 'DEF', 'MID', 'FWD'],
            default=['GK', 'DEF', 'MID', 'FWD']
        )
        
        # Apply filter to the session state data
        filtered_df = st.session_state.data[
            st.session_state.data['position_label'].isin(selected_positions)
        ]
        
        # Show filtered data
        st.write(f"### Filtered Data ({len(filtered_df)} rows)")
        st.write(filtered_df)
        
        # Show original data still exists
        st.write("### Original data still in session_state:")
        st.write(f"Original shape: {st.session_state.data.shape}")
    else:
        st.info("👆 Click 'Fetch Data' button first to load data")

    # STEP 5: Add a reset button
    st.divider()
    if st.button("🔄 Reset All Data"):
        # Clear session state
        st.session_state.data = None
        st.rerun()  # Force refresh to show changes
    