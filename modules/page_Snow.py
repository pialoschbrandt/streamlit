# page_snow.py – forbedret versjon
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import streamlit as st
from datetime import datetime


# =====================================================================
# 📌 Helper-funksjoner
# =====================================================================

def compute_Qupot(hourly_wind_speeds, dt=3600):
    return sum((u ** 3.8) * dt for u in hourly_wind_speeds) / 233847


def compute_snow_transport(T, F, theta, Swe, hourly_wind_speeds, dt=3600):
    Qupot = compute_Qupot(hourly_wind_speeds, dt)
    Qspot = 0.5 * T * Swe
    Srwe = theta * Swe

    if Qspot < Qupot:
        Qinf = Qspot
        control = "Snowfall-controlled"
    else:
        Qinf = Qupot
        control = "Wind-controlled"

    Qt = Qinf * (1 - 0.14 ** (F / T))

    return {
        "Qupot (kg/m)": Qupot,
        "Qspot (kg/m)": Qspot,
        "Srwe (mm)": Srwe,
        "Qinf (kg/m)": Qinf,
        "Qt (kg/m)": Qt,
        "Control": control,
    }


def sector_index(direction):
    return int(((direction + 11.25) % 360) // 22.5)


def compute_sector_transport(ws, wd, dt=3600):
    sectors = [0.0] * 16
    for u, d in zip(ws, wd):
        sectors[sector_index(d)] += (u ** 3.8) * dt / 233847
    return sectors


@st.cache_data(show_spinner=True)
def fetch_openmeteo_hourly(lat, lon, start, end):
    url = "https://archive-api.open-meteo.com/v1/era5"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d"),
        "hourly": "temperature_2m,precipitation,wind_speed_10m,wind_direction_10m",
        "timezone": "Europe/Oslo",
    }

    try:
        r = requests.get(url, params=params, timeout=30)
        if r.status_code != 200:
            return pd.DataFrame()
        data = r.json()
    except:
        return pd.DataFrame()

    if "hourly" not in data:
        return pd.DataFrame()

    df = pd.DataFrame(data["hourly"])
    df["time"] = pd.to_datetime(df["time"])
    return df


@st.cache_data(show_spinner=False)
def compute_snow_drift_for_hydro_year(lat, lon, hydro_year, T, F, theta):

    start = datetime(hydro_year, 7, 1)
    end = datetime(hydro_year + 1, 6, 30, 23)

    df = fetch_openmeteo_hourly(lat, lon, start, end)
    if df.empty:
        return df, {}

    df["Swe_hourly"] = np.where(df["temperature_2m"] < 1, df["precipitation"], 0)
    Swe_total = df["Swe_hourly"].sum()
    ws = df["wind_speed_10m"].to_numpy()

    result = compute_snow_transport(T, F, theta, Swe_total, ws)
    result["hydro_year"] = hydro_year

    return df, result


def compute_monthly_snow_drift(df, hydro_year, T, F, theta):

    df = df.copy()
    df["month_start"] = df["time"].dt.to_period("M").dt.to_timestamp()

    rows = []
    for month, group in df.groupby("month_start"):
        Swe_m = group["Swe_hourly"].sum()
        ws_m = group["wind_speed_10m"].to_numpy()
        res = compute_snow_transport(T, F, theta, Swe_m, ws_m)
        res["hydro_year"] = hydro_year
        res["month_start"] = month
        rows.append(res)

    return pd.DataFrame(rows)


def aggregate_snow_drift(lat, lon, year_start, year_end, T, F, theta):

    yearly, monthly, hourly = [], [], []

    for y in range(year_start, year_end + 1):
        df_y, res_y = compute_snow_drift_for_hydro_year(lat, lon, y, T, F, theta)

        if df_y.empty:
            continue

        hourly.append(df_y)
        yearly.append(res_y)
        monthly.append(compute_monthly_snow_drift(df_y, y, T, F, theta))

    if not yearly:
        return pd.DataFrame(), pd.DataFrame(), []

    return (
        pd.DataFrame(yearly),
        pd.concat(monthly, ignore_index=True),
        hourly,
    )


