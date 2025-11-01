import streamlit as st
import pandas as pd

def show(df=None):
    st.header("Tabell med rådata")

    # Hvis df ikke ble sendt fra main.py, last data lokalt
    if df is None:
        @st.cache_data
        def load_data():
            return pd.read_csv("open-meteo-subset.csv")

        df = load_data()
        df["time"] = pd.to_datetime(df["time"])
        df["month"] = df["time"].dt.month

    # Viser første 100 rader
    st.dataframe(df.head(100))

    # --------------------------------------------------------
    # Mini-linecharts for januar
    # --------------------------------------------------------
    st.header("Tabell med mini-linecharts")

    # Filtrer januar
    df_jan = df[df["month"] == 1]

    # Velg variabler
    variables = [
        "temperature_2m (°C)",
        "precipitation (mm)",
        "wind_speed_10m (m/s)",
        "wind_gusts_10m (m/s)",
        "wind_direction_10m (°)"
    ]

    # Bygg et nytt dataframe: én rad per variabel
    df_spark = pd.DataFrame({
        "Variabel": variables,
        "Trend": [df_jan[v].tolist() for v in variables]
    })

    # Vis som tabell med mini-linjediagrammer
    st.dataframe(
        df_spark,
        column_config={
            "Trend": st.column_config.LineChartColumn(
                "Trend (Januar)",
                y_min=df_spark["Trend"].apply(min).min(),
                y_max=df_spark["Trend"].apply(max).max()
            )
        },
        hide_index=True,
    )
