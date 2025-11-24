import streamlit as st
import pandas as pd
import plotly.express as px
from functions.load_data import load_elhub_data   # henter data samlet og ferdig renset


def show():

    st.header("Elhub-data – Produksjon")

    # ------------------------
    # 1. HENT DATA VIA data_loader
    # ------------------------
    df_ready = load_elhub_data()

    if df_ready.empty:
        st.error("Ingen data tilgjengelig fra load_elhub_data().")
        st.stop()

    # ------------------------
    # 2. FILTER KUN PRODUKSJON
    # ------------------------
    df_ready = df_ready[df_ready["source"] == "production"]

    if df_ready.empty:
        st.warning("Ingen produksjonsdata funnet i datasettet.")
        st.stop()

    # ------------------------
    # 3. MAPPE gamle kolonnenavn slik diagrammene forventer
    # ------------------------
    mapping = {
        "price_area": "priceArea",
        "production_group": "productionGroup",
        "quantity_kwh": "quantityKwh",
    }

    for old, new in mapping.items():
        if old in df_ready.columns and new not in df_ready.columns:
            df_ready[new] = df_ready[old]

    # Legg inn år og måned
    df_ready["year"] = df_ready["start_time"].dt.year
    df_ready["month"] = df_ready["start_time"].dt.to_period("M").astype(str)

    # ------------------------
    # 4. VISUALISERING
    # ------------------------
    st.title("Analyse av produksjonsdata")
    col1, col2 = st.columns(2)

    # -----------------------------------------------------------
    # VENSTRE KOLONNE – PIE CHART
    # -----------------------------------------------------------
    with col1:
        st.subheader("Prisområder og fordeling")

        price_areas = sorted(df_ready["priceArea"].dropna().unique())

        st.session_state["selected_area"] = st.radio("Velg prisområde:", price_areas)
        selected_area = st.session_state["selected_area"]

        area_data = df_ready[df_ready["priceArea"] == selected_area]

        if area_data.empty:
            st.info("Ingen data for valgt prisområde.")
        else:
            fig_pie = px.pie(
                area_data,
                names="productionGroup",
                values="quantityKwh",
                title=f"Fordeling av produksjon i {selected_area}",
                hole=0.4,
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    # -----------------------------------------------------------
    # HØYRE KOLONNE – LINE CHART
    # -----------------------------------------------------------
    with col2:
        st.subheader("Produksjon over tid")

        required = {"priceArea", "productionGroup", "quantityKwh", "start_time", "month", "year"}
        missing = required - set(df_ready.columns)
        if missing:
            st.error(f"Mangler kolonner i data: {sorted(missing)}")
            st.stop()

        # produksjonsgrupper
        prod_groups = sorted(df_ready["productionGroup"].dropna().unique())
        selected_groups = st.multiselect(
            "Velg produksjonsgrupper:",
            options=prod_groups,
            default=prod_groups[:2] if len(prod_groups) >= 2 else prod_groups,
        )

        if not selected_groups:
            st.info("Velg minst én produksjonsgruppe.")
            st.stop()

        # ---------------------------------------------------------
        # ⭐ FILTRER ÅR: KUN 2021–2024
        # ---------------------------------------------------------
        valid_df = df_ready[df_ready["year"].between(2021, 2024)]
        years_all = sorted(valid_df["year"].unique())

        if not years_all:
            st.error("Datasettet inneholder ingen år mellom 2021 og 2024.")
            st.stop()

        selected_year = st.selectbox("Velg år:", years_all)

        # ---------------------------------------------------------
        # ⭐ FILTRER MÅNEDER FOR VALGT ÅR
        # ---------------------------------------------------------
        df_year = valid_df[valid_df["year"] == selected_year]

        months_for_year = sorted(df_year["month"].unique())
        selected_month = st.selectbox("Velg måned:", months_for_year)

        # ---------------------------------------------------------
        # ⭐ KOMBINERT FILTERING
        # ---------------------------------------------------------
        filtered = valid_df[
            (valid_df["priceArea"] == selected_area)
            & (valid_df["productionGroup"].isin(selected_groups))
            & (valid_df["year"] == selected_year)
            & (valid_df["month"] == selected_month)
        ].copy()

        if filtered.empty:
            st.info("Ingen data for valgt kombinasjon.")
        else:
            filtered = filtered.sort_values("start_time")

            fig_line = px.line(
                filtered,
                x="start_time",
                y="quantityKwh",
                color="productionGroup",
                title=f"Produksjon i {selected_area} – {selected_month}",
                labels={
                    "start_time": "Tid",
                    "quantityKwh": "Produksjon (kWh)",
                    "productionGroup": "Produksjonsgruppe",
                },
            )
            fig_line.update_layout(legend_title_text="Produksjonsgrupper")
            st.plotly_chart(fig_line, use_container_width=True)
