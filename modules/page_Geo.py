# page_geo.py
import streamlit as st
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
from functions.load_data import load_elhub_data
import pandas as pd
import json
from modules.page_Snow import show as page_Snow


def show():

    # =====================================================================
    # 🏷️ 1) HOVEDTITTEL
    # =====================================================================
    st.title("Analyse av energiproduksjon og -forbruk i norske elspotområder")
    

    # =====================================================================
    # 2) LAST DATA
    # =====================================================================
    df = load_elhub_data()

    if df.empty:
        st.error("Ingen data returnert fra MongoDB.")
        st.stop()

    df["start_time"] = pd.to_datetime(df["start_time"], errors="coerce")
    df = df.dropna(subset=["start_time"])

    # Sikre energy_group finnes
    if "energy_group" not in df.columns:
        df["energy_group"] = df["production_group"]
        df.loc[df["consumption_group"].notna(), "energy_group"] = df["consumption_group"]


    # =====================================================================
    # 🔀 VIEW-KONTROLL (erstatter TABS)
    # =====================================================================
    view = st.radio(
        "Velg visning:",
        ["🗺️ Kartanalyse", "❄️ Snow Drift"],
        horizontal=True
    )



    # =====================================================================
    # 🗺️ VIEW 1 — KART
    # =====================================================================
    if view == "🗺️ Kartanalyse":

        # -----------------------------------------------------------------
        # 3) SIDEBAR FILTERE for kartdelen
        # -----------------------------------------------------------------
        st.sidebar.header("🔧 Filter")

        # --- Datagrunnlag ---
        st.sidebar.markdown("### 🔍 Datagrunnlag")

        src = st.sidebar.radio(
            "Velg type data:",
            [
                "Alt (produksjon + forbruk)",
                "Kun produksjon",
                "Kun forbruk"
            ]
        )

        if src == "Kun produksjon":
            df = df[df["source"] == "production"]
        elif src == "Kun forbruk":
            df = df[df["source"] == "consumption"]

        # --- Energigruppe ---
        st.sidebar.markdown("### ⚡ Energigruppe")
        groups = sorted(df["energy_group"].dropna().unique())

        group_choice = st.sidebar.selectbox(
            "Velg energigruppe:",
            ["Alle grupper"] + list(groups)
        )

        if group_choice != "Alle grupper":
            df = df[df["energy_group"] == group_choice]

        # =====================================================================
        # 4) DATO-SLIDER 
        # =====================================================================
        st.markdown("## 📅 Velg tidsintervall")

        min_date = df["start_time"].min().date()
        max_date = df["start_time"].max().date()

        start_date, end_date = st.slider(
            "Tidsperiode:",
            min_value=min_date,
            max_value=max_date,
            value=(min_date, max_date),
            format="DD.MM.YYYY",
        )

        df = df[df["start_time"].dt.date.between(start_date, end_date)]

        if df.empty:
            st.warning("Ingen data for valgt tidsintervall.")
            st.stop()

        # =====================================================================
        # 5) GEOJSON 
        # =====================================================================
        @st.cache_data
        def load_geojson():
            gdf = gpd.read_file("file.geojson", engine="pyogrio")

            gdf["ElSpotOmr"] = gdf["ElSpotOmr"].astype(str).str.replace(" ", "")
            return gdf.to_crs(4326)

        areas = load_geojson()


        # =====================================================================
        # 6) STATISTIKK
        # =====================================================================
        stats = (
            df.groupby("price_area")["quantity_kwh"]
            .agg(["mean", "count", "min", "max"])
            .rename(columns={
                "mean": "Gjennomsnitt (kWh)",
                "count": "Antall målinger",
                "min": "Laveste (kWh)",
                "max": "Høyeste (kWh)"
            })
        )

        # =====================================================================
        # 7) TABELL – STIL OG EMOJIS
        # =====================================================================
        st.markdown("## 📊 Oversikt over prisområder")

        styled_stats = (
            stats.style
            .background_gradient(cmap="Blues", subset=["Gjennomsnitt (kWh)"])
            .format({
                "Gjennomsnitt (kWh)": "{:,.0f}",
                "Antall målinger": "{:,.0f}",
                "Laveste (kWh)": "{:,.0f}",
                "Høyeste (kWh)": "{:,.0f}",
            })
            .set_properties(**{
                "font-size": "15px",
                "border-color": "black"
            })
        )

        st.dataframe(styled_stats, use_container_width=True)



        # =====================================================================
        # 8) KART
        # =====================================================================
        st.markdown("## 🗺️ Kart over elspotområder")

        areas = areas.merge(stats, how="left", left_on="ElSpotOmr", right_index=True)
        areas["lat"] = areas.geometry.centroid.y
        areas["lon"] = areas.geometry.centroid.x

        # session state
        if "selected_area" not in st.session_state:
            st.session_state.selected_area = None

        selected_area = st.session_state.selected_area

        # selection (fra plotly on_select)
        sel_state = st.session_state.get("map")
        if sel_state and "selection" in sel_state:
            pts = sel_state["selection"].get("points", [])
            if pts:
                chosen = pts[0].get("location")
                if chosen:
                    st.session_state.selected_area = chosen
                    selected_area = chosen

        # zoom
        center = {"lat": 65, "lon": 12}
        zoom = 4
        if selected_area and selected_area in areas["ElSpotOmr"].values:
            geom = areas.loc[areas["ElSpotOmr"] == selected_area, "geometry"].iloc[0]
            minx, miny, maxx, maxy = geom.bounds
            center = {"lat": (miny + maxy) / 2, "lon": (minx + maxx) / 2}
            span = max(maxy - miny, maxx - minx)
            zoom = 6 if span < 5 else 5

        geojson = json.loads(areas.to_json())

        fig = px.choropleth_mapbox(
            areas,
            geojson=geojson,
            locations="ElSpotOmr",
            featureidkey="properties.ElSpotOmr",
            color="Gjennomsnitt (kWh)",
            color_continuous_scale="Viridis",
            mapbox_style="open-street-map",
            zoom=zoom,
            center=center,
            opacity=0.6,
        )

        fig.update_traces(
            hovertemplate=(
                "<b>Prisområde: %{location}</b><br>"
                "Snitt: %{z:,.0f} kWh<br>"
                "<extra></extra>"
            )
        )

        # Usynlige punkter for klikk
        fig.add_trace(go.Scattermapbox(
            lat=areas["lat"],
            lon=areas["lon"],
            mode="markers",
            marker=dict(size=25, opacity=0),
            customdata=areas["ElSpotOmr"],
            hoverinfo="none",
            name="clickpoints"
        ))

        # Highlight valgt område + lagre koordinat til SNOW
        if selected_area and selected_area in areas["ElSpotOmr"].values:
            geom = areas.loc[areas["ElSpotOmr"] == selected_area, "geometry"].iloc[0]
            js = json.loads(gpd.GeoSeries([geom]).to_json())
            c = areas.loc[areas["ElSpotOmr"] == selected_area].iloc[0]

            # 🔴 Marker valgt polygon
            fig.add_trace(go.Choroplethmapbox(
                geojson=js,
                locations=[0],
                z=[1],
                showscale=False,
                marker_line_color="black",
                marker_line_width=5,
                marker_opacity=0
            ))

            # 🔴 Marker valgt centroid
            fig.add_trace(go.Scattermapbox(
                lat=[c["lat"]],
                lon=[c["lon"]],
                mode="markers",
                marker=dict(size=18, color="red"),
                name="Valgt område"
            ))

            # ⭐️ Viktig: lagre koordinat til SNOW-siden
            st.session_state["selected_coord"] = {
                "lat": float(c["lat"]),
                "lon": float(c["lon"]),
            }

        fig.update_layout(height=650, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, key="map", on_select="rerun", use_container_width=True)

        # =====================================================================
        # 9) DETALJER + TIDSSERIE
        # =====================================================================

        st.markdown("---")
        st.subheader("📌 Detaljer for valgt område")

        if selected_area and selected_area in stats.index:

            row = stats.loc[selected_area]

            st.metric(
                label=f"Gjennomsnittlig energimengde i {selected_area}",
                value=f"{row['Gjennomsnitt (kWh)']:,.0f} kWh"
            )

            st.write(f"Antall målinger: **{int(row['Antall målinger'])}**")
            st.write(f"Min–maks: **{row['Laveste (kWh)']:,.0f} – {row['Høyeste (kWh)']:,.0f} kWh**")

            df_ts = df[df["price_area"] == selected_area].copy()

            if not df_ts.empty:
                df_ts_daily = (
                    df_ts.set_index("start_time")["quantity_kwh"]
                    .resample("D").mean()
                    .reset_index()
                )

                fig_ts = px.line(
                    df_ts_daily,
                    x="start_time",
                    y="quantity_kwh",
                    title=f"Daglig gjennomsnittlig energimengde – {selected_area}",
                    labels={"start_time": "Dato", "quantity_kwh": "kWh"},
                )
                fig_ts.update_layout(height=350, margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig_ts, use_container_width=True)
            else:
                st.info("Ingen tidsseriedata for dette området.")

        else:
            st.info("Klikk på et prisområde for å vise detaljer. "
                    "Koordinaten brukes også på SNOW-siden.")
                    

        # =====================================================================
        # 10) INFO-SEKSJONER
        # =====================================================================

        with st.expander("ℹ️ Hva betyr energigruppe?"):
            st.markdown("""
        En *energigruppe* beskriver **typen energi** som produseres eller forbrukes.

        Vanlige grupper:
        - 🔵 **hydro** – vannkraft  
        - 🟢 **wind** – vindkraft  
        - 🟠 **thermal** – varme, gass, biomasse  
        - 🟣 **industry** – energibruk i industri  
        - 🏠 **household** – energibruk i husholdninger  
        - ⚙️ **other** – kategorier som ikke passer i andre grupper
            """)

        with st.expander("ℹ️ Hva er `kWh`?"):
            st.markdown("""
        `quantity_kwh` viser hvor mye energi (kWh) som er **produsert eller brukt i løpet av én time**.
            """)



    # =====================================================================
    # ❄️ VIEW 2 — SNOW DRIFT
    # =====================================================================
    if view == "❄️ Snow Drift":

        st.subheader("❄️ Snow Drift Analysis")

        coord = st.session_state.get("selected_coord")
        if coord is None:
            st.info("Klikk et prisområde i kartet for å bruke snødriftanalysen.")
            st.stop()

        # -----------------------------------------------------------------
        # 🎛️ SNOW-FILTERE — vises KUN HER
        # -----------------------------------------------------------------
        st.sidebar.header("❄️ Snødrift-parametere")

        year_start = st.sidebar.number_input(
            "Start hydrologisk år",
            min_value=2000,
            max_value=2030,
            value=2019,
            step=1
        )

        year_end = st.sidebar.number_input(
            "Slutt hydrologisk år",
            min_value=2000,
            max_value=2030,
            value=2023,
            step=1
        )

        if year_start > year_end:
            st.sidebar.error("Startår kan ikke være større enn sluttår.")
            st.stop()

        T = st.sidebar.slider(
            "T – maksimal transportdistanse [m]",
            min_value=500.0, max_value=5000.0,
            value=3000.0, step=250.0
        )

        F = st.sidebar.slider(
            "F – fetch distance [m]",
            min_value=5000.0, max_value=50000.0,
            value=30000.0, step=2500.0
        )

        theta = st.sidebar.slider(
            "θ – relokaliseringskoeffisient",
            min_value=0.1, max_value=1.0,
            value=0.5, step=0.05
        )

        # Lagre filtrene
        st.session_state.snow_filters = {
            "year_start": year_start,
            "year_end": year_end,
            "T": T,
            "F": F,
            "theta": theta,
        }

        # -----------------------------------------------------------------
        # Start selve snø-driftsiden
        # -----------------------------------------------------------------
        page_Snow()
