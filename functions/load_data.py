import pandas as pd
import requests
import pymongo
import streamlit as st
from datetime import date


# ---------------------------------------------------------
# ERA5 weather 
# ---------------------------------------------------------
def load_era5_raw(latitude, longitude, year):
    try:
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"

        url = (
            "https://archive-api.open-meteo.com/v1/era5?"
            f"latitude={latitude}&longitude={longitude}&"
            f"start_date={start_date}&end_date={end_date}&"
            "hourly=temperature_2m,precipitation,wind_speed_10m,"
            "wind_gusts_10m,wind_direction_10m&timezone=auto"
        )

        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "hourly" not in data:
            st.error("ERA5 API returned no hourly data.")
            return pd.DataFrame()

        df = pd.DataFrame(data["hourly"])
        df["time"] = pd.to_datetime(df["time"], errors="coerce")
        return df

    except Exception as e:
        st.error(f"Failed to load ERA5 data: {e}")
        return pd.DataFrame()


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
@st.cache_data
def hent_elhub_data(price_area: str):
    try:
        base_url = "https://api.elhub.no/energy-data/v0/price-areas"
        params = {'dataset': 'PRODUCTION_PER_GROUP_MBA_HOUR'}

        all_data = []

        for month in range(1, 13):
            start = date(2021, month, 1)
            end = date(2022, 1, 1) if month == 12 else date(2021, month + 1, 1)

            params['startDate'] = f"{start}T00:00:00+02:00"
            params['endDate'] = f"{end}T00:00:00+02:00"

            r = requests.get(base_url, params=params, timeout=10)
            r.raise_for_status()

            raw = r.json().get("data", [])
            if not raw:
                continue

            rows = []
            for d in raw:
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

        if not all_data:
            st.warning(f"No API data found for price area {price_area}.")
            return pd.DataFrame()

        df = pd.concat(all_data, ignore_index=True)
        df["startTime"] = pd.to_datetime(df["startTime"], utc=True, errors="coerce")
        df = df[df["startTime"].dt.year == 2021]

        return df

    except Exception as e:
        st.error(f"Failed to fetch API data: {e}")
        return pd.DataFrame()
