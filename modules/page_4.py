import streamlit as st
import pandas as pd
import plotly.express as px

# IMPORTER RIKTIG FUNKSJON FRA load_data.py
from functions.load_data import load_era5_raw


# -----------------------------
# Funksjon: vis side
# -----------------------------
def show(df=None):
    st.header("Meteorologiske data – Open-Meteo ERA5")

    # ---------------------------------------------------
    # 1. Hent valgt område fra side 2
    # ---------------------------------------------------
    selected_area = st.session_state.get("selected_area")
    if not selected_area:
        st.warning("⚠️ Du må først velge et prisområde på side 2 (Elhub-data).")
        st.stop()

    st.write(f"📍 Valgt prisområde: **{selected_area}**")
    year = 2021

    # ---------------------------------------------------
    # 2. Definer koordinater for prisområdene
    # ---------------------------------------------------
    data = {
        "price_area": ["NO1", "NO2", "NO3", "NO4", "NO5"],
        "city": ["Oslo", "Kristiansand", "Trondheim", "Tromsø", "Bergen"],
        "latitude": [59.9139, 58.1467, 63.4305, 69.6492, 60.3929],
        "longitude": [10.7522, 7.9956, 10.3951, 18.9560, 5.3240],
    }
    cities_df = pd.DataFrame(data)

    row = cities_df[cities_df["price_area"] == selected_area].iloc[0]
    lat, lon = row["latitude"], row["longitude"]
    city = row["city"]

    st.write(f"Henter data for **{city} ({lat:.2f}, {lon:.2f})** for året **{year}** ...")

    # ---------------------------------------------------
    # 3. Hent data fra API (cachet)
    # ---------------------------------------------------
    @st.cache_data(show_spinner="Henter værdata fra Open-Meteo ...")
    def load_weather(lat, lon, year):
        return load_era5_raw(lat, lon, year)

    df = load_weather(lat, lon, year)

    # ---------------------------------------------------
    # 4. Forbered data
    # ---------------------------------------------------
    line_chart_data = df.copy()

    line_chart_data["time"] = pd.to_datetime(line_chart_data["time"], errors="coerce")
    line_chart_data = line_chart_data[line_chart_data["time"].dt.year == year]
    line_chart_data = line_chart_data.dropna(subset=["time"])

    line_chart_data["month"] = line_chart_data["time"].dt.month
    line_chart_data["day"] = line_chart_data["time"].dt.day

    variables = [c for c in line_chart_data.columns if c not in ["time", "month", "day"]]

    # ---------------------------------------------------
    # 5. UI–valg
    # ---------------------------------------------------
    pick_a_variable = st.selectbox(
        "Velg en variabel eller 'Alle variabler':",
        ["Alle variabler"] + variables
    )

    months = sorted(line_chart_data["month"].unique())
    pick_month_range = st.select_slider(
        "Velg et månedsspenn (kun 2021):",
        options=months,
        value=(months[0], months[-1])
    )

    df_plot = line_chart_data[
        (line_chart_data["month"] >= pick_month_range[0]) &
        (line_chart_data["month"] <= pick_month_range[1])
    ]

    # ---------------------------------------------------
    # 6. Plot
    # ---------------------------------------------------
    if pick_a_variable == "Alle variabler":
        fig = px.line(
            df_plot,
            x="time",
            y=variables,
            title=f"Alle variabler i {city} ({selected_area}) – måneder {pick_month_range[0]}–{pick_month_range[1]} i 2021"
        )
    else:
        fig = px.line(
            df_plot,
            x="time",
            y=pick_a_variable,
            title=f"{pick_a_variable} i {city} ({selected_area}) – måneder {pick_month_range[0]}–{pick_month_range[1]} i 2021"
        )

    fig.update_layout(
        xaxis_title="Tid",
        yaxis_title="Verdi",
        legend_title="Variabler",
        template="plotly_white"
    )

    st.plotly_chart(fig, use_container_width=True)

    # ---------------------------------------------------
    # 8. Rådata
    # ---------------------------------------------------
    with st.expander("Vis rådata"):
        st.dataframe(df.head(50))
