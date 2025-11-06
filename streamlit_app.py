import streamlit as st
import plotly.express as px
import pandas as pd
import requests
import pymongo
from urllib.parse import quote_plus

# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------
st.set_page_config(
    page_title="Elhub & Open-Meteo Dashboard",
    layout="wide",
    page_icon="⚡"
)

# ------------------------------------------------------------
# IMPORT PAGES
# ------------------------------------------------------------
from modules.page_1 import show as page1
from modules.page_2 import show as page2
from modules.page_3 import show as page3
from modules.page_4 import show as page4
from modules.page_5 import show as page5
from modules.page_6 import show as page6
from modules.page_7 import show as page7

# ------------------------------------------------------------
# 1. Helper: Load Open-Meteo Data (cached)
# ------------------------------------------------------------
@st.cache_data(show_spinner="Fetching Open-Meteo data ...")
def hent_open_meteo_data(lat, lon, year=2021):
    """Fetch hourly ERA5 data from Open-Meteo API."""
    url = (
        f"https://archive-api.open-meteo.com/v1/era5?"
        f"latitude={lat}&longitude={lon}&"
        f"start_date={year}-01-01&end_date={year}-12-31&"
        "hourly=temperature_2m,precipitation,wind_speed_10m,wind_gusts_10m,wind_direction_10m&"
        "timezone=auto"
    )

    r = requests.get(url)
    r.raise_for_status()
    data = r.json()
    df = pd.DataFrame(data["hourly"])
    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    df["month"] = df["time"].dt.month
    return df

# ------------------------------------------------------------
# 2. Load data into session_state (only once)
# ------------------------------------------------------------
if "meteo_df" not in st.session_state or st.session_state["meteo_df"] is None:
    st.info("⏳ No weather data in memory — fetching default data for Oslo (NO1, 2021)...")

    lat, lon = 59.9139, 10.7522  # Oslo / NO1
    df = hent_open_meteo_data(lat, lon, 2021)

    st.session_state["meteo_df"] = df
    st.session_state["selected_area"] = "NO1"
else:
    df = st.session_state["meteo_df"]

# ------------------------------------------------------------
# 3. Sidebar navigation
# ------------------------------------------------------------
st.sidebar.title("📍 Navigation")
page = st.sidebar.radio(
    "Go to page:",
    [
        "Home",
        "Elhub production statistics",
        "STL and Spectrogram",
        "Elhub (MongoDB)",
        "Open-Meteo",
        "SPC and LOF analysis",
        "Check weather data"
    ]
)

# ------------------------------------------------------------
# 4. Background color selector
# ------------------------------------------------------------
color_choice = st.selectbox(
    "Choose background color:",
    ["White", "Blue", "Green", "Yellow", "Gray", "Red", "Black"]
)

colors = {
    "White": "#FFFFFF",
    "Blue": "#0000FF",
    "Green": "#008000",
    "Yellow": "#FFFF00",
    "Gray": "#808080",
    "Red": "#FF0000",
    "Black": "#000000",
}
bg_color = colors[color_choice]

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {bg_color};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------------------------------------
# 5. Page routing
# ------------------------------------------------------------
if page == "Home":
    page1()
elif page == "Elhub production statistics":
    page2()
elif page == "STL and Spectrogram":
    page3()
elif page == "Elhub (MongoDB)":
    page4()
elif page == "Open-Meteo":
    page5()
elif page == "SPC and LOF analysis":
    page6()
elif page == "Check weather data":
    page7()

