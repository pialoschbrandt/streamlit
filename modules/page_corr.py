# page_corr.py
import streamlit as st
import pandas as pd
import plotly.express as px

from functions.load_data import load_era5_raw, load_elhub_data


# ------------------------------------------------------------
# Sliding window correlation
# ------------------------------------------------------------
def sliding_corr(df, met_var, energy_var, lag_hours, window):
    s1 = df[met_var]
    s2 = df[energy_var].shift(lag_hours)

    corr = s1.rolling(window=window).corr(s2)

    out = pd.DataFrame({
        "time": df["time"],
        "corr": corr
    })
    return out


# ------------------------------------------------------------
# MAIN PAGE
# ------------------------------------------------------------
def show():

    st.title("📈 Sliding Window Correlation – Meteorologi vs Energi")

    st.info("Velg variabler og parametere i sidefeltet for å beregne glidende korrelasjon.")

    # ------------------------------------------------------------
    # 1) Last værdata og energidata
    # ------------------------------------------------------------
    meteo = load_era5_raw(60.39, 5.32, 2021)  # Bergen eksempel – tilpass
    energy = load_elhub_data()

    # Tid til datetime
    meteo["time"] = pd.to_datetime(meteo["time"])
    energy["start_time"] = pd.to_datetime(energy["start_time"])

    # Gjør om til timesnitt per prisområde (tilpass hvis du bruker NO1, NO2 osv.)
    energy_hourly = (
        energy.groupby("start_time")["quantity_kwh"]
        .sum()
        .reset_index()
        .rename(columns={"start_time": "time", "quantity_kwh": "energy_kwh"})
    )

    # Merge vær + energi
    df = pd.merge(meteo, energy_hourly, on="time", how="inner").sort_values("time")

    # ------------------------------------------------------------
    # 2) Sidebar – velg variabler
    # ------------------------------------------------------------
    met_vars = [c for c in meteo.columns if c not in ["time"]]
    energy_vars = ["energy_kwh"]

    st.sidebar.header("🔧 Parametere")

    met_var = st.sidebar.selectbox("Meteorologisk variabel", met_vars)
    energy_var = st.sidebar.selectbox("Energivariabel", energy_vars)

    lag = st.sidebar.slider("Lag (timer)", -72, 72, 0)
    window = st.sidebar.slider("Vindu (timer)", 6, 240, 72, 6)

    # ------------------------------------------------------------
    # 3) Beregn korrelasjon
    # ------------------------------------------------------------
    corr_df = sliding_corr(df, met_var, energy_var, lag, window)

    # ------------------------------------------------------------
    # 4) Plot
    # ------------------------------------------------------------
    st.subheader("📉 Glidende korrelasjon")
    fig = px.line(
        corr_df,
        x="time",
        y="corr",
        labels={"corr": "Korrelasjon", "time": "Tid"},
        title=f"Sliding correlation: {met_var} vs {energy_var}"
    )
    fig.add_hline(y=0, line_dash="dash")
    st.plotly_chart(fig, use_container_width=True)

    # ------------------------------------------------------------
    # 5) Vis råserier
    # ------------------------------------------------------------
    with st.expander("Vis tidsserier for valgte variabler"):
        fig2 = px.line(
            df,
            x="time",
            y=[met_var, energy_var],
            title="Tidsserier",
            labels={"value": "Verdi", "variable": "Serie"}
        )
        st.plotly_chart(fig2, use_container_width=True)
