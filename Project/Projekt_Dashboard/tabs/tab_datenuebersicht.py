import streamlit as st
import pandas as pd

# Callback-Funktion zum Zurücksetzen aller Filter
def reset_all_filters():
    st.session_state.f_year = "Alle"
    st.session_state.f_month = "Alle"
    st.session_state.f_weekday = "Alle"
    st.session_state.f_hour = "Alle"
    st.session_state.f_borough = "Alle"
    st.session_state.f_factor = "Alle"
    st.session_state.f_injured = 0
    st.session_state.f_killed = 0
    st.session_state.f_vehicles = "Alle"
    st.session_state.f_max_rows = 50

def render_datenuebersicht(df):
    # NEU: Standardwert für die Zeilenanzahl im Session State vorab definieren,
    # damit wir unten auf das 'value'-Argument im Slider verzichten können.
    if 'f_max_rows' not in st.session_state:
        st.session_state.f_max_rows = 50

    st.title("📊 Datenübersicht: NYC Motor Vehicle Collisions")
    
    st.markdown("""
    ### Worum geht es in diesem Datensatz?
    Der Datensatz enthält Informationen zu allen von der New Yorker Polizeibehörde (NYPD) erfassten Verkehrsunfällen.
    Ein offizieller Unfallbericht muss immer dann ausgefüllt werden, wenn Personen verletzt oder getötet wurden oder ein Sachschaden
    von mindestens 1.000 $ entstanden ist. 
    """)
    
    st.markdown("---")
    
    st.subheader("📋 Datensatz-Informationen (Gesamtdatensatz)")
    kpi1, kpi2 = st.columns(2)
    with kpi1:
        st.metric(label="Gesamtanzahl der erfassten Unfälle", value=f"{len(df):,}")
    with kpi2:
        st.metric(label="Anzahl der Merkmale (Spalten)", value=f"{len(df.columns)}")
        
    st.markdown("---")

    st.subheader("🗂️ Struktur des Datensatzes (Spalten-Details)")
    st.markdown("Die folgende Tabelle zeigt alle Merkmale, ihre Datentypen sowie die Anzahl ausgefüllter und fehlender Werte:")
    
    info_df = pd.DataFrame({
        'Merkmal (Spalte)': df.columns,
        'Datentyp': df.dtypes.astype(str),
        'Ausgefüllte Werte (Non-Null)': df.notna().sum().values,
        'Fehlende Werte (NaN)': df.isna().sum().values
    })
    
    tabelle_hoehe = int((len(info_df) + 1) * 35 + 10)
    
    st.dataframe(
        info_df, 
        use_container_width=False, 
        hide_index=True,
        height=tabelle_hoehe,
        column_config={
            "Merkmal (Spalte)": st.column_config.TextColumn(width="large"),
            "Datentyp": st.column_config.TextColumn(),
            "Ausgefüllte Werte (Non-Null)": st.column_config.NumberColumn(),
            "Fehlende Werte (NaN)": st.column_config.NumberColumn()
        }
    )
            
    st.markdown("---")
    
    # =========================================================================
    # INTERAKTIVE DATENVORSCHAU MIT ERWEITERTEN FILTERN & RESET BUTTON
    # =========================================================================
    st.subheader("💡 Interaktive Datenvorschau & Tiefenanalyse")
    st.markdown("_Nutze die Filter im ausklappbaren Menü, um gezielt nach bestimmten Unfallszenarien zu suchen._")
    
    # Wir starten mit einer Kopie des Datensatzes für die Filterung
    preview_df = df.copy()
    
    # Expander für die Filter-UIs, um Platz zu sparen
    with st.expander("🔍 Filter für die Datenvorschau konfigurieren", expanded=False):
        
        # Reihe 1: Zeitliche Filter
        col_t1, col_t2, col_t3, col_t4 = st.columns(4)
        
        with col_t1:
            jahre = ["Alle"] + sorted(list(preview_df['CRASH DATE'].dt.year.dropna().unique().astype(int)))
            f_year = st.selectbox("Jahr:", jahre, key='f_year')
            
        with col_t2:
            monate = ["Alle"] + list(range(1, 13))
            f_month = st.selectbox("Monat:", monate, key='f_month')
            
        with col_t3:
            if 'WEEKDAY' in preview_df.columns:
                tage = ["Alle"] + sorted(list(preview_df['WEEKDAY'].dropna().unique()))
            else:
                tage = ["Alle", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            f_weekday = st.selectbox("Wochentag:", tage, key='f_weekday')
            
        with col_t4:
            stunden = ["Alle"] + list(range(0, 24))
            f_hour = st.selectbox("Uhrzeit (Stunde):", stunden, key='f_hour')
            
        # Reihe 2: Ort & Ursache
        col_o1, col_o2 = st.columns(2)
        
        with col_o1:
            if 'BOROUGH' in preview_df.columns:
                stadtteile = ["Alle"] + sorted(list(preview_df['BOROUGH'].dropna().unique()))
            else:
                stadtteile = ["Alle"]
            f_borough = st.selectbox("Stadtteil (Borough):", stadtteile, key='f_borough')
            
        with col_o2:
            factor_col = 'CONTRIBUTING FACTOR VEHICLE 1'
            if factor_col in preview_df.columns:
                valid_factors = preview_df[factor_col].dropna()
                valid_factors = valid_factors[~valid_factors.isin(['Unspecified', 'UNKNOWN', '', 'NaN'])]
                ursachen = ["Alle"] + sorted(list(valid_factors.unique()))
            else:
                ursachen = ["Alle"]
            f_factor = st.selectbox("Haupt-Unfallursache (Factor 1):", ursachen, key='f_factor')
            
        # Reihe 3: Schweregrad & Fahrzeuge
        col_s1, col_s2, col_s3 = st.columns(3)
        
        with col_s1:
            max_inj = int(preview_df['NUMBER OF PERSONS INJURED'].max()) if 'NUMBER OF PERSONS INJURED' in preview_df.columns else 10
            # HINWEIS: 'value=0' gelöscht. Der Slider startet automatisch bei min_value (0).
            f_injured = st.slider("Mindestens Verletzte Personen:", 0, max_inj, key='f_injured')
            
        with col_s2:
            max_kil = int(preview_df['NUMBER OF PERSONS KILLED'].max()) if 'NUMBER OF PERSONS KILLED' in preview_df.columns else 10
            # HINWEIS: 'value=0' gelöscht. Der Slider startet automatisch bei min_value (0).
            f_killed = st.slider("Mindestens Getötete Personen:", 0, max_kil, key='f_killed')
            
        with col_s3:
            f_vehicles = st.selectbox("Anzahl beteiligter Fahrzeuge:", ["Alle", "1", "2", "3", "4", "5+"], key='f_vehicles')

        # Reihe 4: Zeilenbegrenzung & Reset-Button via Callback (on_click)
        col_r1, col_r2 = st.columns([3, 1])
        with col_r1:
            # HINWEIS: 'value=50' gelöscht. Der Startwert wird jetzt oben über den Session State geregelt.
            f_max_rows = st.slider("Anzahl anzuzeigender Zeilen in der Vorschau:", 10, 500, step=10, key='f_max_rows')
        with col_r2:
            # HTML-Abstandshalter, damit der Button bündig mit dem Slider abschließt
            st.markdown("<div style='padding-top: 28px;'></div>", unsafe_allow_html=True)
            st.button("🔄 Zurücksetzen", use_container_width=True, on_click=reset_all_filters)

    # =========================================================================
    # LOGIK: FILTER ANWENDEN
    # =========================================================================
    
    # 1. Zeit-Filter
    if f_year != "Alle":
        preview_df = preview_df[preview_df['CRASH DATE'].dt.year == int(f_year)]
    if f_month != "Alle":
        preview_df = preview_df[preview_df['CRASH DATE'].dt.month == int(f_month)]
    if f_weekday != "Alle" and 'WEEKDAY' in preview_df.columns:
        preview_df = preview_df[preview_df['WEEKDAY'] == f_weekday]
    if f_hour != "Alle" and 'CRASH HOUR' in preview_df.columns:
        preview_df = preview_df[preview_df['CRASH HOUR'] == int(f_hour)]
        
    # 2. Ort & Ursache
    if f_borough != "Alle" and 'BOROUGH' in preview_df.columns:
        preview_df = preview_df[preview_df['BOROUGH'] == f_borough]
    if f_factor != "Alle" and 'CONTRIBUTING FACTOR VEHICLE 1' in preview_df.columns:
        preview_df = preview_df[preview_df['CONTRIBUTING FACTOR VEHICLE 1'] == f_factor]
        
    # 3. Schweregrad
    if 'NUMBER OF PERSONS INJURED' in preview_df.columns:
        preview_df = preview_df[preview_df['NUMBER OF PERSONS INJURED'] >= f_injured]
    if 'NUMBER OF PERSONS KILLED' in preview_df.columns:
        preview_df = preview_df[preview_df['NUMBER OF PERSONS KILLED'] >= f_killed]
        
    # 4. Fahrzeuganzahl-Berechnung
    v_cols = ['VEHICLE TYPE CODE 1', 'VEHICLE TYPE CODE 2', 'VEHICLE TYPE CODE 3', 'VEHICLE TYPE CODE 4', 'VEHICLE TYPE CODE 5']
    existierende_v_cols = [c for c in v_cols if c in preview_df.columns]
    
    if f_vehicles != "Alle" and existierende_v_cols:
        valid_vehicle_count = preview_df[existierende_v_cols].notna().sum(axis=1)
        for c in existierende_v_cols:
            valid_vehicle_count -= (preview_df[c].isin(['Unspecified', 'UNKNOWN', ''])).astype(int)
        
        if f_vehicles == "5+":
            preview_df = preview_df[valid_vehicle_count >= 5]
        else:
            preview_df = preview_df[valid_vehicle_count == int(f_vehicles)]

    # =========================================================================
    # ERGEBNIS ANZEIGEN
    # =========================================================================
    gefundene_zeilen = len(preview_df)
    
    if gefundene_zeilen == 0:
        st.warning("⚠️ Keine Unfälle mit dieser spezifischen Filter-Kombination gefunden. Bitte lockere die Filter etwas an.")
    else:
        st.success(f"🎯 Suchergebnis: {gefundene_zeilen:,} Unfälle entsprechen deinen Filtern. Zeige die ersten {min(f_max_rows, gefundene_zeilen)} Einträge:")
        st.dataframe(preview_df.head(f_max_rows), use_container_width=True)