import streamlit as st
import pandas as pd
from functions.load_data import load_era5_raw  


# ------------------------------------------------------------
# Funksjon: hent eller bruk allerede lagrede værdata
# ------------------------------------------------------------
@st.cache_data(show_spinner="Henter værdata fra Open-Meteo API ...")
def load_weather(latitude, longitude, year):
    """Cache-wrapper rundt load_era5_raw (fra functions/load_data.py)."""
    df = load_era5_raw(latitude, longitude, year)
    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    df = df[df["time"].dt.year == year].dropna(subset=["time"])

    # Legg til hjelpekolonner
    df["month"] = df["time"].dt.month
    df["day"] = df["time"].dt.day
    return df


# ------------------------------------------------------------
# Fellesfunksjon brukt av denne og andre sider
# ------------------------------------------------------------
def get_or_load_meteo_data(year=2021):
    """
    Henter Open-Meteo-data enten fra session_state (hvis lagret)
    eller fra API via load_weather().
    """
    selected_area = st.session_state.get("selected_area")
    if not selected_area:
        st.warning("⚠️ Du må først velge et prisområde på side 2 (Elhub-data).")
        st.stop()

    # 📍 Koordinater for prisområdene
    data = {
        "price_area": ["NO1", "NO2", "NO3", "NO4", "NO5"],
        "city": ["Oslo", "Kristiansand", "Trondheim", "Tromsø", "Bergen"],
        "latitude": [59.9139, 58.1467, 63.4305, 69.6492, 60.3929],
        "longitude": [10.7522, 7.9956, 10.3951, 18.9560, 5.3240],
    }
    cities_df = pd.DataFrame(data)
    row = cities_df[cities_df["price_area"] == selected_area].iloc[0]
    lat, lon, city = row["latitude"], row["longitude"], row["city"]

    # 🔹 Bruk eksisterende data hvis tilgjengelig
    if "meteo_df" in st.session_state:
        st.info(f"♻️ Bruker lagrede værdata for {city} ({selected_area}).")
        return st.session_state["meteo_df"], selected_area

    # 🔹 Ellers hent via load_weather()
    df = load_weather(lat, lon, year)

    st.session_state["meteo_df"] = df
    st.success(f"✅ Hentet og lagret værdata for {city} ({selected_area}) – {year}.")
    return df, selected_area


# ------------------------------------------------------------
# HOVEDSide
# ------------------------------------------------------------
def show(df=None):
    st.header("Open-Meteo ERA5 – Meteorologiske data")

    # 🔹 1. Last data (fra session_state eller via API)
    df, selected_area = get_or_load_meteo_data(2021)

    st.write(f"📍 Prisområde: **{selected_area}** – viser data for året **2021**")

    # 🔹 2. Vis rådata
    st.subheader("Første 100 rader")
    st.dataframe(df.head(100))

    # 🔹 3. Mini-linjediagrammer for januar
    st.subheader("Mini-linjediagrammer for januar")
    df_jan = df[df["month"] == 1]

    variables = [c for c in df_jan.columns if c not in ["time", "month", "day"]]

    if variables:
        df_spark = pd.DataFrame({
            "Variabel": variables,
            "Trend": [df_jan[v].tolist() for v in variables]
        })

        st.dataframe(
            df_spark,
            column_config={
                "Trend": st.column_config.LineChartColumn(
                    "Trend (Januar)",
                    y_min=min(map(min, df_spark["Trend"])),
                    y_max=max(map(max, df_spark["Trend"])),
                )
            },
            hide_index=True
        )
    else:
        st.info("Ingen numeriske variabler funnet i datasettet.")

    # 🔹 4. Info nederst
    with st.expander("ℹ️ Om dataene"):
        st.markdown(
            """
            Dataene er hentet fra **Open-Meteo ERA5** og viser timesoppløste
            værdata for valgt prisområde (temperatur, nedbør, vind, snø osv.)
            for året **2021**.
            """
        )
