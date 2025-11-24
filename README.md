# ⚡ Streamlit Elhub & Open-Meteo App
### Developed by Pia Loschbrandt  
**Course:** IND320 – Industrial Digitalization  

---

## 🌍 Overview
This project is an interactive **Streamlit web application** that combines **energy production data from Elhub** (stored in MongoDB) and **weather data from the Open-Meteo API (ERA5 reanalysis)**.  
The app provides interactive visualizations and statistical analyses of production and meteorological data across Norwegian price areas (NO1–NO5) for the year 2021.

---
## 🚀 Features

The application consists of multiple pages, accessible from the sidebar:

| Page | Name | Description |
|------|------|--------------|
| 🏠 **Home** | Introduction | Overview of the project and navigation |
| 📊 **Page 2: Table** | Elhub Raw Data | Displays production and consumption data from MongoDB with pie and line charts |
| 📈 **Page 3: Plot (API)** | Elhub API Data | Retrieves production data from the Elhub API for the selected price area |
| ⚙️ **Page 4: Elhub (MongoDB)** | Database Viewer | Loads historical Elhub data (production and consumption) from MongoDB with caching |
| 🌦 **Page 5: Open-Meteo (API)** | Weather Data | Fetches weather data (temperature, wind, precipitation, snow depth) from the Open-Meteo ERA5 API |
| 🧮 **Page 6: SPC & LOF Analysis** | Statistical Quality Control | Outlier detection using SPC and LOF on meteorological variables |
| 🌈 **Page 7: Open-Meteo Extended** | Advanced Analyses | STL decomposition, spectrograms and transformation-based weather analysis |
| 📉 **Correlation Analysis** | Weather–Energy Correlation | Computes sliding correlations between weather variables and energy signals |
| 🔮 **Energy Forecast (SARIMAX)** | Forecasting | Forecasts production, consumption and net load using SARIMAX with configurable model parameters |
| 🗺 **Geo** | Geospatial View | Provides geospatial visualizations including wind direction, clusters and map overlays |
| ❄️ **Snow Drift** | Snow & Wind Analysis | Snow drift modelling and wind rose generation |


## 🧠 Key Concepts

- **`st.session_state`** – Used to share data and user selections (like price area) between pages.  
- **`@st.cache_data`** – Caches downloaded or processed data to avoid re-fetching and speed up performance.  
- **`@st.cache_resource`** – Keeps persistent connections (like MongoDB) alive across reruns.  
- **MongoDB Atlas** – Stores historical Elhub production data.  
- **Open-Meteo API** – Fetches weather data dynamically from the ERA5 dataset.

---

## 🧰 Technologies Used
## Libraries Used

| Library | Purpose |
|---------|---------|
| streamlit | Frontend framework for building the interactive web application |
| pandas | Data manipulation, time-series handling, cleaning and aggregation |
| numpy | Numerical computing and array operations |
| scipy | Numerical transformations (including DCT), signal analysis |
| plotly | Interactive charting and dashboard visualizations |
| plotly.express | Quick high-level chart API |
| plotly.graph_objects | Advanced chart customization (STL, spectrogram, SPC, forecasting plots) |
| requests | API requests for Elhub API and Open-Meteo ERA5 |
| pymongo | MongoDB Atlas connectivity and data retrieval |
| scikit-learn | Outlier detection using LOF, correlation utilities |
| statsmodels | Time-series forecasting (SARIMAX), STL decomposition, statistical modeling |
| python-dateutil | Date/time parsing and manipulation |
| pytz | Time zone conversions for timestamps |
| urllib.parse | Safe URI handling for MongoDB credentials |
---

## ⚙️ Local Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/<username>/<repo-name>.git
   cd <repo-name>


2. Install dependencies
- pip install -r requirements.txt

3. Create a secrets file for MongoDB
Create a secrets file for MongoDB
[mongo]
user = "your_username"
password = "your_password"
cluster = "cluster.mongodb.net"
database = "elhub_data"
collection = "production_per_group_hour"

4. Run the application
streamlit run streamlit_app.py

5. Navigate between pages
Use the sidebar to switch between pages.
On Page 2, select your preferred price area (NO1–NO5) — this selection is stored in st.session_state and used automatically on other pages.


## Data Sources:

| Source              | Description                                                           | URL                                                            |
| ------------------- | --------------------------------------------------------------------- | -------------------------------------------------------------- |
| **Elhub API**       | Hourly energy production by price area and production group in Norway | [https://api.elhub.no/](https://api.elhub.no/)                 |
| **Open-Meteo ERA5** | Hourly weather data (temperature, wind, precipitation)                | [https://open-meteo.com/](https://open-meteo.com/)             |
| **MongoDB Atlas**   | Cloud-hosted database containing Elhub production data                | [https://www.mongodb.com/atlas](https://www.mongodb.com/atlas) |

## Project Structure:


pialoschbrandt-app/
├── modules/
│   ├── page_1.py             # Home
│   ├── page_2.py             # Elhub raw data table
│   ├── page_3.py             # Elhub API plots (STL, spectrogram)
│   ├── page_4.py             # MongoDB data retrieval (production & consumption)
│   ├── page_5.py             # Open-Meteo weather data display
│   ├── page_6.py             # SPC and LOF statistical analysis
│   ├── page_7.py             # Extended weather analyses (spectrogram/STL)
│   ├── page_corr.py          # Weather–energy correlation analysis
│   ├── page_forecast.py      # SARIMAX forecasting (production, consumption, net load)
│   ├── page_Geo.py           # Geospatial map and wind data
│   ├── page_Snow.py          # Snow drift modelling and snow/wind stats
├── functions/
│   ├── data_loader.py        # Shared data loading utilities
│   └── load_elhub_data.py    # Dedicated loader for Elhub production/consumption
│
├── streamlit_app.py          # Main app entry point and navigation
├── requirements.txt          # Project dependencies (libraries used)
└── README.md                 # Full documentation for the application
     # Documentation

## Summary:
This project demonstrates:
Real-time API integration (Elhub & Open-Meteo)
Database connectivity with MongoDB
Advanced analytics (SPC, LOF, STL, Spectrogram)
Interactive visualization and filtering
Efficient state and cache management in Streamlit