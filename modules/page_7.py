import streamlit as st
import requests
import pandas as pd
import plotly.express as px

def show():
    st.header("🌤️ Live værdata fra Open-Meteo")


    # Velg by
    cities = {
        "Oslo": (59.91, 10.75),
        "Bergen": (60.39, 5.32),
        "Trondheim": (63.43, 10.39),
        "Tromsø": (69.65, 18.96),
    }

    city = st.selectbox("Velg en by:", list(cities.keys()))
    lat, lon = cities[city]

    # Hent data fra Open-Meteo API
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&hourly=temperature_2m,precipitation,wind_speed_10m"
        f"&timezone=auto"
    )
    response = requests.get(url)
    data = response.json()

    # Konverter data til DataFrame
    df_weather = pd.DataFrame(data["hourly"])
    df_weather["time"] = pd.to_datetime(df_weather["time"])

    # Vis rådata
    st.subheader(f"Timesdata for {city}")
    st.dataframe(df_weather.head(20))

    # Velg variabel for plotting
    variables = ["temperature_2m", "precipitation", "wind_speed_10m"]
    var = st.selectbox("Velg variabel å plotte:", variables)

    # Lag linjediagram
    fig = px.line(
        df_weather,
        x="time",
        y=var,
        title=f"{var.replace('_', ' ').title()} i {city}",
    )
    fig.update_layout(
        xaxis_title="Tid",
        yaxis_title="Verdi",
        template="plotly_white"
    )
    st.plotly_chart(fig, use_container_width=True)