import streamlit as st
import pandas as pd
import plotly.express as px

def show(df=None):
    st.header("Plot av data")

    # ---------------------------------------------------
    # Last inn data hvis den ikke ble sendt fra main.py
    # ---------------------------------------------------
    if df is None:
        @st.cache_data
        def load_data():
            df_local = pd.read_csv("open-meteo-subset.csv")
            df_local["time"] = pd.to_datetime(df_local["time"])
            df_local["month"] = df_local["time"].dt.month
            return df_local

        df = load_data()

    # ---------------------------------------------------
    # Rensing og forberedelse av data
    # ---------------------------------------------------
    line_chart_data = df.copy()
    line_chart_data["time"] = pd.to_datetime(line_chart_data["time"])
    line_chart_data["day"] = line_chart_data["time"].dt.day

    # Finn alle variabler unntatt tid, dag og måned
    variables = [c for c in line_chart_data.columns if c not in ["time", "month", "day"]]

    # ---------------------------------------------------
    # Velg hva som skal plottes
    # ---------------------------------------------------
    pick_a_variable = st.selectbox(
        "Velg en variabel eller 'Alle variabler':",
        ["Alle variabler"] + variables
    )

    # Velg måneder (fra min til maks)
    months = sorted(line_chart_data["month"].unique())
    pick_month_range = st.select_slider(
        "Velg et månedsspenn:",
        options=months,
        value=(months[0], months[-1])  # standard = hele året
    )

    # Filtrer data på valgt månedsspenn
    df_plot = line_chart_data[
        (line_chart_data["month"] >= pick_month_range[0]) &
        (line_chart_data["month"] <= pick_month_range[1])
    ]

    # ---------------------------------------------------
    # Lag plot
    # ---------------------------------------------------
    if pick_a_variable == "Alle variabler":
        fig = px.line(
            df_plot,
            x="time",
            y=variables,
            title=f"Alle variabler fra måned {pick_month_range[0]} til {pick_month_range[1]}"
        )
    else:
        fig = px.line(
            df_plot,
            x="time",
            y=pick_a_variable,
            title=f"{pick_a_variable} fra måned {pick_month_range[0]} til {pick_month_range[1]}"
        )

    fig.update_layout(
        xaxis_title="Tid",
        yaxis_title="Verdi",
        legend_title="Variabler",
        template="plotly_white"
    )

    # ---------------------------------------------------
    # Vis plottet
    # ---------------------------------------------------
    st.plotly_chart(fig, use_container_width=True)
