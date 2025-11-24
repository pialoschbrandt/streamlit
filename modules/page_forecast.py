# modules/page_forecast.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from datetime import timedelta
from statsmodels.tsa.statespace.sarimax import SARIMAX
from functions.load_data import load_elhub_data


# ==============================================================
#  HJELPEFUNKSJONER
# ==============================================================

def prepare_series(df: pd.DataFrame, price_area: str, source: str | None = None) -> pd.Series:
    """
    Hent timesaggregert tidsserie (kWh) for valgt prisområde og kilde (production/consumption/None).
    Hvis source=None, brukes både produksjon og forbruk samlet.
    """
    df = df.copy()
    df["start_time"] = pd.to_datetime(df["start_time"], errors="coerce")
    df = df.dropna(subset=["start_time", "quantity_kwh"])
    df = df.sort_values("start_time")

    if "price_area" in df.columns:
        df = df[df["price_area"] == price_area]

    if source is not None and "source" in df.columns:
        df = df[df["source"] == source]

    ts = (
        df.set_index("start_time")["quantity_kwh"]
        .resample("H")
        .sum()
        .dropna()
    )
    return ts


def limit_training_series(y: pd.Series, max_samples: int = 5000) -> pd.Series:
    """Begrenser treningsdatasettet til de siste max_samples punktene om det er for stort."""
    if len(y) > max_samples:
        st.error(
            f"Treningsdatasettet er for stort ({len(y)} punkter). "
            f"Begrens perioden eller bruk færre data. Grensen er {max_samples} punkter."
        )
        st.stop()
    return y


def fit_sarimax(y_train: pd.Series, order: tuple, seasonal_order: tuple):
    """Tren en SARIMAX-modell med robuste default-innstillinger."""
    model = SARIMAX(
        y_train,
        order=order,
        seasonal_order=seasonal_order,
        enforce_stationarity=False,
        enforce_invertibility=False,
        simple_differencing=True,
        use_exact_diffuse=False,
    )
    result = model.fit(
        disp=False,
        method="lbfgs",
        maxiter=200,
    )
    return result


# ==============================================================
#  HOVEDSIDE
# ==============================================================

