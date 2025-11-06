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
| 📊 **Page 2: Table** | Elhub Raw Data | Displays production data from MongoDB with pie and line charts |
| 📈 **Page 3: Plot (API)** | Elhub API Data | Retrieves production data from the Elhub API for the selected price area |
| ⚙️ **Page 4: Elhub (MongoDB)** | Database Viewer | Connects directly to MongoDB Atlas and loads data with caching |
| 🌦 **Page 5: Open-Meteo (API)** | Weather Data | Fetches meteorological data (temperature, wind, precipitation) via Open-Meteo API |
| 🧮 **Page 6: SPC & LOF Analysis** | Statistical Quality Control | Performs outlier detection (SPC) and anomaly detection (LOF) on weather data |
| 🌈 **Page 7: Open-Meteo Extended** | Advanced Analyses | STL decomposition and Spectrogram analysis of meteorological time series |

---

## 🧠 Key Concepts

- **`st.session_state`** – Used to share data and user selections (like price area) between pages.  
- **`@st.cache_data`** – Caches downloaded or processed data to avoid re-fetching and speed up performance.  
- **`@st.cache_resource`** – Keeps persistent connections (like MongoDB) alive across reruns.  
- **MongoDB Atlas** – Stores historical Elhub production data.  
- **Open-Meteo API** – Fetches weather data dynamically from the ERA5 dataset.

---

## 🧰 Technologies Used

| Library | Purpose |
|----------|----------|
| `streamlit` | Frontend framework for the interactive web app |
| `pandas` | Data manipulation and analysis |
| `plotly.express` | Interactive visualizations |
| `plotly.graph_objects` | Advanced chart customization (STL, spectrogram, SPC) |
| `requests` | API requests (Elhub & Open-Meteo) |
| `pymongo` | MongoDB connectivity |
| `scikit-learn` | Local Outlier Factor (LOF) anomaly detection |
| `numpy`, `scipy` | Numerical processing and DCT transformations |
| `statsmodels` | STL decomposition for time series |
| `urllib.parse` | Secure URI handling for database credentials |

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
📦 pialoschbrandt-app/
├── modules/
│   ├── page_1.py          # Home
│   ├── page_2.py          # Elhub data table
│   ├── page_3.py          # Elhub API plots (STL, spectrogram)
│   ├── page_4.py          # MongoDB data retrieval
│   ├── page_5.py          # Open-Meteo data display
│   ├── page_6.py          # SPC and LOF statistical analysis
│   ├── page_7.py          # Extended analyses (spectrogram/STL)
├── streamlit_app.py       # Main app entry point and navigation
├── requirements.txt        # Dependencies
└── README.md               # Documentation

## Example Workflow:
Go to Page 2 and select a price area (NO1–NO5).
On Page 5, the app fetches weather data for the corresponding region.
On Page 6, use the SPC and LOF tabs to analyze temperature outliers and precipitation anomalies.
Optionally, explore Page 7 for STL and spectrogram analysis.
All data and selections are automatically shared between pages using st.session_state.

## Summary:
This project demonstrates:
Real-time API integration (Elhub & Open-Meteo)
Database connectivity with MongoDB
Advanced analytics (SPC, LOF, STL, Spectrogram)
Interactive visualization and filtering
Efficient state and cache management in Streamlit