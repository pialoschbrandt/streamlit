import streamlit as st
import pandas as pd
import plotly.express as px
from functions.load_data import load_elhub_data


def show():

    st.header("Elhub-data – Produksjon")

    # ------------------------
    # 1. VELG ÅR
    # ------------------------
    year_selected = st.selectbox("Velg år:", [2021, 2022, 2023, 2024], index=0)

    # ------------------------
    # 2. LAST DATA (kun én spinner)
    # ------------------------
    with st.spinner("📂 Leser Elhub-data"):
        df_ready = load_elhub_data()   # <-- RIKTIG FUNKSJON

    if df_ready.empty:
        st.error("Ingen data tilgjengelig.")
        st.stop()

    # ------------------------
    # 3. FILTER PÅ PRODUKSJON
    # ------------------------
    df_prod = df_ready[df_ready["source"] == "production"]

    if df_prod.empty:
        st.warning("Ingen produksjonsdata tilgjengelig.")
        st.stop()

    # ------------------------
    # 4. FILTER ÅR
    # ------------------------
    df_year = df_prod[df_prod["year"] == year_selected]

    if df_year.empty:
        st.warning(f"Ingen data funnet for år {year_selected}.")
        st.stop()

    # ------------------------
    # 5. VELG PRISOMRÅDE
    # ------------------------
    price_areas = sorted(df_year["price_area"].dropna().unique())
    selected_area = st.radio("Velg prisområde:", price_areas)

    df_area = df_year[df_year["price_area"] == selected_area]

    # ------------------------
    # 6. PIE CHART
    # ------------------------
    st.subheader(f"Fordeling av produksjon – {selected_area} – {year_selected}")

    fig_pie = px.pie(
        df_area,
        names="production_group",
        values="quantity_kwh",
        hole=0.4,
        title="Produksjonsfordeling",
    )

    st.plotly_chart(fig_pie, use_container_width=True)

    # ------------------------
    # 7. LINE CHART – PRODUKSJON OVER TID
    # ------------------------
    st.subheader("Produksjon over tid")

    prod_groups = sorted(df_area["production_group"].dropna().unique())

    selected_groups = st.multiselect(
        "Velg produksjonsgrupper:",
        prod_groups,
        default=prod_groups[:2],
    )

    df_plot = df_area[df_area["production_group"].isin(selected_groups)]
    df_plot = df_plot.sort_values("start_time")

    fig_line = px.line(
        df_plot,
        x="start_time",
        y="quantity_kwh",
        color="production_group",
        labels={
            "start_time": "Tid",
            "quantity_kwh": "Produksjon (kWh)",
        },
        title=f"Produksjon i {selected_area}, {year_selected}",
    )

    st.plotly_chart(fig_line, use_container_width=True)
