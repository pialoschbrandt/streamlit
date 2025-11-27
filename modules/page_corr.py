# page_corr.py
import streamlit as st
import pandas as pd
import plotly.express as px

from functions.load_data import load_era5_raw, load_elhub_data


# ------------------------------------------------------------
# Sliding window correlation
# ------------------------------------------------------------
def sliding_corr(df, met_var, energy_var, lag_hours, window):
    """Compute sliding correlation between weather and energy time series."""
    s1 = df[met_var]
    s2 = df[energy_var].shift(lag_hours)

    corr = s1.rolling(window=window).corr(s2)

    return pd.DataFrame({"time": df["time"], "corr": corr})


# ------------------------------------------------------------
# MAIN PAGE
# ------------------------------------------------------------
def show():

    st.title("📈 Sliding Window Correlation – Meteorologi vs Energi")

    st.markdown(
        """
        Denne siden lar deg analysere **sammenhengen mellom vær og energiforbruk** 
        ved hjelp av *glidende korrelasjon*.  

        Du kan:
        - sammenligne ulike værvariabler mot energiforbruk  
        - teste forskjellige tidsetterslep (*lag*)  
        - bruke glidende vinduer for å se hvordan sammenhengen endrer seg over tid  

        Glidende korrelasjon er nyttig for å forstå om:
        - temperatur, vind eller nedbør påvirker forbruk  
        - effekten kommer **før**, **samtidig**, eller **forsinket**  
        - sammenhengen er sterkere i enkelte perioder  
        """
    )

    st.info("Velg by, variabler og parametere i sidefeltet for å beregne glidende korrelasjon.")

    # ------------------------------------------------------------
    # 1) Velg by for værdata
    # ------------------------------------------------------------
    CITIES = {
        "Oslo": (59.9139, 10.7522),
        "Bergen": (60.39299, 5.32415),
        "Stavanger": (58.96998, 5.73311),
        "Trondheim": (63.4305, 10.3951),
        "Tromsø": (69.6492, 18.9553),
        "Kristiansand": (58.1467, 7.9956)
    }

    st.sidebar.subheader("📍 Velg by for værdata")

    city = st.sidebar.selectbox(
        "By:",
        list(CITIES.keys()),
        help="Velg hvilken by værdata skal hentes fra."
    )

    lat, lon = CITIES[city]

    # ------------------------------------------------------------
    # 2) Last værdata og energidata
    # ------------------------------------------------------------
    with st.status("Henter værdata og energidata...", expanded=False):
        meteo = load_era5_raw(lat, lon, 2021)
        energy = load_elhub_data()

    meteo["time"] = pd.to_datetime(meteo["time"])
    energy["start_time"] = pd.to_datetime(energy["start_time"])

    # Aggregér energiproduksjon pr time
    energy_hourly = (
        energy.groupby("start_time")["quantity_kwh"]
        .sum()
        .reset_index()
        .rename(columns={"start_time": "time", "quantity_kwh": "energy_kwh"})
    )

    # Merge vær + energi
    df = pd.merge(meteo, energy_hourly, on="time", how="inner").sort_values("time")

    # ------------------------------------------------------------
    # 3) Sidebar – velg parametere
    # ------------------------------------------------------------
    st.sidebar.header("🔧 Parametere")

    st.sidebar.markdown("Justér korrelasjonsanalysen:")

    met_vars = [c for c in meteo.columns if c not in ["time"]]
    energy_vars = ["energy_kwh"]

    # Meteorologisk variabel
    met_var = st.sidebar.selectbox(
        "🌦️ Meteorologisk variabel",
        met_vars,
        help="Velg hvilken værvariabel som skal sammenlignes med energiforbruket."
    )

    # Energivariabel
    energy_var = st.sidebar.selectbox(
        "⚡ Energivariabel",
        energy_vars,
        help="Timeoppløst energiproduksjon akkumulert fra Elhub-data."
    )

    # Lag
    lag = st.sidebar.slider(
        "⏱️ Lag (timer)",
        -72, 72, 0,
        help=(
            "Forskyver energiserien i tid.\n\n"
            "**Positiv lag (+24):** Været skjer FØR energiforbruket\n"
            "**Negativ lag (–24):** Energiforbruket skjer FØR været\n"
            "Bruk dette for å avdekke forsinkede effekter."
        )
    )

    # Vindu
    window = st.sidebar.slider(
        "📏 Vindu (timer)",
        6, 240, 72, 6,
        help=(
            "Antall timer som brukes til å beregne glidende korrelasjon.\n"
            "• Lite vindu → mer detaljer, men mer støy\n"
            "• Stort vindu → jevnere kurve, men mindre detaljer"
        )
    )

    # ------------------------------------------------------------
    # 4) Beregn korrelasjon
    # ------------------------------------------------------------
    corr_df = sliding_corr(df, met_var, energy_var, lag, window)

    # ------------------------------------------------------------
    # 5) Plot korrelasjon
    # ------------------------------------------------------------
    st.subheader("📉 Glidende korrelasjon")

    st.markdown(
        f"""
        **Tolkning av korrelasjon:**
        - **+1** → sterk positiv sammenheng  
        - **–1** → sterk negativ sammenheng  
        - **0** → ingen tydelig sammenheng  

        Variablene du sammenligner:
        **{met_var}** (vær) vs **{energy_var}** (energi)
        """
    )

    fig = px.line(
        corr_df,
        x="time",
        y="corr",
        title=f"Korrelasjon mellom {met_var} og {energy_var} (lag={lag}t, vindu={window}t)",
        labels={"corr": "Korrelasjon", "time": "Tid"}
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    st.plotly_chart(fig, use_container_width=True)

    # ------------------------------------------------------------
    # 6) Vis rå tidsserier
    # ------------------------------------------------------------
    with st.expander("📊 Vis tidsserier for valgte variabler"):
        st.markdown("Under ser du de faktiske målingene som korrelasjonen er basert på:")
        fig2 = px.line(
            df,
            x="time",
            y=[met_var, energy_var],
            labels={"value": "Verdi", "variable": "Serie"},
            title=f"Tidsserier: {met_var} og {energy_var}"
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ------------------------------------------------------------
    # Tips
    # ------------------------------------------------------------
    st.info(
        """
        **Tips for tolkning:**
        - Prøv forskjellige byer for å se geografiske forskjeller  
        - Test flere negative eller positive lag for å avdekke tidsetterslep  
        - Øk vinduet hvis kurven er veldig støyete  
        - Undersøk rå tidsserier for å forstå korrelasjonen visuelt  
        """
    )
