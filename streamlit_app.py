import streamlit as st
import plotly.express as px
import requests
import pandas as pd
from pymongo import MongoClient
import pymongo
from urllib.parse import quote_plus

# Importer sidene
from modules.page_1 import show as page1
from modules.page_2 import show as page2
from modules.page_3 import show as page3
from modules.page_4 import show as page4
from modules.page_5 import show as page5


# Hent data fra MongoDB (brukes hvis du skal teste direkte)
def get_data(col):
    try:
        docs = list(col.find().limit(10))
        if docs:
            df = pd.DataFrame(docs)
            return df
        else:
            st.info("Ingen dokumenter funnet i samlingen.")
    except Exception as e:
        st.error(f"Feil ved henting av data: {e}")

# Navigasjon i sidebar
st.sidebar.title("Navigasjon")
page = st.sidebar.radio(
    "Gå til:",
    ["Hjem", "Side 2: Tabell", "Side 3: Plot", "Side 4: Elhub", "Side 5: Open-Meteo"]
)

# Filsti til CSV
file = "open-meteo-subset.csv"

# Hent data (caches slik at den ikke lastes flere ganger)
@st.cache_data
def load_data(file):
    df = pd.read_csv(file)
    df["time"] = pd.to_datetime(df["time"])
    df["month"] = df["time"].dt.month
    return df

df = load_data(file)

# Velg bakgrunnsfarge
color_choice = st.selectbox(
    "Velg bakgrunnsfarge:",
    ["Hvit", "Blå", "Grønn", "Gul", "Grå", "Rød", "Svart"]
)

colors = {
    "Hvit": "#FFFFFF",
    "Blå": "#0000FF",
    "Grønn": "#008000",
    "Gul": "#FFFF00",
    "Grå": "#808080",
    "Rød": "#FF0000",
    "Svart": "#000000",
}
bg_color = colors[color_choice]

# Bruk CSS til å endre bakgrunnsfargen
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

# Koble til de ulike sidene
if page == "Hjem":
    page1()
elif page == "Side 2: Tabell":
    page2(df)
elif page == "Side 3: Plot":
    page3(df)
elif page == "Side 4: Elhub":
    page4()
elif page == "Side 5: Open-Meteo":
    page5()
