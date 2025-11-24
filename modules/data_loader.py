import streamlit as st
import pandas as pd
import pymongo

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




# ------------------------------------------------------------
# 1. Hent data fra Elhub API (cachet)
# ------------------------------------------------------------
@st.cache_data
def hent_elhub_data(price_area: str):
    """Henter timesoppløst produksjonsdata fra Elhub API (2021)."""
    base_url = "https://api.elhub.no/energy-data/v0/price-areas"
    params = {'dataset': 'PRODUCTION_PER_GROUP_MBA_HOUR'}
    all_data = []

    for month in range(1, 13):
        start = date(2021, month, 1)
        end = date(2022, 1, 1) if month == 12 else date(2021, month + 1, 1)

        params['startDate'] = f"{start.isoformat()}T00:00:00+02:00"
        params['endDate'] = f"{end.isoformat()}T00:00:00+02:00"

        r = requests.get(base_url, params=params)
        r.raise_for_status()
        data = r.json().get('data', [])

        rows = []
        for d in data:
            attr = d.get('attributes', {})
            for p in attr.get('productionPerGroupMbaHour', []):
                # Filtrer på valgt prisområde
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
            df = pd.DataFrame(rows)
            all_data.append(df)

    if not all_data:
        st.error(f"Ingen data hentet for {price_area}.")
        st.stop()

    df_all = pd.concat(all_data, ignore_index=True)

    # ✅ Trygg konvertering av tidspunkter
    for col in ['startTime', 'endTime', 'lastUpdatedTime']:
        if col in df_all.columns:
            df_all[col] = pd.to_datetime(df_all[col], errors='coerce', utc=True)

    # Fjern rader uten gyldig startTime
    df_all = df_all.dropna(subset=['startTime'])
    df_all = df_all[df_all['startTime'].dt.year == 2021]

    return df_all
