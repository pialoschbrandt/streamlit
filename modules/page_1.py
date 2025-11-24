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
            Analyse av energiproduksjon, forbruk, værdata og snødrift i Norge
        </p>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    # -------------------------------
    # ↪ Geo Map
    # -------------------------------
    with col1:
        st.markdown("#### 🗺️ Kart & Snø")
        if st.button("Geo Map & Snow Drift"):
            st.balloons()

        st.markdown("#### ⚡ Elhub")
        if st.button("Elhub produksjon"):
            st.balloons()

    # -------------------------------
    # ↪ Weather / SPC
    # -------------------------------
    with col2:
        st.markdown("#### 🌦️ Værdata")
        if st.button("Open-Meteo værdata"):
            st.balloons()

        st.markdown("#### 🧪 Analyseverktøy")
        if st.button("SPC & LOF analyse"):
            st.balloons()

    # -------------------------------
    # ↪ Snow / MongoDB
    # -------------------------------
    with col3:
        st.markdown("#### ❄️ Snødrift")
        if st.button("Snow Drift Analysis"):
            st.balloons()

        st.markdown("#### 📊 MongoDB")
        if st.button("MongoDB analyser"):
            st.balloons()

    st.markdown("---")

    # ================================
    # 📘 INFORMASJONSBOKSER
    # ================================
    st.markdown("## 📘 Hva inneholder de ulike sidene?")
    st.markdown("Her er en oversikt over hva du finner i hver kategori.")

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
            - SPC and LOF analysis  
            - Forecast av energiproduksjon og energiforbruk (SARIMAX)
            """
        )

        st.markdown("### 🌍 Geo Map & Snow")
        st.info(
            """
            - Geo Map & Snow Drift  
            - Statistikk per område  
            - Snødriftmodell og vindrose  
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
            - Sliding Correlation  
            """
        )


    st.markdown("---")

    # ================================
    # FOOTER
    # ================================
    st.markdown(
        "<p style='text-align:center; color:#888; font-size:14px;'>"
        "© 2025 Energi & Klima Dashboard – laget for analyse og utforskning 🎈"
        "</p>",
        unsafe_allow_html=True
    )
