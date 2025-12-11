from datetime import datetime
import streamlit as st
from utils.load_player_data import fetch_fpl_bootstrap


def fpl_search_inputs():
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

    return manager_id, gw