from xmlrpc import client
import streamlit as st
import plotly.express as px
import requests
import pandas as pd
from pymongo import MongoClient
from urllib.parse import quote_plus
import pymongo
import plotly.express as px

# Hent data fra MongoDB
def get_data(col):
    try:
        docs = list(col.find().limit(10))
        if docs:
            df = pd.DataFrame(docs)
            return df
        else:
            st.info("Ingen dokumenter funnet i samlingen.")
    except Exception as e:
        st.error(f"Feil ved henting av data: {e}")

# Navigasjon i sidebar
st.sidebar.title("Navigasjon")
page = st.sidebar.radio("Gå til:", ["Hjem", "Side 2: Tabell", "Side 3: Plot", "Side 4: Elhub", "Side 5: Open-Meteo"])

# Filsti til CSV
file = 'open-meteo-subset.csv'

# funksjonen slik at data ikke lastes inn på nytt hver gang appen kjører
@st.cache_data
def load_data(file):
    return pd.read_csv(file)


# Kaller funksjonen for å laste data og lagrer den i variabel df
df = load_data(file)
df["time"] = pd.to_datetime(df["time"])
df["month"] = df["time"].dt.month


   # Velg bakgrunnsfarge fra selectbox
   # Laget med hjelp av ChatGPT
color_choice = st.selectbox(
    "Velg bakgrunnsfarge:",
    ["Hvit", "Blå", "Grønn", "Gul", "Grå", "Rød", "Svart"]
)

# Vanlige fargekoder (hex)
colors = {
    "Hvit": "#FFFFFF",
    "Blå": "#0000FF",
    "Grønn": "#008000",
    "Gul": "#FFFF00",
    "Grå": "#808080",
    "Rød": "#FF0000",
    "Svart": "#000000"
}
bg_color = colors[color_choice]

    # Bruk CSS til å endre bakgrunnsfargen
st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {bg_color};
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# Sidene i streamlit-appen

# Side 1: Hjem
if page == "Hjem":
    st.title("Velkommen")
    st.header("Dette er hjem-siden")
    st.write("Bruk menyen i sidebaren for å navigere mellom sidene.")


# Side 2: Tabell med mini-linecharts (LineChartColumn)
elif page == "Side 2: Tabell":
    st.header("Tabell med rådata")
    st.dataframe(df.head(100))  # viser de første 20 radene

    st.header("Tabell med mini-linecharts")

    # Filtrer januar
    df_jan = df[df["month"] == 1]

    # Velg variabler
    variables = ["temperature_2m (°C)", "precipitation (mm)", 
                 "wind_speed_10m (m/s)", "wind_gusts_10m (m/s)", 
                 "wind_direction_10m (°)"]

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



# Side 3: Plot av kolonner mot tid
elif page == "Side 3: Plot":
    st.header("Plot av data")

    # Rensing og forberedelse av data
    line_chart_data = df.copy() #Lager en kopi av df
    line_chart_data['time'] = pd.to_datetime(line_chart_data['time']) #Sørger for at 'time' er i datetime-format
    line_chart_data['day'] = line_chart_data['time'].dt.day #Legger til en kolonne for dag

    # Finn alle variabler unntatt tid, dag og måned
    variables = [c for c in line_chart_data.columns if c not in ["time", "month", "day"]]

    # Velg variabel i selectbox
    pick_a_variable = st.selectbox(
        "Velg en variabel eller 'Alle variabler':",
        ["Alle variabler"] + variables
    )

    # Velg måneder (fra min til maks)
    months = sorted(line_chart_data["month"].unique()) # unike måneder i sortert rekkefølge
    pick_month_range = st.select_slider( 
        "Velg et månedsspenn:",
        options=months,
        value=(months[0], months[0])  # default = første måned
    )

    # Filtrer data på valgt månedsspenn
    df_plot = line_chart_data[
        (line_chart_data["month"] >= pick_month_range[0]) &
        (line_chart_data["month"] <= pick_month_range[1])
    ]

    # Plot
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

    # Tilpass aksetitler
    fig.update_layout(
        xaxis_title="Tid",
        yaxis_title="Verdi",
        legend_title="Variabler",
        template="plotly_white"
    )

    # Vis plottet
    st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# Side 4: Elhub-data fra MongoDB
