import pandas as pd
import requests
import pymongo
import streamlit as st
from datetime import date


# ---------------------------------------------------------
# ERA5 weather 
# ---------------------------------------------------------
def load_era5_raw(latitude, longitude, year):
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"

    url = (
        "https://archive-api.open-meteo.com/v1/era5?"
        f"latitude={latitude}&longitude={longitude}&"
        f"start_date={start_date}&end_date={end_date}&"
        "hourly=temperature_2m,precipitation,wind_speed_10m,"
        "wind_gusts_10m,wind_direction_10m&timezone=auto"
    )

    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    df = pd.DataFrame(data["hourly"])
    df["time"] = pd.to_datetime(df["time"])
    return df


# ---------------------------------------------------------
# MongoDB CLIENT (cached once per session)
# ---------------------------------------------------------
@st.cache_resource
def get_mongo_client():
    uri = (
        f"mongodb+srv://{st.secrets['mongo']['user']}:"
        f"{st.secrets['mongo']['password']}@"
        f"{st.secrets['mongo']['cluster']}/"
        "?retryWrites=true&w=majority"
    )
    client = pymongo.MongoClient(uri)
    client.admin.command("ping")
    return client


# ---------------------------------------------------------
# 1 — Load Elhub-data FRA MONGODB (for dashboards)
# ---------------------------------------------------------
@st.cache_data(ttl=600)
def load_elhub_data():
    """Loads production + consumption datasets from MongoDB (fast)."""

    client = get_mongo_client()
    db = client[st.secrets["mongo"]["database"]]

    df_prod = pd.DataFrame(list(db["production_per_group_mba_hour"].find()))
    df_cons = pd.DataFrame(list(db["consumption_per_group_mba_hour"].find()))

    # Convert datetimes
    for df in (df_prod, df_cons):
        for col in ["start_time", "end_time", "last_updated_time"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

    df_prod["source"] = "production"
    df_cons["source"] = "consumption"

    df_prod["energy_group"] = df_prod["production_group"]
    df_cons["energy_group"] = df_cons["consumption_group"]

    df = pd.concat([df_prod, df_cons], ignore_index=True)

    df["year"] = df["start_time"].dt.year
    df["month"] = df["start_time"].dt.to_period("M").astype(str)

    return df


# ---------------------------------------------------------
# 2 — Load API-data (2021 only) for STL/Spectrogram
# ---------------------------------------------------------
@st.cache_data
def hent_elhub_data(price_area: str):
    """Henter rå API-data for KUN produksjon i 2021.
       Brukes av page_3 (STL og spektrogram).
    """

    base_url = "https://api.elhub.no/energy-data/v0/price-areas"
    params = {'dataset': 'PRODUCTION_PER_GROUP_MBA_HOUR'}

    all_data = []

    for month in range(1, 13):

        start = date(2021, month, 1)
        end = date(2022, 1, 1) if month == 12 else date(2021, month + 1, 1)

        params['startDate'] = f"{start}T00:00:00+02:00"
        params['endDate'] = f"{end}T00:00:00+02:00"

        r = requests.get(base_url, params=params)
        r.raise_for_status()
        data = r.json().get('data', [])

        rows = []
        for d in data:
            attr = d.get('attributes', {})

            for p in attr.get('productionPerGroupMbaHour', []):
                if p.get('priceArea') == price_area:
                    rows.append({
                        'country': attr.get('country'),
                        'priceArea': p.get('priceArea'),
                        'productionGroup': p.get('productionGroup'),
                        'quantityKwh': p.get('quantityKwh'),
                        'startTime': p.get('startTime'),
                        'endTime': p.get('endTime'),
                        'lastUpdatedTime': p.get('lastUpdatedTime')
                    })

        if rows:
            all_data.append(pd.DataFrame(rows))

    df_all = pd.concat(all_data, ignore_index=True)

    df_all["startTime"] = pd.to_datetime(df_all["startTime"], utc=True)
    df_all = df_all[df_all["startTime"].dt.year == 2021]

    return df_all


