import streamlit as st
import pandas as pd
import requests


# ------------------------------------------------------------
# Hjelpefunksjon – hent eller bruk eksisterende Open-Meteo-data
# ------------------------------------------------------------
@st.cache_data(show_spinner="Henter værdata fra Open-Meteo API ...")
def hent_era5_data(latitude, longitude, year):
    """Henter timesoppløste værdata fra Open-Meteo ERA5 API."""
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"

    url = (
        "https://archive-api.open-meteo.com/v1/era5?"
        f"latitude={latitude}&longitude={longitude}&"
        f"start_date={start_date}&end_date={end_date}&"
        "hourly=temperature_2m,precipitation,wind_speed_10m,"
        "wind_gusts_10m,wind_direction_10m&timezone=auto"
    )

    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    df = pd.DataFrame(data["hourly"])
    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    return df


# ------------------------------------------------------------
# Funksjon som kan brukes både her og fra andre sider
# ------------------------------------------------------------
def get_or_load_meteo_data(year=2021):
    """Hent Open-Meteo-data fra session_state eller fra API ved behov."""
    selected_area = st.session_state.get("selected_area")

    if not selected_area:
        st.warning("⚠️ Du må først velge et prisområde på side 2 (Elhub-data).")
        st.stop()

    # 📍 Definer koordinater for prisområdene
    data = {
        "price_area": ["NO1", "NO2", "NO3", "NO4", "NO5"],
        "city": ["Oslo", "Kristiansand", "Trondheim", "Tromsø", "Bergen"],
        "latitude": [59.9139, 58.1467, 63.4305, 69.6492, 60.3929],
        "longitude": [10.7522, 7.9956, 10.3951, 18.9560, 5.3240],
    }
    cities_df = pd.DataFrame(data)
    row = cities_df[cities_df["price_area"] == selected_area].iloc[0]
    lat, lon, city = row["latitude"], row["longitude"], row["city"]

    # 🔹 Hvis data allerede finnes, gjenbruk dem
    if "meteo_df" in st.session_state:
        st.info(f"♻️ Bruker lagrede værdata for {city} ({selected_area}) fra session_state.")
        return st.session_state["meteo_df"], selected_area

    # 🔹 Ellers: hent fra API
    df = hent_era5_data(lat, lon, year)
    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    df = df[df["time"].dt.year == year].dropna(subset=["time"])

    # Legg til hjelpekolonner
    df["month"] = df["time"].dt.month
    df["day"] = df["time"].dt.day

    # Lagre i session_state for gjenbruk
    st.session_state["meteo_df"] = df
    st.session_state["selected_area"] = selected_area

    st.success(f"✅ Data for {city} ({selected_area}, {year}) hentet og lagret.")
    return df, selected_area


# ------------------------------------------------------------
# Hovedvisning av side 5
# ------------------------------------------------------------
def show(df=None):
    st.header("Open-Meteo ERA5 – Meteorologiske data")

    # 1️⃣ Hent data (fra session_state eller API)
    df, selected_area = get_or_load_meteo_data(2021)

    # 2️⃣ Vis kontekst
    st.write(f"📍 Prisområde: **{selected_area}** – viser data for året **2021**")

    # 3️⃣ Rådata-visning
    st.subheader("Første 100 rader")
    st.dataframe(df.head(100))

    # 4️⃣ Mini-linjediagrammer for januar
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
                    y_min=df_spark["Trend"].apply(lambda x: min(x) if len(x) else 0).min(),
                    y_max=df_spark["Trend"].apply(lambda x: max(x) if len(x) else 0).max(),
                )
            },
            hide_index=True,
        )
    else:
        st.info("Ingen numeriske variabler funnet i datasettet.")

    # 5️⃣ Informasjon nederst
    with st.expander("ℹ️ Om dataene"):
        st.markdown(
            """
            Dataene er hentet fra **Open-Meteo ERA5** og viser timesoppløste værdata
            (temperatur, nedbør, vindhastighet osv.) for valgt prisområde i **2021**.
            """
        )
