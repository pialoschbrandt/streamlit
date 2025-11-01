import streamlit as st
import pandas as pd
import pymongo
import plotly.express as px

def show():
    st.header("Elhub-data fra MongoDB")

    # ------------------------
    # INITIALISER TILKOBLING
    # ------------------------
    @st.cache_resource
    def init_connection():
        uri = (
            f"mongodb+srv://{st.secrets['mongo']['user']}:"
            f"{st.secrets['mongo']['password']}@"
            f"{st.secrets['mongo']['cluster']}/?retryWrites=true&w=majority"
        )
        return pymongo.MongoClient(uri)

    client = init_connection()

    try:
        client.admin.command("ping")
        st.success("Tilkobling til MongoDB fungerer.")
    except Exception as e:
        st.error(f"Klarte ikke koble til MongoDB: {e}")
        st.stop()

    # ------------------------
    # HENT DATA FRA MONGODB
    # ------------------------
    @st.cache_data(ttl=600)
    def get_data():
        db = client[st.secrets["mongo"]["database"]]
        collection = db[st.secrets["mongo"]["collection"]]
        return list(collection.find())

    items = get_data()
    if not items:
        st.warning("Ingen data hentet — samlingen er kanskje tom.")
        st.stop()

    # ------------------------
    # KLARGJØR DATA FOR PLOTTING
    # ------------------------
    df_ready = pd.DataFrame(items)

    if df_ready["startTime"].apply(lambda x: isinstance(x, dict)).any():
        df_ready["startTime"] = df_ready["startTime"].apply(
            lambda x: x.get("$date") if isinstance(x, dict) else x
        )

    df_ready["startTime"] = pd.to_datetime(df_ready["startTime"], errors="coerce", utc=True)
    df_ready["startTime"] = df_ready["startTime"].dt.tz_convert(None)
    df_ready["month"] = df_ready["startTime"].dt.to_period("M").astype(str)

    # ------------------------
    # VISUALISERINGER
    # ------------------------
    st.title("Analyse av produksjonsdata")
    col1, col2 = st.columns(2)

    # Venstre kolonne – kakediagram
    with col1:
        st.subheader("Prisområder og fordeling")
        price_areas = sorted(df_ready["priceArea"].dropna().unique())
        selected_area = st.radio("Velg prisområde:", price_areas)

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

    # Høyre kolonne – linjediagram
    with col2:
        st.subheader("Produksjon over tid")

        required = {"priceArea", "productionGroup", "quantityKwh", "startTime", "month"}
        missing = required - set(df_ready.columns)
        if missing:
            st.error(f"Mangler kolonner i data: {sorted(missing)}")
            st.stop()

        prod_groups_all = sorted(df_ready["productionGroup"].dropna().unique().tolist())
        months_all = sorted(df_ready["month"].dropna().unique().tolist())

        selected_groups = st.multiselect(
            "Velg produksjonsgrupper:",
            options=prod_groups_all,
            default=prod_groups_all[:2] if len(prod_groups_all) >= 2 else prod_groups_all,
        )
        if not selected_groups:
            st.info("Velg minst én produksjonsgruppe for å vise graf.")
            st.stop()

        selected_month = st.selectbox("Velg måned:", months_all, index=0)

        filtered = df_ready[
            (df_ready["priceArea"] == selected_area)
            & (df_ready["productionGroup"].isin(selected_groups))
            & (df_ready["month"] == selected_month)
        ].copy()

        if filtered.empty:
            st.info("Ingen data for valgt kombinasjon.")
        else:
            filtered = filtered.sort_values("startTime")
            fig_line = px.line(
                filtered,
                x="startTime",
                y="quantityKwh",
                color="productionGroup",
                title=f"Produksjon i {selected_area} – {selected_month}",
                labels={
                    "startTime": "Tid",
                    "quantityKwh": "Produksjon (kWh)",
                    "productionGroup": "Produksjonsgruppe",
                },
            )
            fig_line.update_layout(legend_title_text="Produksjonsgrupper")
            st.plotly_chart(fig_line, use_container_width=True)

    # Dokumentasjon nederst
    with st.expander("Datakilde"):
        st.markdown(
            """
            Dataene på denne siden hentes fra **MongoDB**-databasen `elhub_data`,
            samlingen `production_per_group_hour`.
            Hver rad representerer én times produksjon for et gitt prisområde og produksjonsgruppe.
            Kilde: **Elhub / Statnett**.
            """
        )
