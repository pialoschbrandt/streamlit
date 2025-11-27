import streamlit as st

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
        st.button("Open-Meteo værdata")

        st.markdown("#### 🧪 Analyseverktøy")
        st.button("SPC & LOF analyse")

    # -------------------------------
    # Column 3
    # -------------------------------
    with col3:
        st.markdown("#### 🔗 Korrelasjoner")
        st.button("Sliding Correlation")

        st.markdown("#### 📊 MongoDB")
        st.button("MongoDB analyser")

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
        st.markdown("### ⚡ Energy & Elhub")
        st.info(
            """
            - Elhub production statistics  
            - STL and Spectrogram  
            - Elhub (MongoDB)  
            - Energy Forecast (SARIMAX)
            """
        )

        st.markdown("### 🌍 Geo Map & Snow")
        st.info(
            """
            - Geografisk visualisering  
            - Snødriftmodell  
            - Vindretning og snøtransport  
            """
        )

    # -------------------------------
    # RIGHT COLUMN
    # -------------------------------
    with info2:
        st.markdown("### 🌦️ Meteorology")
        st.info(
            """
            - Open-Meteo Raw Data  
            - Check Weather Data  
            """
        )

        st.markdown("### 🌡️ Weather, Consumption & Production")
        st.info(
            """
            - SPC & LOF anomalies (temperatur + nedbør)  
            - Sliding Window Correlation (vær vs energi)  
            - Sammenhenger mellom forbruk, produksjon og vær
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
