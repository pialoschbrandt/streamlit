import pandas as pd
import requests
import pymongo
import streamlit as st

# ---------------------------------------------------------
# ERA5 weather 
# ---------------------------------------------------------
def load_era5_raw(latitude, longitude, year):
    """
    Fetch hourly ERA5 weather data from Open-Meteo for the given location and year.
    """
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"

    url = (
        "https://archive-api.open-meteo.com/v1/era5?"
        f"latitude={latitude}&longitude={longitude}&"
        f"start_date={start_date}&end_date={end_date}&"
        "hourly=temperature_2m,precipitation,wind_speed_10m,wind_gusts_10m,wind_direction_10m&"
        "timezone=auto"
    )

    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    df = pd.DataFrame(data["hourly"])
    df["time"] = pd.to_datetime(df["time"])
    return df


# ---------------------------------------------------------
# Elhub loader 
# ---------------------------------------------------------
@st.cache_data(ttl=600)
def load_elhub_data():
    """Loads production + consumption datasets and returns merged DataFrame."""

    # Connect to MongoDB
    uri = (
        f"mongodb+srv://{st.secrets['mongo']['user']}:"
        f"{st.secrets['mongo']['password']}@"
        f"{st.secrets['mongo']['cluster']}/?retryWrites=true&w=majority"
    )
    client = pymongo.MongoClient(uri)
    db = client[st.secrets["mongo"]["database"]]

    # Correct collection names
    prod_col = "production_per_group_mba_hour"
    cons_col = "consumption_per_group_mba_hour"

    # Load into DataFrame
    df_prod = pd.DataFrame(list(db[prod_col].find()))
    df_cons = pd.DataFrame(list(db[cons_col].find()))

    # Rename to snake_case if needed
    rename_map = {
        "priceArea": "price_area",
        "productionGroup": "production_group",
        "consumptionGroup": "consumption_group",
        "quantityKwh": "quantity_kwh",
    }

    df_prod.rename(columns=rename_map, inplace=True)
    df_cons.rename(columns=rename_map, inplace=True)

    # Ensure datetime
    for col in ["start_time", "end_time", "last_updated_time"]:
        if col in df_prod.columns:
            df_prod[col] = pd.to_datetime(df_prod[col], errors="coerce")
        if col in df_cons.columns:
            df_cons[col] = pd.to_datetime(df_cons[col], errors="coerce")

    # Add source column
    df_prod["source"] = "production"
    df_cons["source"] = "consumption"

    # --------------------------------------------------
    # ⭐ ADD UNIFIED energy_group HERE
    # --------------------------------------------------
    df_prod["energy_group"] = df_prod["production_group"]
    df_cons["energy_group"] = df_cons["consumption_group"]
    # --------------------------------------------------

    # Merge (now both dfs contain energy_group)
    df_all = pd.concat([df_prod, df_cons], ignore_index=True)

    # Add month
    df_all["month"] = df_all["start_time"].dt.to_period("M").astype(str)

    return df_all
