# Anaconda prompt in verzeichnis öffnen, dann: streamlit run app.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import seaborn as sns

from tabs import tab_datenuebersicht
from tabs import tab_diagramme
from tabs import tab_karte
from tabs import tab_ml_prediction
from tabs import tab_fahrzeug_kombinationen

# Seiten-Einstellung für ein breites Dashboard
st.set_page_config(page_title="NYC Collision Analytics", layout="wide")

# --- CALLBACK-FUNKTION ZUM ZURÜCKSETZEN DER VISUALISIERUNGS-FILTER ---
def reset_visualization_filters():
    st.session_state.v_year = "Alle"
    st.session_state.v_month = "Alle"
    st.session_state.v_weekday = "Alle"
    st.session_state.v_hour = "Alle"
    st.session_state.v_borough = "Alle"
    st.session_state.v_factor = "Alle"
    st.session_state.v_injured = 0
    st.session_state.v_killed = 0
    st.session_state.v_vehicles = "Alle"
    if 'v_sample_size' in st.session_state:
        del st.session_state.v_sample_size

# --- 1. DATEN LADEN (MIT CACHING) ---
@st.cache_data
def load_data_from_csv():
    df = pd.read_csv('NYC_Collisions_Clean.csv', parse_dates=['CRASH DATE'], low_memory=False)
    
    # Automatisch alle 'object'-Spalten (Text) in echten 'string'-Datentyp umwandeln
    for col in df.select_dtypes(include=['object']).columns:
        df[col] = df[col].astype("string")
        
    return df

with st.spinner("Lade Daten aus Cache..."):
    df = load_data_from_csv()


# --- 2. ZUSTANDSSPEICHER (SESSION STATE) FÜR BUTTON-NAVIGATION ---
if 'aktives_tab' not in st.session_state:
    st.session_state.aktives_tab = "Datenübersicht"


# --- 3. SEITENLEISTE ---
st.sidebar.title("📌 Pages")

type_daten = "primary" if st.session_state.aktives_tab == "Datenübersicht" else "secondary"
if st.sidebar.button("📊 Datenübersicht", use_container_width=True, type=type_daten):
    st.session_state.aktives_tab = "Datenübersicht"
    st.rerun()

type_diagramme = "primary" if st.session_state.aktives_tab == "Data visualization" else "secondary"
if st.sidebar.button("🗽 Data Visualization", use_container_width=True, type=type_diagramme):
    st.session_state.aktives_tab = "Data visualization"
    st.rerun()

type_ml = "primary" if st.session_state.aktives_tab == "ML Prediction" else "secondary"
if st.sidebar.button("🧠 ML Prediction", use_container_width=True, type=type_ml):
    st.session_state.aktives_tab = "ML Prediction"
    st.rerun()

# =========================================================================
# 🏢 INHALT FÜR TAB 1: DATENÜBERSICHT
# =========================================================================
if st.session_state.aktives_tab == "Datenübersicht":
    tab_datenuebersicht.render_datenuebersicht(df)


