import streamlit as st
import pandas as pd
import numpy as np
from scipy.fft import dct, idct
from sklearn.neighbors import LocalOutlierFactor
import plotly.graph_objects as go

# 👇 Gjenbruk funksjonen fra page_5
from modules.page_5 import get_or_load_meteo_data


# ------------------------------------------------------------
# --- 1. Hjelpefunksjon: SPC-analyse for temperatur -----------
# ------------------------------------------------------------
def analyser_temperatur_dct_spc(
    df, verdi_kolonne="temperature_2m", tids_kolonne="time",
    cutoff_dager=90, k_sigma=3
):
    """Robust SPC-analyse med DCT-filtrert serie."""
    s = (
        df.set_index(tids_kolonne)
        .sort_index()[verdi_kolonne]
        .asfreq("1h")
        .interpolate("time")
    )

    x = s.to_numpy()
    N = len(x)

    # --- Diskret cosinustransform ---
    c = dct(x, type=2, norm="ortho")
    T_timer = cutoff_dager * 24
    k_cut = max(int(np.floor(2 * N / T_timer)), 1)
    c_hp = c.copy()
    c_hp[:k_cut] = 0.0

    # --- Høyfrekvent komponent (SATV) ---
    satv = idct(c_hp, type=2, norm="ortho")

    # --- Robust SPC-grenser ---
    median = np.median(satv)
    mad = np.median(np.abs(satv - median))
    sigma = 1.4826 * mad if mad > 0 else np.std(satv)
    lo, hi = median - k_sigma * sigma, median + k_sigma * sigma
    is_outlier = (satv < lo) | (satv > hi)

    # --- Plot ---
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df[tids_kolonne], y=df[verdi_kolonne],
        mode="lines", name="Temperatur (°C)", line=dict(color="steelblue")
    ))
    fig.add_trace(go.Scatter(
        x=df[tids_kolonne][is_outlier],
        y=df[verdi_kolonne][is_outlier],
        mode="markers", name="Outliers (±3σ)",
        marker=dict(color="red", size=5)
    ))
    fig.update_layout(
        title="Temperatur med SPC-outliers (DCT-basert SATV)",
        xaxis_title="Tid", yaxis_title="Temperatur (°C)",
        template="plotly_white", hovermode="x unified", title_x=0.5
    )

    stats = {
        "median_SATV": round(float(median), 3),
        "sigma_SATV": round(float(sigma), 3),
        "nedre_grense": round(float(lo), 3),
        "ovre_grense": round(float(hi), 3),
        "antall_outliers": int(is_outlier.sum()),
        "andel_outliers_%": round(100 * is_outlier.mean(), 2),
    }

    return fig, stats


# ------------------------------------------------------------
# --- 2. Hjelpefunksjon: LOF-analyse for nedbør --------------
# ------------------------------------------------------------
def analyser_nedbor_lof(df, verdi_kolonne="precipitation",
                        tids_kolonne="time", andel_outliers=0.01):
    """LOF-analyse for å finne anomale nedbørshendelser."""
    s = (
        df.set_index(tids_kolonne)
        .sort_index()[verdi_kolonne]
        .asfreq("1h")
        .interpolate("time")
        .fillna(0.0)
    )
    x = s.to_numpy().reshape(-1, 1)

    lof = LocalOutlierFactor(contamination=andel_outliers, n_neighbors=50)
    labels = lof.fit_predict(x)
    scores = -lof.negative_outlier_factor_
    is_outlier = labels == -1

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df[tids_kolonne], y=df[verdi_kolonne],
        mode="lines", name="Nedbør (mm/t)", line=dict(color="royalblue")
    ))
    fig.add_trace(go.Scatter(
        x=df[tids_kolonne][is_outlier],
        y=df[verdi_kolonne][is_outlier],
        mode="markers", name="Anomalier (LOF)",
        marker=dict(color="red", size=6)
    ))
    fig.update_layout(
        title=f"Nedbør med LOF-anomalier (andel={andel_outliers*100:.1f} %)",
        xaxis_title="Tid", yaxis_title="Nedbør (mm/t)",
        template="plotly_white", hovermode="x unified", title_x=0.5
    )

    stats = {
        "antall_observasjoner": int(len(x)),
        "antall_outliers": int(is_outlier.sum()),
        "andel_outliers_%": round(100 * is_outlier.mean(), 2),
        "gjennomsnitt_LOF": round(scores.mean(), 3),
        "maks_LOF": round(scores.max(), 3),
    }
    return fig, stats


# ------------------------------------------------------------
# --- 3. Streamlit-side: “new B” ------------------------------
# ------------------------------------------------------------
def show():
    st.title("Outlier- og Anomalidetektering")

    # 🔹 Bruk eksisterende Open-Meteo-data eller hent automatisk
    df, selected_area = get_or_load_meteo_data(2021)

    st.write(f"📍 Analyserer værdata for prisområde **{selected_area}** (Open-Meteo ERA5, 2021)")

    # Tabs
    tabs = st.tabs(["📊 SPC – Temperatur Outliers", "🌧 LOF – Nedbør Anomalier"])

    # === Tab 1: SPC-analyse ===
    with tabs[0]:
        st.subheader("SPC-analyse av temperatur")
        st.write(
            "Denne analysen bruker **robuste SPC-grenser** "
            "(median ± k × 1.4826 × MAD) etter DCT-filtrering for å fremheve raske, "
            "uvanlige temperaturendringer."
        )
        cutoff = st.slider("Trend-cutoff (dager)", 30, 180, 90, step=10)
        k_sigma = st.slider("k σ (kontrollgrense)", 1, 5, 3, step=1)

        fig_spc, stats_spc = analyser_temperatur_dct_spc(df, "temperature_2m", "time", cutoff, k_sigma)
        st.plotly_chart(fig_spc, use_container_width=True)
        st.dataframe(pd.DataFrame([stats_spc]))

        with st.expander("📘 Forklaring"):
            st.markdown(
                """
                Røde punkter markerer **outliers** — timer der den sesongjusterte temperaturvariasjonen ligger utenfor ± 3 σ.  
                Disse indikerer ekstreme kulde- eller varme-episoder.
                """
            )

    # === Tab 2: LOF-analyse ===
    with tabs[1]:
        st.subheader("LOF-analyse av nedbør")
        st.write(
            "Metoden **Local Outlier Factor (LOF)** finner observasjoner som avviker sterkt fra nabopunktene, "
            "for eksempel ekstremregn."
        )
        andel = st.slider("Forventet andel anomalier (%)", 0.1, 5.0, 1.0, step=0.1) / 100.0
        fig_lof, stats_lof = analyser_nedbor_lof(df, "precipitation", "time", andel)
        st.plotly_chart(fig_lof, use_container_width=True)
        st.dataframe(pd.DataFrame([stats_lof]))

        with st.expander("📘 Forklaring"):
            st.markdown(
                """
                **LOF** måler hvor tett en observasjon ligger i forhold til naboene.  
                Høy LOF-score betyr at verdien skiller seg ut og regnes som en anomali.
                """
            )