# -----------------------------
elif page == "Side 4: Elhub":
    st.header("Elhub-data fra MongoDB")

    # ------------------------
    # 🔌 INITIALISER TILKOBLING
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
        st.success("✅ Tilkobling til MongoDB fungerer!")
    except Exception as e:
        st.error(f"❌ Klarte ikke koble til MongoDB: {e}")
        st.stop()

    # ------------------------
    # 📦 HENT DATA FRA MONGODB
    # ------------------------
    @st.cache_data(ttl=600)
    def get_data():
        db = client[st.secrets["mongo"]["database"]]
        collection = db[st.secrets["mongo"]["collection"]]
        return list(collection.find())

    items = get_data()
    if not items:
        st.warning("⚠️ Ingen data hentet — samlingen er kanskje tom?")
        st.stop()


    # ------------------------
    # 🧹 GJØR DATA KLAR FOR PLOTTING
    # ------------------------
    df_ready = pd.DataFrame(items)

    # Konverter eventuelle MongoDB-dicts {"$date": ...}
    if df_ready["startTime"].apply(lambda x: isinstance(x, dict)).any():
        df_ready["startTime"] = df_ready["startTime"].apply(
            lambda x: x.get("$date") if isinstance(x, dict) else x
        )

    df_ready["startTime"] = pd.to_datetime(df_ready["startTime"], errors="coerce", utc=True)
    df_ready["startTime"] = df_ready["startTime"].dt.tz_convert(None)
    df_ready["month"] = df_ready["startTime"].dt.to_period("M").astype(str)

    # ------------------------
    # 📊 VISUALISERINGER
    # ------------------------
    st.title("📊 Analyse av produksjonsdata")
    col1, col2 = st.columns(2)

    # Venstre kolonne – prisområde og kakediagram
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

    # Høyre kolonne – produksjonsgrupper, måned og linjediagram
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
    with st.expander("📘 Datakilde"):
        st.markdown(
            """
            Dataene som vises på denne siden hentes fra **MongoDB**-databasen `elhub_data`,
            samlingen `production_per_group_hour`.  
            Hver rad representerer én times produksjon for et gitt prisområde og produksjonsgruppe.  
            Kilde: **Elhub / Statnett**.
            """
        )



# Side 5: Live værdata fra Open-Meteo
#Dette er laget med hjelp av ChatGPT

if page == "Side 5: Open-Meteo":
    st.header("Live værdata fra Open-Meteo")

    # Velg by
    cities = {
        "Oslo": (59.91, 10.75),
        "Bergen": (60.39, 5.32),
        "Trondheim": (63.43, 10.39),
        "Tromsø": (69.65, 18.96),
    }
    city = st.selectbox("Velg en by:", list(cities.keys()))
    lat, lon = cities[city]

    # Hent data fra Open-Meteo
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&hourly=temperature_2m,precipitation,wind_speed_10m"
        f"&timezone=auto"
    )
    response = requests.get(url)
    data = response.json()

    # Lag DataFrame
    df_weather = pd.DataFrame(data["hourly"])
    df_weather["time"] = pd.to_datetime(df_weather["time"])

    # Vis rådata (første 20 rader)
    st.subheader(f"Timesdata for {city}")
    st.dataframe(df_weather.head(20))

    # Velg hvilken variabel du vil plotte
    variables = ["temperature_2m", "precipitation", "wind_speed_10m"]
    var = st.selectbox("Velg variabel å plotte:", variables)

    # Plot valgt variabel
    fig = px.line(
        df_weather,
        x="time",
        y=var,
        title=f"{var.replace('_', ' ').title()} i {city}"
    )
    fig.update_layout(
        xaxis_title="Tid",
        yaxis_title="Verdi",
        template="plotly_white"
    )
    st.plotly_chart(fig, use_container_width=True)