# =========================================================================
# 🏢 INHALT FÜR TAB 2: DATA VISUALIZATION (JETZT MIT PROFI-FILTERN)
# =========================================================================
elif st.session_state.aktives_tab == "Data visualization":
    st.title("🗽 Data Visualization & Interaktive Analysen")
    
    # --- NEUER, ERWEITERTER FILTERBEREICH (KOMPLETT DYNAMISCH) ---
    with st.expander("🔍 Filter für Diagramme & Karten konfigurieren", expanded=True):
        
        # Reihe 1: Zeitliche Filter
        col_t1, col_t2, col_t3, col_t4 = st.columns(4)
        
        with col_t1:
            jahre = ["Alle"] + sorted(list(df['CRASH DATE'].dt.year.dropna().unique().astype(int)))
            v_year = st.selectbox("Jahr:", jahre, key='v_year')
            
        with col_t2:
            monate = ["Alle"] + list(range(1, 13))
            v_month = st.selectbox("Monat:", monate, key='v_month')
            
        with col_t3:
            if 'WEEKDAY' in df.columns:
                tage = ["Alle"] + sorted(list(df['WEEKDAY'].dropna().unique()))
            else:
                tage = ["Alle", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            v_weekday = st.selectbox("Wochentag:", tage, key='v_weekday')
            
        with col_t4:
            stunden = ["Alle"] + list(range(0, 24))
            v_hour = st.selectbox("Uhrzeit (Stunde):", stunden, key='v_hour')
            
        # Reihe 2: Ort & Ursache
        col_o1, col_o2 = st.columns(2)
        
        with col_o1:
            if 'BOROUGH' in df.columns:
                stadtteile = ["Alle"] + sorted(list(df['BOROUGH'].dropna().unique()))
            else:
                stadtteile = ["Alle"]
            v_borough = st.selectbox("Stadtteil (Borough):", stadtteile, key='v_borough')
            
        with col_o2:
            factor_col = 'CONTRIBUTING FACTOR VEHICLE 1'
            if factor_col in df.columns:
                valid_factors = df[factor_col].dropna()
                valid_factors = valid_factors[~valid_factors.isin(['Unspecified', 'UNKNOWN', '', 'NaN'])]
                ursachen = ["Alle"] + sorted(list(valid_factors.unique()))
            else:
                ursachen = ["Alle"]
            v_factor = st.selectbox("Haupt-Unfallursache (Factor 1):", ursachen, key='v_factor')
            
        # Reihe 3: Schweregrad & Fahrzeuge
        col_s1, col_s2, col_s3 = st.columns(3)
        
        with col_s1:
            max_inj = int(df['NUMBER OF PERSONS INJURED'].max()) if 'NUMBER OF PERSONS INJURED' in df.columns else 10
            v_injured = st.slider("Mindestens Verletzte Personen:", 0, max_inj, key='v_injured')
            
        with col_s2:
            max_kil = int(df['NUMBER OF PERSONS KILLED'].max()) if 'NUMBER OF PERSONS KILLED' in df.columns else 10
            v_killed = st.slider("Mindestens Getötete Personen:", 0, max_kil, key='v_killed')
            
        with col_s3:
            v_vehicles = st.selectbox("Anzahl beteiligter Fahrzeuge:", ["Alle", "1", "2", "3", "4", "5+"], key='v_vehicles')

        # ---------------------------------------------------------------------
        # LOGISCHE FILTERUNG DIREKT ANWENDEN, UM DAS SLIDER-MAXIMUM ZU BERECHNEN
        # ---------------------------------------------------------------------
        filtered_df = df.copy()
        
        if v_year != "Alle":
            filtered_df = filtered_df[filtered_df['CRASH DATE'].dt.year == int(v_year)]
        if v_month != "Alle":
            filtered_df = filtered_df[filtered_df['CRASH DATE'].dt.month == int(v_month)]
        if v_weekday != "Alle" and 'WEEKDAY' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['WEEKDAY'] == v_weekday]
        if v_hour != "Alle" and 'CRASH HOUR' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['CRASH HOUR'] == int(v_hour)]
        if v_borough != "Alle" and 'BOROUGH' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['BOROUGH'] == v_borough]
        if v_factor != "Alle" and 'CONTRIBUTING FACTOR VEHICLE 1' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['CONTRIBUTING FACTOR VEHICLE 1'] == v_factor]
        if 'NUMBER OF PERSONS INJURED' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['NUMBER OF PERSONS INJURED'] >= v_injured]
        if 'NUMBER OF PERSONS KILLED' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['NUMBER OF PERSONS KILLED'] >= v_killed]
            
        v_cols = ['VEHICLE TYPE CODE 1', 'VEHICLE TYPE CODE 2', 'VEHICLE TYPE CODE 3', 'VEHICLE TYPE CODE 4', 'VEHICLE TYPE CODE 5']
        existierende_v_cols = [c for c in v_cols if c in filtered_df.columns]
        
        if v_vehicles != "Alle" and existierende_v_cols:
            valid_vehicle_count = filtered_df[existierende_v_cols].notna().sum(axis=1)
            for c in existierende_v_cols:
                valid_vehicle_count -= (filtered_df[c].isin(['Unspecified', 'UNKNOWN', ''])).astype(int)
            if v_vehicles == "5+":
                filtered_df = filtered_df[valid_vehicle_count >= 5]
            else:
                filtered_df = filtered_df[valid_vehicle_count == int(v_vehicles)]

        # Dynamisches Maximum bestimmen
        max_zeilen_verfuegbar = len(filtered_df)

        # Reihe 4: Daten-Sampling Slider & Reset Button
        col_r1, col_r2 = st.columns([3, 1])
        
        with col_r1:
            if max_zeilen_verfuegbar == 0:
                st.warning("⚠️ Keine Unfälle mit dieser spezifischen Filter-Kombination gefunden. Bitte lockere die Filter etwas.")
                sample_size = 0
            else:
                # Standardwert im Session State initialisieren (max 20.000 für flüssige Performance)
                if 'v_sample_size' not in st.session_state:
                    st.session_state.v_sample_size = min(20000, max_zeilen_verfuegbar)
                
                # Zwingende Grenzanpassung, damit der State-Wert nie außerhalb des aktuellen Maxiums liegt
                if st.session_state.v_sample_size > max_zeilen_verfuegbar:
                    st.session_state.v_sample_size = max_zeilen_verfuegbar
                if st.session_state.v_sample_size < min(1000, max_zeilen_verfuegbar):
                    st.session_state.v_sample_size = min(1000, max_zeilen_verfuegbar)

                slider_min = min(1000, max_zeilen_verfuegbar)
                slider_max = max_zeilen_verfuegbar
                
                # Falls exakt so wenige Zeilen da sind, dass min == max ist, rendern wir keinen Slider (Fehlerschutz)
                if slider_min == slider_max:
                    st.info(f"💡 Genau {max_zeilen_verfuegbar:,} Unfälle entsprechen deinen Filtern (werden vollständig für Diagramme genutzt).")
                    sample_size = max_zeilen_verfuegbar
                else:
                    # Schrittweite dynamisch anpassen (1000er Schritte nur wenn genug Daten da sind)
                    step_size = 1000 if (slider_max - slider_min) >= 1000 else 1
                    sample_size = st.slider(
                        "Verwendete Anzahl an Daten (Zeilen) für Diagramme (Zufallsstichprobe):", 
                        min_value=slider_min, 
                        max_value=slider_max, 
                        step=step_size,
                        key='v_sample_size'
                    )
        
        with col_r2:
            st.markdown("<div style='padding-top: 28px;'></div>", unsafe_allow_html=True)
            st.button("🔄 Filter zurücksetzen", use_container_width=True, on_click=reset_visualization_filters, key="btn_reset_vis")

    # ---------------------------------------------------------------------
    # SCHLUSSENDLICHES SAMPLING & RENDERING DER SUB-TABS
    # ---------------------------------------------------------------------
    if max_zeilen_verfuegbar > 0:
        # Zufälliges Sampling für die Performance der Diagramme/Karten
        if max_zeilen_verfuegbar > sample_size and sample_size > 0:
            plot_df = filtered_df.sample(n=sample_size, random_state=42)
        else:
            plot_df = filtered_df
            
        st.info(f"📊 Es werden aktuell {len(plot_df):,} von {max_zeilen_verfuegbar:,} gefilterten Unfällen visuell dargestellt.")
        st.markdown("---")
        
        # --- ERSTELLUNG DER UNTER-TABS ---
        sub_tab1, sub_tab2, sub_tab3 = st.tabs([
            "📊 Diagramme", 
            "🗺️ Interaktive Karte",
            "🤝 Fahrzeug-Kombinationen"
        ])
        
        with sub_tab1:
            tab_diagramme.render_diagramme(plot_df, v_year)

        with sub_tab2:
            tab_karte.render_karte(plot_df)

        with sub_tab3:
            tab_fahrzeug_kombinationen.render_fahrzeug_kombinationen(plot_df)


# ==========================================
# 🏢 INHALT FÜR TAB 3: ML Prediction
# ==========================================
if st.session_state.aktives_tab == "ML Prediction":
    tab_ml_prediction.render_ml_prediction(df)