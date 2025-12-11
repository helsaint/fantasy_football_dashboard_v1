import requests
import streamlit as st
# Cache the API calls to avoid rate limiting
@st.cache_data(ttl=300)  # Cache for 5 minutes (shorter for manager data)
def fetch_manager_data(manager_id, gameweek):
    """Fetch manager team data from FPL API"""
    try:
        url = f"https://fantasy.premierleague.com/api/entry/{manager_id}/event/{gameweek}/picks/"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        if response.status_code == 404:
            st.error(f"Manager ID {manager_id} not found or no data for GW{gameweek}.")
        else:
            st.error(f"Error fetching manager data: {e}")
        return None