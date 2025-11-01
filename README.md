# pialoschbrandt-app
# ⚡ Streamlit Elhub & Open-Meteo App

Dette prosjektet er en interaktiv **Streamlit-applikasjon** som kombinerer lokale værdata og elhub-data for å visualisere temperatur, vind, nedbør og produksjonsdata over tid.  
Applikasjonen er utviklet som en del av faget **IND320 – Industriell digitalisering**.

---

## 🚀 Funksjoner

Appen har fem sider, navigerbare fra sidebaren:

1. **Hjem** – introduksjon og navigasjon  
2. **Tabell** – viser rådata og mini-linecharts for værvariabler  
3. **Plot** – interaktive grafer med Plotly Express  
4. **Elhub (MongoDB)** – henter elhub-data direkte fra MongoDB Atlas  
5. **Open-Meteo (API)** – viser live værdata for norske byer via Open-Meteo API

---

## 🧰 Brukte teknologier

| Bibliotek | Beskrivelse |
|------------|-------------|
| `streamlit` | Brukergrensesnitt for webappen |
| `pandas` | Databehandling og analyse |
| `plotly.express` | Interaktive grafer |
| `requests` | Henter live-data fra Open-Meteo API |
| `pymongo` | Kobling til MongoDB |
| `urllib.parse` | Håndtering av passord i URI-format |

---

## ⚙️ Installasjon (lokalt)

1. **Klon repoet**  
   ```bash
   git clone https://github.com/<brukernavn>/<repo-navn>.git
   cd <repo-navn>


2. pip install -r requirements.txt

3. Opprett secrets-fil for MongoDB
    Lag en fil: .streamlit/secrets.toml
    [mongo]
user = "brukernavn"
password = "passord"
cluster = "cluster.mongodb.net"
database = "elhub_data"
collection = "production_per_group_hour"

5. streamlit run streamlit_app.py

6. 