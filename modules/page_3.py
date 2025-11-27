import streamlit as st
import pandas as pd
import requests
from datetime import date
from statsmodels.tsa.seasonal import STL
import plotly.graph_objects as go
from scipy import signal
import numpy as np
from functions.load_data import hent_elhub_data



# ------------------------------------------------------------
# 1. Hent data fra Elhub API (cachet)
# ------------------------------------------------------------


# ------------------------------------------------------------
# 2. STL-dekomponering
# ------------------------------------------------------------
def stl_decomposition_plot(df, price_area, production_group, period=24, seasonal=13, trend=31, robust=True):
    required_cols = {"priceArea", "productionGroup", "quantityKwh", "startTime"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"Mangler kolonner: {required_cols - set(df.columns)}")

    df_filtered = df[
        (df["priceArea"].str.upper() == price_area.upper()) &
        (df["productionGroup"].str.lower() == production_group.lower())
    ].copy()

    if df_filtered.empty:
        st.warning(f"Ingen data funnet for {price_area} / {production_group}")
        return None

    df_filtered["startTime"] = pd.to_datetime(df_filtered["startTime"], utc=True, errors="coerce").dt.tz_convert(None)
    df_filtered = df_filtered.dropna(subset=["startTime"]).sort_values("startTime").set_index("startTime")

    ts = df_filtered["quantityKwh"].resample("h").mean().interpolate()
    stl = STL(ts, period=period, seasonal=seasonal, trend=trend, robust=robust)
    result = stl.fit()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ts.index, y=ts, name="Original", line=dict(color="blue")))
    fig.add_trace(go.Scatter(x=ts.index, y=result.trend, name="Trend", line=dict(color="red")))
    fig.add_trace(go.Scatter(x=ts.index, y=result.seasonal, name="Seasonal", line=dict(color="orange")))
    fig.add_trace(go.Scatter(x=ts.index, y=result.resid, name="Residual", line=dict(color="green")))

    fig.update_layout(
        title=f"STL-dekomponering for {production_group.upper()} i {price_area} (2021)",
        xaxis_title="Tid",
        yaxis_title="Produksjon (kWh)",
        template="plotly_white",
        hovermode="x unified",
    )
    return fig


# ------------------------------------------------------------
# 3. Spektrogram
# ------------------------------------------------------------
def spectrogram_plot(df, price_area, production_group, window_length=256, overlap=128):
    dff = df[
        (df["priceArea"].str.upper() == price_area.upper()) &
        (df["productionGroup"].str.lower() == production_group.lower())
    ].copy()

    if dff.empty:
        st.warning(f"Ingen data for {price_area}/{production_group}")
        return None

    dff["startTime"] = pd.to_datetime(dff["startTime"], utc=True, errors="coerce").dt.tz_convert(None)
    dff = dff.dropna(subset=["startTime"]).sort_values("startTime").set_index("startTime")
    ts = dff["quantityKwh"].resample("h").mean().interpolate()

    if len(ts) < max(32, window_length):
        st.warning(f"For kort serie ({len(ts)} punkter) for vindu {window_length}")
        return None

    overlap = min(overlap, window_length - 1)
    fs = 1.0  # én måling per time

    f, t_rel, Sxx = signal.spectrogram(
        ts.values,
        fs=fs,
        nperseg=window_length,
        noverlap=overlap,
        detrend="linear",
        scaling="spectrum",
        window="hann",
    )

    Sxx_db = 10 * np.log10(Sxx + 1e-12)
    t0 = ts.index[0]
    t_abs = t0 + pd.to_timedelta(t_rel, unit="h")
    f_per_day = f * 24.0

    fig = go.Figure(
        data=go.Heatmap(z=Sxx_db, x=t_abs, y=f_per_day, colorscale="Viridis", colorbar=dict(title="Power [dB]"))
    )
    fig.update_layout(
        title=f"Spektrogram for {production_group.upper()} i {price_area} (2021)",
        xaxis_title="Tid (2021)",
        yaxis_title="Frekvens [sykluser/døgn]",
        template="plotly_white",
    )
    return fig


# ------------------------------------------------------------
# 4. Streamlit-side
# ------------------------------------------------------------
def show():
    st.title("Analyse av produksjonsdata – STL og Spektrogram")

    # --- Hent valgt område fra session_state ---
    selected_area = st.session_state.get("selected_area")
    if not selected_area:
        st.warning("⚠️ Du må først velge et prisområde på side 4 (Elhub-data).")
        st.stop()

    st.success(f"📍 Analysen gjelder prisområde **{selected_area}** for året 2021.")

    # --- Hent data ---
    df_all = hent_elhub_data(selected_area)
    st.write(f"✅ Hentet {len(df_all):,} rader fra Elhub API")

    production_groups = sorted(df_all["productionGroup"].dropna().unique())
    selected_group = st.selectbox("Velg produksjonsgruppe:", production_groups)

    tabs = st.tabs(["📈 STL-analyse", "🌈 Spektrogram"])

    # --- Tab 1 ---
    with tabs[0]:
        st.subheader("STL-dekomponering")
        st.write(
            """
            **STL (Seasonal-Trend decomposition using Loess)** deler opp tidsserien i tre komponenter:
            - **Trend:** Langsiktig utvikling  
            - **Sesong:** Regelmessige mønstre  
            - **Residual:** Støy og uregelmessige svingninger
            """
        )
        fig_stl = stl_decomposition_plot(df_all, selected_area, selected_group)
        if fig_stl:
            st.plotly_chart(fig_stl, use_container_width=True)

    # --- Tab 2 ---
    with tabs[1]:
        st.subheader("Spektrogram")
        window_length = st.slider("Velg vinduslengde (timer)", 64, 512, 256, step=32)
        overlap = st.slider("Velg overlapp (timer)", 32, 256, 128, step=32)

        fig_spec = spectrogram_plot(df_all, selected_area, selected_group, window_length, overlap)
        if fig_spec:
            st.plotly_chart(fig_spec, use_container_width=True)