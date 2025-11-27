import streamlit as st
import pandas as pd
import plotly.express as px
from functions.load_data import load_elhub_data


def show():

    # ================================
    # TITLE
    # ================================
    st.markdown(
        """
        <h1 style='text-align:center; font-size:52px; margin-bottom:0px;'>
            ⚡ Energi & Klima Dashboard
        </h1>
        <p style='text-align:center; font-size:20px; color:#666; margin-top:0;'>
            Analyse av energiproduksjon, forbruk, værdata, korrelasjoner og snødrift i Norge
        </p>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    # ================================
    # QUICK ACCESS BUTTONS
    # ================================
    col1, col2, col3 = st.columns(3)

    # -------------------------------
    # Column 1
    # -------------------------------
    with col1:
        st.markdown("#### 🗺️ Kart & Snø")
        st.button("Geo Map & Snow Drift")

        st.markdown("#### ⚡ Elhub")
        st.button("Elhub produksjon")

    # -------------------------------
    # Column 2
    # -------------------------------
    with col2:
        st.markdown("#### 🌦️ Værdata")
        st.button("Open-Meteo Weather")

        st.markdown("#### 🧪 Analyseverktøy")
        st.button("SPC & LOF Analysis")

    # -------------------------------
    # Column 3
    # -------------------------------
    with col3:
        st.markdown("#### 🔗 Korrelasjoner")
        st.button("Sliding Correlation")

        st.markdown("#### 📊 MongoDB")
        st.button("MongoDB Insights")

    st.markdown("---")

    # ================================
    # 📘 INFORMASJONSBOKSER
    # ================================
    st.markdown("## 📘 Hva inneholder de ulike sidene?")
    st.markdown("En rask oversikt over dashboardets analysefunksjoner:")

    info1, info2 = st.columns(2)

    # -------------------------------
    # LEFT COLUMN
    # -------------------------------
    with info1:
        # ⚡ ENERGY & ELHUB
        st.markdown("### ⚡ Energy & Elhub")
        st.info(
            """
            - Produksjonsanalyse  
            - Elhub-data (fra MongoDB)  
            - Tidsserier og visualisering  
            - STL & Spektrogram  
            - SARIMAX-baserte prognoser  
            """
        )

        # 🌍 GEO & SNOW
        st.markdown("### 🌍 Geo & Snow")
        st.info(
            """
            - Geografiske kart  
            - Snødrift-modellering  
            - Vindretning & snøtransport  
            """
        )

    # -------------------------------
    # RIGHT COLUMN
    # -------------------------------
    with info2:
        # 🌦️ METEOROLOGY
        st.markdown("### 🌦️ Meteorology")
        st.info(
            """
            - Open-Meteo rådata  
            - Kontroller værdata  
            - Værvariabler time for time  
            """
        )

        # 🌡️ WEATHER, CONSUMPTION & PRODUCTION
        st.markdown("### 🌡️ Weather, Consumption & Production")
        st.info(
            """
            - LOF (Local Outlier Factor) – avviksdeteksjon  
            - SPC (Statistical Process Control)  
            - Sliding Window Correlation  
            - Samspill mellom temperatur, nedbør, forbruk og produksjon  
            """
        )

    st.markdown("---")

    # ================================
    # FOOTER
    # ================================
    st.markdown(
        """
        <p style='text-align:center; color:#888; font-size:14px;'>
            © 2025 Energi & Klima Dashboard – laget for innsikt, analyse og utforskning 🌍⚡
        </p>
        """,
        unsafe_allow_html=True
    )
