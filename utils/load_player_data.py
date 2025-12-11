import requests
import streamlit as st

@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_fpl_bootstrap():
    """Fetch bootstrap-static data from FPL API"""
    try:
        url = "https://fantasy.premierleague.com/api/bootstrap-static/"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching FPL data: {e}")
        return None