def show():

    st.title("📈 SARIMAX-forecast for energiproduksjon / -forbruk")

    st.warning(
        """
        **Stabilitetsbegrensninger i denne appen:**
        - Maks **5000 treningspunkter** per modell
        - Summen **p+q+P+Q ≤ 10**
        - Maks sesonglengde: **168 timer**
        - Anbefalt treningsperiode: **30–60 dager**
        """
    )

    st.info(
        """
        ## 🔍 Hvordan bruke forecasting på en enkel og riktig måte

        ### 1️⃣ Velg en fornuftig treningsperiode  
        **Anbefaling:** de siste **30–60 dagene**.  
        Store datasett øker beregningstid og risiko for krasj.

        ### 2️⃣ Velg korrekt sesonglengde  
        Typisk:
        - **24 timer (døgn)**  
        - **168 timer (uke)**  

        ### 3️⃣ Bruk enkel modell først  
        **Start her:**  
        - p=1, d=0, q=1  
        - P=0, D=0, Q=0  
        - s=24

        Du kan alltid gjøre modellen mer kompleks senere, men start enkelt.
        """
    )

    # ------------------------------------------------------------
    # Hent data og velg prisområde / energitype
    # ------------------------------------------------------------
    df_raw = load_elhub_data()

    if df_raw.empty:
        st.error("Ingen data tilgjengelig fra Elhub.")
        return

    if "price_area" not in df_raw.columns:
        st.error("Kolonnen 'price_area' mangler i Elhub-data.")
        return

    areas = sorted(df_raw["price_area"].dropna().unique())

    col_top1, col_top2 = st.columns(2)
    with col_top1:
        price_area = st.selectbox("Velg prisområde", options=areas, index=0)

        energy_choice_label = st.selectbox(
            "Velg energitype for forecasting",
            options=[
                "Produksjon",
                "Forbruk",
                "Begge (produksjon + forbruk + nettolast)",
            ],
            index=0,
        )

        # Mappe til interne koder
        if energy_choice_label.startswith("Produksjon"):
            energy_mode = "production"
        elif energy_choice_label.startswith("Forbruk"):
            energy_mode = "consumption"
        else:
            energy_mode = "both"

    with st.expander("ℹ️ Hva betyr nettolast?"):
        st.markdown(
            """
            **Nettolast** beskriver hvor mye kraftsystemet må levere netto, og beregnes som:

            \\[
            \\text{nettolast} = \\text{forbruk} - \\text{produksjon}
            \\]

            - Når nettolast er **positiv** → forbruket er større enn produksjonen  
              → behov for import / ekstra produksjon  
            - Når nettolast er **negativ** → produksjonen er større enn forbruket  
              → potensielt overskudd i området

            I denne appen plottes nettolast som en ekstra linje når du velger
            **“Begge (produksjon + forbruk + nettolast)”**, og vises også i hover-informasjonen.
            """
        )

    # ------------------------------------------------------------
    # Treningsperiode
    # ------------------------------------------------------------
    # Vi trenger først en "referanseserie" for å finne min/max-dato
    ref_series = prepare_series(df_raw, price_area, source=None)
    if ref_series.empty:
        st.error("Ingen energidata tilgjengelig for valgt prisområde.")
        return

    min_date = ref_series.index.min().date()
    max_date = ref_series.index.max().date()

    with col_top2:
        st.write("### ⏱ Tidsvalg")
        default_start = max_date - timedelta(days=30)
        train_start, train_end = st.date_input(
            "Treningsperiode (fra–til)",
            value=(default_start, max_date),
            min_value=min_date,
            max_value=max_date,
        )

        horizon_hours = st.number_input(
            "Forecast horisont (timer)",
            min_value=1,
            max_value=24 * 30,
            value=24,
            step=1,
        )

    # ------------------------------------------------------------
    # SARIMAX-parametere
    # ------------------------------------------------------------
    st.markdown("### 🔢 SARIMAX-parametere")

    with st.expander("Konfigurer SARIMAX-modellen"):

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            p = st.number_input("p (AR)", min_value=0, max_value=5, value=1)
        with c2:
            d = st.number_input("d (diff)", min_value=0, max_value=2, value=0)
        with c3:
            q = st.number_input("q (MA)", min_value=0, max_value=5, value=1)
        with c4:
            seasonal_period = st.number_input(
                "Sesonglengde s (timer)",
                min_value=0,
                max_value=168,
                value=24,
                help="Typisk 24 (døgn) eller 168 (uke). 0 betyr ingen sesongkomponent."
            )

        c5, c6, c7 = st.columns(3)
        with c5:
            P = st.number_input("P (sesong-AR)", min_value=0, max_value=3, value=0)
        with c6:
            D = st.number_input("D (sesong-diff)", min_value=0, max_value=2, value=0)
        with c7:
            Q = st.number_input("Q (sesong-MA)", min_value=0, max_value=3, value=0)

    if (p + q + P + Q) > 10:
        st.error("Summen av p+q+P+Q må være ≤ 10. Reduser noen av parametrene.")
        st.stop()

    if seasonal_period > 168:
        st.error("Sesonglengden s kan ikke være større enn 168 timer.")
        st.stop()

    order = (p, d, q)
    seasonal_order = (P, D, Q, seasonal_period) if seasonal_period > 0 else (0, 0, 0, 0)

    # ------------------------------------------------------------
    # Kjør modell
    # ------------------------------------------------------------
    st.markdown("### 🤖 Kjør modell")

    if st.button("Tren SARIMAX og lag forecast"):
        with st.spinner("Trener modell og lager forecast ..."):

            try:
                # ------------------------------------------------
                # CASE 1 & 2: kun produksjon ELLER kun forbruk
                # ------------------------------------------------
                if energy_mode in ("production", "consumption"):

                    y = prepare_series(df_raw, price_area, source=energy_mode)
                    if y.empty:
                        st.error(f"Ingen data for valgt energitype ({energy_mode}) i dette prisområdet.")
                        return

                    y_train = y[(y.index.date >= train_start) & (y.index.date <= train_end)]
                    if y_train.empty:
                        st.error("Ingen data i valgt treningsperiode.")
                        return

                    y_train = limit_training_series(y_train, max_samples=5000)

                    result = fit_sarimax(y_train, order=order, seasonal_order=seasonal_order)

                    # Forecast-tidspunkter
                    future_index = pd.date_range(
                        start=y_train.index[-1] + timedelta(hours=1),
                        periods=horizon_hours,
                        freq="H",
                    )

                    forecast_res = result.get_forecast(steps=horizon_hours)
                    forecast_mean = forecast_res.predicted_mean
                    forecast_ci = forecast_res.conf_int()

                    # Plot
                    st.markdown("### 📊 Forecast-resultat")

                    hist_horizon = 24 * 7
                    y_hist = y_train[-hist_horizon:]

                    fig = go.Figure()

                    label_hist = "Historisk produksjon" if energy_mode == "production" else "Historisk forbruk"
                    label_fc = "Forecast produksjon" if energy_mode == "production" else "Forecast forbruk"

                    fig.add_trace(go.Scatter(
                        x=y_hist.index,
                        y=y_hist.values,
                        mode="lines",
                        name=label_hist,
                        line=dict(color="black")
                    ))

                    fig.add_trace(go.Scatter(
                        x=forecast_mean.index,
                        y=forecast_mean.values,
                        mode="lines",
                        name=label_fc,
                        line=dict(color="blue")
                    ))

                    fig.add_trace(go.Scatter(
                        x=forecast_mean.index.tolist() + forecast_mean.index[::-1].tolist(),
                        y=forecast_ci.iloc[:, 0].tolist() + forecast_ci.iloc[:, 1][::-1].tolist(),
                        fill="toself",
                        fillcolor="rgba(0, 0, 255, 0.15)",
                        line=dict(color="rgba(0,0,0,0)"),
                        name="Konfidensintervall",
                    ))

                    fig.update_layout(
                        height=500,
                        hovermode="x unified",
                        title=f"SARIMAX-forecast for {energy_choice_label} – {price_area}",
                        xaxis_title="Tid",
                        yaxis_title="kWh",
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    with st.expander("📄 Modellinfo (summary)"):
                        st.text(result.summary())

                # ------------------------------------------------
                # CASE 3: begge – produksjon + forbruk + nettolast
                # ------------------------------------------------
                elif energy_mode == "both":
                    y_prod = prepare_series(df_raw, price_area, source="production")
                    y_cons = prepare_series(df_raw, price_area, source="consumption")

                    if y_prod.empty or y_cons.empty:
                        st.error("Mangler enten produksjons- eller forbruksdata i dette området.")
                        return

                    # Sørg for felles tidsakse
                    common_index = y_prod.index.intersection(y_cons.index)
                    if common_index.empty:
                        st.error("Fant ingen felles tidsstempler mellom produksjon og forbruk.")
                        return

                    y_prod = y_prod.reindex(common_index)
                    y_cons = y_cons.reindex(common_index)

                    # Filtrer på treningsperiode
                    mask = (common_index.date >= train_start) & (common_index.date <= train_end)
                    common_index_train = common_index[mask]

                    y_prod_train = y_prod.reindex(common_index_train)
                    y_cons_train = y_cons.reindex(common_index_train)

                    if y_prod_train.empty or y_cons_train.empty:
                        st.error("Ingen overlappende produksjons-/forbruksdata i valgt treningsperiode.")
                        return

                    # Begrens størrelse
                    y_prod_train = limit_training_series(y_prod_train, max_samples=5000)
                    y_cons_train = limit_training_series(y_cons_train, max_samples=5000)

                    # Tren to modeller
                    result_prod = fit_sarimax(y_prod_train, order=order, seasonal_order=seasonal_order)
                    result_cons = fit_sarimax(y_cons_train, order=order, seasonal_order=seasonal_order)

                    # Forecast-tidspunkter (bruk felles slutt)
                    last_time = common_index_train[-1]
                    future_index = pd.date_range(
                        start=last_time + timedelta(hours=1),
                        periods=horizon_hours,
                        freq="H",
                    )

                    fc_prod_res = result_prod.get_forecast(steps=horizon_hours)
                    fc_cons_res = result_cons.get_forecast(steps=horizon_hours)

                    fc_prod_mean = fc_prod_res.predicted_mean
                    fc_cons_mean = fc_cons_res.predicted_mean

                    fc_prod_ci = fc_prod_res.conf_int()
                    fc_cons_ci = fc_cons_res.conf_int()

                    # Nettolast: forbruk - produksjon
                    net_hist = y_cons_train - y_prod_train
                    net_fc = fc_cons_mean - fc_prod_mean

                    # Plot
                    st.markdown("### 📊 Forecast-resultat – produksjon, forbruk og nettolast")

                    hist_horizon = 24 * 7
                    y_prod_hist = y_prod_train[-hist_horizon:]
                    y_cons_hist = y_cons_train[-hist_horizon:]
                    net_hist = net_hist[-hist_horizon:]

                    fig = go.Figure()

                    # Historikk
                    fig.add_trace(go.Scatter(
                        x=y_prod_hist.index,
                        y=y_prod_hist.values,
                        mode="lines",
                        name="Historisk produksjon",
                        line=dict(color="green")
                    ))
                    fig.add_trace(go.Scatter(
                        x=y_cons_hist.index,
                        y=y_cons_hist.values,
                        mode="lines",
                        name="Historisk forbruk",
                        line=dict(color="red")
                    ))
                    fig.add_trace(go.Scatter(
                        x=net_hist.index,
                        y=net_hist.values,
                        mode="lines+markers",
                        name="Historisk nettolast (forbruk − produksjon)",
                        line=dict(color="gray", dash="dot"),
                        opacity=0.7
                    ))

                    # Forecast-linjer
                    fig.add_trace(go.Scatter(
                        x=fc_prod_mean.index,
                        y=fc_prod_mean.values,
                        mode="lines",
                        name="Forecast produksjon",
                        line=dict(color="green", dash="dash")
                    ))
                    fig.add_trace(go.Scatter(
                        x=fc_cons_mean.index,
                        y=fc_cons_mean.values,
                        mode="lines",
                        name="Forecast forbruk",
                        line=dict(color="red", dash="dash")
                    ))
                    fig.add_trace(go.Scatter(
                        x=net_fc.index,
                        y=net_fc.values,
                        mode="lines+markers",
                        name="Forecast nettolast (forbruk − produksjon)",
                        line=dict(color="gray", dash="dashdot"),
                        opacity=0.9
                    ))

                    # Konfidensintervall for produksjon
                    fig.add_trace(go.Scatter(
                        x=fc_prod_mean.index.tolist() + fc_prod_mean.index[::-1].tolist(),
                        y=fc_prod_ci.iloc[:, 0].tolist() + fc_prod_ci.iloc[:, 1][::-1].tolist(),
                        fill="toself",
                        fillcolor="rgba(0, 128, 0, 0.12)",
                        line=dict(color="rgba(0,0,0,0)"),
                        name="Konfidensintervall produksjon",
                        showlegend=True,
                    ))

                    # Konfidensintervall for forbruk
                    fig.add_trace(go.Scatter(
                        x=fc_cons_mean.index.tolist() + fc_cons_mean.index[::-1].tolist(),
                        y=fc_cons_ci.iloc[:, 0].tolist() + fc_cons_ci.iloc[:, 1][::-1].tolist(),
                        fill="toself",
                        fillcolor="rgba(255, 0, 0, 0.12)",
                        line=dict(color="rgba(0,0,0,0)"),
                        name="Konfidensintervall forbruk",
                        showlegend=True,
                    ))

                    fig.update_layout(
                        height=550,
                        hovermode="x unified",
                        title=f"SARIMAX-forecast – produksjon, forbruk og nettolast – {price_area}",
                        xaxis_title="Tid",
                        yaxis_title="kWh",
                        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                                    xanchor="center", x=0.5),
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    with st.expander("📄 Modellinfo (summary) – produksjon"):
                        st.text(result_prod.summary())

                    with st.expander("📄 Modellinfo (summary) – forbruk"):
                        st.text(result_cons.summary())

            except Exception as e:
                st.error(f"Feil under modelltrening eller forecasting: {e}")
