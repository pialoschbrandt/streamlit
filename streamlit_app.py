import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import pandas as pd
from pymongo import MongoClient
from urllib.parse import quote_plus
import pymongo

# Navigasjon i sidebar
st.sidebar.title("Navigasjon")
page = st.sidebar.radio("Gå til:", ["Hjem", "Side 2: Tabell", "Side 3: Plot", "Side 4: Elhub", "Side 5: Open-Meteo"])

# Filsti til CSV
file = '/Users/pialoschbrandt/Documents/Skole/Semester-5/Ind320/Innlevering1/data/open-meteo-subset.csv'

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


# Side 4: Elhub-data fra MongoDB
elif page == "Side 4: Elhub":
    st.header("Elhub produksjonsdata fra MongoDB")

    # ⚙️ Opprett MongoDB-forbindelse (kjøres bare én gang)
    @st.cache_resource
    def init_connection():
        user = st.secrets["mongo"]["user"]
        password = quote_plus(st.secrets["mongo"]["password"])
        cluster = st.secrets["mongo"]["cluster"]

        uri = f"mongodb+srv://{user}:{password}@{cluster}/?retryWrites=true&w=majority"
        client = pymongo.MongoClient(uri)

        # 🔍 Test at tilkoblingen fungerer (ping)
        try:
            client.admin.command("ping")
            st.sidebar.success("✅ Tilkoblet MongoDB")
        except Exception as e:
            st.sidebar.error(f"🚨 Klarte ikke å koble til MongoDB: {e}")

        return client

    client = init_connection()

    # 📦 Hent data (lagres i cache i 10 min)
    @st.cache_data(ttl=600)
    def get_data():
        db = client[st.secrets["mongo"]["database"]]
        collection = db[st.secrets["mongo"]["collection"]]
        return list(collection.find())

    # 🧱 Streamlit-grensesnitt
    st.header("Elhub-data fra MongoDB")

    try:
        data = get_data()

        if not data:
            st.warning("Ingen data funnet i databasen.")
        else:
            df = pd.DataFrame(data).drop(columns=["_id"], errors="ignore")
            st.success(f"✅ Hentet {len(df)} rader fra MongoDB.")
            st.dataframe(df)

    except Exception as e:
        st.error(f"🚨 Feil under henting av data: {e}")



# Side 5: Live værdata fra Open-Meteo
#Dette er laget med hjelp av ChatGPT

elif page == "Side 5: Open-Meteo":
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