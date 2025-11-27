import streamlit as st
import pandas as pd
import plotly.express as px
import requests


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
from modules.page_Geo import show as page_geo
from modules.page_corr import show as page_corr
from modules.page_forecast import show as page_forecast   


# ------------------------------------------------------------
# Load weather (cached)
# ------------------------------------------------------------
@st.cache_data(show_spinner="Fetching Open-Meteo data ...")
def hent_open_meteo_data(lat, lon, year=2021):
    url = (
        f"https://archive-api.open-meteo.com/v1/era5?"
        f"latitude={lat}&longitude={lon}&"
        f"start_date={year}-01-01&end_date={year}-12-31&"
        "hourly=temperature_2m,precipitation,wind_speed_10m,"
        "wind_gusts_10m,wind_direction_10m&timezone=auto"
    )
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()
    df = pd.DataFrame(data["hourly"])
    df["time"] = pd.to_datetime(df["time"])
    df["month"] = df["time"].dt.month
    return df


# ------------------------------------------------------------
# Load default weather on startup
# ------------------------------------------------------------
if "meteo_df" not in st.session_state:
    st.info("⏳ Loading default ERA5 weather for Oslo...")
    df = hent_open_meteo_data(59.91, 10.75, 2021)
    st.session_state["meteo_df"] = df
    st.session_state["selected_area"] = "NO1"


# ------------------------------------------------------------
# NAVIGATION (fixed with keys)
# ------------------------------------------------------------
st.sidebar.title("📍 Navigation")

category = st.sidebar.radio(
    "Choose category:",
    [
        "🏠 Home",
        "⚡ Energy & Elhub",
        "🌦️ Meteorology",
        "Weather, Consumption & Production",
        "🌍 Geo & Snow"
    ],
    key="nav_category"
)

# ---------------- HOME ----------------
if category == "🏠 Home":
    page = st.sidebar.radio("Subpage:", ["Welcome"], key="nav_home")

# ---------------- ENERGY SECTION ----------------
elif category == "⚡ Energy & Elhub":
    page = st.sidebar.radio(
        "Subpage:",
        [
            "Elhub production statistics",
            "STL and Spectrogram",
            "Elhub (MongoDB)",
            "Energy Forecast (SARIMAX)",
        ],
        key="nav_energy"
    )

# ---------------- METEOROLOGY ----------------
elif category == "🌦️ Meteorology":
    page = st.sidebar.radio(
        "Subpage:",
        [
            "Open-Meteo Raw Data",
            "Check weather data",
        ],
        key="nav_meteo"
    )

# ---------------- NEW CATEGORY ----------------
elif category == "Weather, Consumption & Production":
    page = st.sidebar.radio(
        "Subpage:",
        [
            "SPC & LOF anomalies",
            "Sliding Correlation",
        ],
        key="nav_weather_prod"
    )

# ---------------- GEO ----------------
elif category == "🌍 Geo & Snow":
    page = st.sidebar.radio(
        "Subpage:",
        ["Geo Map & Snow Drift"],
        key="nav_geo"
    )


# ------------------------------------------------------------
# ROUTING 
# ------------------------------------------------------------
if page == "Welcome":
    page1()

elif page == "Elhub production statistics":
    page2()

elif page == "STL and Spectrogram":
    page3()

elif page == "Elhub (MongoDB)":
    page4()

elif page == "Open-Meteo Raw Data":
    page5()

elif page == "Check weather data":
    page7()

elif page == "SPC & LOF anomalies":
    page6()

elif page == "Sliding Correlation":
    page_corr()

elif page == "Geo Map & Snow Drift":
    page_geo()

elif page == "Energy Forecast (SARIMAX)":  
    page_forecast()