def build_wind_rose(dfs):
    if not dfs:
        return None

    sec_vals = []
    for df in dfs:
        ws = df["wind_speed_10m"].to_numpy()
        wd = df["wind_direction_10m"].to_numpy()
        sec_vals.append(compute_sector_transport(ws, wd))

    avg = np.mean(sec_vals, axis=0)

    labels = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
              "S","SSW","SW","WSW","W","WNW","NW","NNW"]

    df = pd.DataFrame({"direction": labels, "Qt_tonnes_per_m": avg / 1000})

    fig = px.bar_polar(
        df,
        r="Qt_tonnes_per_m",
        theta="direction",
        color="Qt_tonnes_per_m",
        title="Wind Rose – Mean Snow Transport per Direction (tonnes/m)",
        color_continuous_scale="Viridis"
    )
    return fig


# =====================================================================
# 🖥️ HOVEDFUNKSJON: show()
# =====================================================================

def show():

    st.header("❄️ Snow Drift & Wind Rose Analysis")
    st.caption("Beregning basert på ERA5-data og en forenklet Tabler-modell (2003).")

    # ---- Hent koordinat fra kart ----
    coord = st.session_state.get("selected_coord")
    if coord is None:
        st.warning("Velg et område i kartet før du starter snødriftanalysen.")
        st.stop()

    lat, lon = coord["lat"], coord["lon"]
    st.info(f"**Valgt koordinat** → Lat: `{lat:.4f}`, Lon: `{lon:.4f}`")

    # ---- Hent filtre fra page_geo ----
    filters = st.session_state.get("snow_filters")
    if filters is None:
        st.error("Snødrift-parametere er ikke satt i sidemenyen.")
        st.stop()

    year_start = filters["year_start"]
    year_end = filters["year_end"]
    T = filters["T"]
    F = filters["F"]
    theta = filters["theta"]

    # =====================================================================
    # 🔄 Beregning
    # =====================================================================

    with st.spinner("Henter ERA5-data og beregner snødrift ..."):
        yearly, monthly, hourly = aggregate_snow_drift(lat, lon, year_start, year_end, T, F, theta)

    if yearly.empty:
        st.error("Ingen snødriftdata tilgjengelig for valgt periode.")
        st.stop()

    st.subheader("📊 Årlig og månedlig snøtransport")
    st.caption("Qt [kg/m] beregnet for hver hydrologiske periode.")

    # ---- Plot kombinasjon ----
    fig = make_subplots(
        rows=2, cols=1,
        vertical_spacing=0.12,
        subplot_titles=["Årlig snøtransport (Qt)", "Månedlig snøtransport (Qt)"]
    )

    fig.add_bar(x=yearly["hydro_year"], y=yearly["Qt (kg/m)"],
                name="Årlig Qt", row=1, col=1)

    fig.add_bar(x=monthly["month_start"], y=monthly["Qt (kg/m)"],
                name="Månedlig Qt", row=2, col=1)

    fig.update_layout(height=700, hovermode="x unified", margin=dict(l=0, r=0, t=60, b=0))
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        yearly[["hydro_year","Qupot (kg/m)","Qspot (kg/m)","Qinf (kg/m)","Qt (kg/m)","Control"]],
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # =====================================================================
    # 🌬️ Wind Rose
    # =====================================================================

    st.subheader("🌬️ Vindrose – Snøtransport per retning")
    st.caption("Basert på u³·⁸-modellen og 16-sektors kompassinndeling.")

    fig_rose = build_wind_rose(hourly)
    if fig_rose:
        st.plotly_chart(fig_rose, use_container_width=True)
    else:
        st.info("Ikke nok vinddata for å generere vindrose.")

    # =====================================================================
    # ℹ️ Informasjonsseksjon
    # =====================================================================

    with st.expander("ℹ️ Hva viser denne siden?"):
        st.markdown("""
### 🔍 Introduksjon
Denne siden beregner **snødrift (Qt)** og vindstyrt snøtransport basert på:
- Historiske værdata fra **ERA5 / Open-Meteo**
- En forenklet versjon av **Tabler-modellen (2003)**  
- Hydrologiske år: **1. juli – 30. juni**

### 📘 Kort forklaring
- **Qt** → total snøtransport (kg/m)  
- **Qupot** → potensiell vindstyrt snøtransport  
- **Qspot** → begrensning basert på nytt snøfall  
- **Qinf** → faktisk styrende transport (vind eller snøfall)  
- **Srwe** → omfordelt snø (mm)

### 🌬️ Vindrose
Viser hvordan snøtransport fordeler seg mellom 16 vindretninger (N, NNE, NE, ...).

### 📍 Koordinat
Koordinaten kommer fra kartet i *Geo*-fanen.
        """)

