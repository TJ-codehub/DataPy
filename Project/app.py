# Anaconda promt in verzeichnis öffnen, dann: streamlit run app.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import seaborn as sns

# Seiten-Einstellung für ein breites Dashboard
st.set_page_config(page_title="NYC Collision Analytics", layout="wide")

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


# ==========================================
# 🏢 INHALT FÜR TAB 1: DATENÜBERSICHT
# ==========================================
if st.session_state.aktives_tab == "Datenübersicht":
    st.title("📊 Datenübersicht: NYC Motor Vehicle Collisions")
    
    st.markdown("""
    ### Worum geht es in diesem Datensatz?
    Dieser Datensatz enthält detaillierte Informationen zu allen von der New Yorker Polizeibehörde (NYPD) 
    erfassten Verkehrsunfällen in New York City. Die Daten dienen dazu, Muster im Unfallgeschehen zu erkennen, 
    Gefahrenstellen zu identifizieren und die Sicherheit auf New Yorks Straßen statistisch auszuwerten.
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
    
    st.subheader("💡 Datenvorschau")
    st.markdown("_Hinweis: Here werden Zeilen aus dem Gesamtdatensatz angezeigt, bei denen die wichtigsten Spalten vollständig ausgefüllt sind._")
    
    moegliche_kern_spalten = [
        'CRASH DATE', 'CRASH TIME', 'BOROUGH', 'ZIP CODE', 'LATITUDE', 'LONGITUDE', 
        'NUMBER OF PERSONS INJURED', 'NUMBER OF PERSONS KILLED', 'WEEKDAY', 'CRASH HOUR'
    ]
    kern_spalten = [c for c in moegliche_kern_spalten if c in df.columns]
    
    if len(kern_spalten) > 0:
        vorschau_df = df[df[kern_spalten].notna().all(axis=1)].head(50)
    else:
        vorschau_df = df.head(50)
        
    st.dataframe(vorschau_df, use_container_width=True)


# ==========================================
# 🏢 INHALT FÜR TAB 2: DATA VISUALIZATION
# ==========================================
elif st.session_state.aktives_tab == "Data visualization":
    st.title("🗽 Data Visualization")
    
    # --- OBERER FILTERBEREICH ---
    st.markdown("### 🔍 Daten verfeinern & filtern")
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        jahre_liste = sorted(df['CRASH DATE'].dt.year.dropna().unique().astype(int))
        year_options = ["Alle Jahre"] + [int(j) for j in jahre_liste]
        selected_year = st.selectbox("Jahr filtern:", year_options)
    
    # Filter logisch anwenden, UM DIE DATENMENGE ZU BESTIMMEN
    if selected_year != "Alle Jahre":
        filtered_df = df[df['CRASH DATE'].dt.year == selected_year]
    else:
        filtered_df = df
        
    # 🎯 DYNAMISCHES MAXIMUM BESTIMMEN
    max_zeilen_verfuegbar = len(filtered_df)
    
    with col_f2:
        # Falls keine Daten für ein Jahr da sind, min auf 0 setzen
        sample_size = st.slider(
            "Verwendete Anzahl an Daten (Zeilen) für Diagramme:", 
            min_value=min(1000, max_zeilen_verfuegbar), 
            max_value=max_zeilen_verfuegbar, 
            value=min(20000, max_zeilen_verfuegbar), 
            step=1000
        )
    
    # Zufälliges Sampling für die Performance
    if max_zeilen_verfuegbar > sample_size:
        plot_df = filtered_df.sample(n=sample_size, random_state=42)
    else:
        plot_df = filtered_df
        
    st.info(f"💡 Es werden aktuell {len(plot_df):,} von {max_zeilen_verfuegbar:,} Unfällen verwendet.")
    st.markdown("---")
    
    # --- ERSTELLUNG DER UNTER-TABS ---
    sub_tab1, sub_tab2, sub_tab3, sub_tab4 = st.tabs([
        "📊 Diagramme", 
        "🗺️ Interaktive Karte", 
        "📉 Korrelationsdiagramm", 
        "🔄 Variablen-Vergleich"
    ])
    
    # ------------------------------------------
    # UNTER-TAB 1: DIAGRAMME
    # ------------------------------------------
    with sub_tab1:
        layout_col, _ = st.columns([8, 2])
        
        with layout_col:

        ##### Hauptunfallursachen
            st.markdown("### 📊 Hauptunfallursachen (Contributing Factors)")
            if 'CONTRIBUTING FACTOR VEHICLE 1' in plot_df.columns:
                factor_counts = plot_df[plot_df['CONTRIBUTING FACTOR VEHICLE 1'] != 'UNSPECIFIED']['CONTRIBUTING FACTOR VEHICLE 1'].value_counts().head(20)
                
                fig1 = px.bar(
                    x=factor_counts.index, y=factor_counts.values,
                    labels={'x': 'Ursache', 'y': 'Anzahl der Unfälle'},
                    color_discrete_sequence=['#1f77b4']
                )
                fig1.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'),
                    xaxis=dict(tickangle=-35, automargin=True, title=None),
                    yaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                    margin=dict(l=10, r=10, t=10, b=10)
                )
                st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})
            else:
                st.warning("Spalte für Unfallursachen nicht gefunden.")
                
            st.markdown("---")
            

        ##### Häufigste Fahrzeugtypen
            st.markdown("### 🚗 Beteiligte Fahrzeugtypen (Vehicle Types)")
            v_col = 'VEHICLE TYPE CODE 1' if 'VEHICLE TYPE CODE 1' in plot_df.columns else ('VEHICLE TYPE' if 'VEHICLE TYPE' in plot_df.columns else None)
            
            if v_col and v_col in plot_df.columns:
                vehicle_counts = plot_df[(plot_df[v_col].notna()) & (plot_df[v_col] != 'Unspecified') & (plot_df[v_col] != '')][v_col].value_counts().head(20)
                
                fig3 = px.bar(x=vehicle_counts.index, y=vehicle_counts.values, labels={'x': 'Fahrzeugtyp', 'y': 'Anzahl'}, color_discrete_sequence=['#1f77b4'])
                fig3.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'),
                    xaxis=dict(tickangle=-35, automargin=True, title=None), yaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                    margin=dict(l=10, r=10, t=10, b=10)
                )
                st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})
            else:
                st.warning("Spalte für Fahrzeugtypen (VEHICLE TYPE CODE 1) nicht gefunden.")
                
            st.markdown("---")
            

        ##### Gefahren-Matrix: Wochentag vs. Uhrzeit
            st.markdown("### 📆 Wochentag vs. Uhrzeit")
            if 'WEEKDAY' in plot_df.columns and 'CRASH HOUR' in plot_df.columns:
                wochentage_ordnung = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                heatmap_data = plot_df.groupby(['WEEKDAY', 'CRASH HOUR']).size().unstack(fill_value=0)
                heatmap_data = heatmap_data.reindex(wochentage_ordnung)
                
                fig_heat = px.imshow(
                    heatmap_data,
                    labels=dict(x="Uhrzeit (Stunde)", y="Wochentag", color="Anzahl Unfälle"),
                    x=heatmap_data.columns, y=heatmap_data.index,
                    color_continuous_scale="Viridis"
                )
                fig_heat.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'),
                    xaxis=dict(tickmode='linear', dtick=1),
                    margin=dict(l=10, r=10, t=10, b=10)
                )
                st.plotly_chart(fig_heat, use_container_width=True, config={'displayModeBar': False})

            st.markdown("---")


        ##### Saisonaler Verlauf nach Monaten und Tagen
            st.markdown("### 📈 Saisonaler Unfalltrend im Jahresverlauf")
            if 'CRASH DATE' in plot_df.columns:
                df_seasonal = plot_df.copy()
                
                # Dynamische Bestimmung des Zieljahres für die X-Achse
                if selected_year == "Alle Jahre":
                    # Schaltjahre filtern für die fiktive Standardachse (2023)
                    df_seasonal = df_seasonal[~((df_seasonal['CRASH DATE'].dt.month == 2) & (df_seasonal['CRASH DATE'].dt.day == 29))]
                    ziel_jahr = "2023"
                else:
                    ziel_jahr = str(int(selected_year))
                
                df_seasonal['MONAT_NUM'] = df_seasonal['CRASH DATE'].dt.month
                df_seasonal['TAG_NUM'] = df_seasonal['CRASH DATE'].dt.day
                
                seasonal_counts = df_seasonal.groupby(['MONAT_NUM', 'TAG_NUM']).size().reset_index(name='Anzahl Unfälle')
                
                # Zeitachse bauen (Fiktiv bei "Alle Jahre", Echt bei spezifischem Jahr)
                seasonal_counts['Anzeige_Datum'] = pd.to_datetime(
                    seasonal_counts['MONAT_NUM'].astype(str) + '-' + seasonal_counts['TAG_NUM'].astype(str) + '-' + ziel_jahr, 
                    errors='coerce'
                )
                seasonal_counts = seasonal_counts.dropna(subset=['Anzeige_Datum']).sort_values('Anzeige_Datum')
                
                monatsnamen_de = {
                    1: "Januar", 2: "Februar", 3: "März", 4: "April", 5: "Mai", 6: "Juni",
                    7: "Juli", 8: "August", 9: "September", 10: "Oktober", 11: "November", 12: "Dezember"
                }
                
                # Tooltip-Formatierung anpassen: Jahreszahl nur mitsenden, wenn ein echtes Jahr gefiltert ist
                if selected_year == "Alle Jahre":
                    seasonal_counts['Datum_Schoen'] = seasonal_counts['TAG_NUM'].astype(str) + ". " + seasonal_counts['MONAT_NUM'].map(monatsnamen_de)
                else:
                    seasonal_counts['Datum_Schoen'] = seasonal_counts['TAG_NUM'].astype(str) + ". " + seasonal_counts['MONAT_NUM'].map(monatsnamen_de) + " " + ziel_jahr
                
                seasonal_counts['Glatter_Trend'] = seasonal_counts['Anzahl Unfälle'].ewm(span=20, adjust=False).mean()
                
                fig_line_month = px.bar(
                    seasonal_counts, x='Anzeige_Datum', y='Anzahl Unfälle',
                    custom_data=['Datum_Schoen'],
                    labels={'Anzeige_Datum': 'Datum', 'Anzahl Unfälle': 'Echte Unfälle'},
                    color_discrete_sequence=['rgba(255, 255, 255, 0.12)']
                )
                
                fig_line_month.update_traces(
                    hovertemplate="<b>%{customdata[0]}</b><br>Echte Unfälle: %{y}<extra></extra>",
                    selector=dict(type='bar')
                )
                
                fig_line_month.add_scatter(
                    x=seasonal_counts['Anzeige_Datum'], y=seasonal_counts['Glatter_Trend'],
                    mode='lines', line=dict(color='#1f77b4', width=3, shape='spline'),
                    customdata=seasonal_counts[['Datum_Schoen']],
                    hovertemplate="<b>%{customdata[0]}</b><br>Trend-Mittelwert: %{y:.1f}<extra></extra>",
                    name='Trend-Verlauf'
                )
                
                fig_line_month.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'),
                    showlegend=False,
                    xaxis=dict(tickformat="%B", dtick="M1", gridcolor='rgba(255,255,255,0.1)', title=None),
                    yaxis=dict(gridcolor='rgba(255,255,255,0.1)', title='Anzahl der Unfälle'),
                    margin=dict(l=10, r=10, t=10, b=10)
                )
                st.plotly_chart(fig_line_month, use_container_width=True, config={'displayModeBar': False})
            else:
                st.warning("Spalte 'CRASH DATE' für den Monatsverlauf nicht gefunden.")
                
            st.markdown("---")


        ##### LANGFRISTIGER TREND ÜBER DIE JAHRE (Taucht nur auf bei "Alle Jahre")
            if selected_year == "Alle Jahre":
                st.markdown("### 📈 Langfristiger Unfalltrend im Zeitverlauf (Monatliche Auflösung)")
                if 'CRASH DATE' in plot_df.columns:
                    df_longterm = plot_df.copy()
                    df_longterm['JAHR'] = df_longterm['CRASH DATE'].dt.year
                    df_longterm['MONAT'] = df_longterm['CRASH DATE'].dt.month
                    
                    longterm_counts = df_longterm.groupby(['JAHR', 'MONAT']).size().reset_index(name='Anzahl Unfälle')
                    
                    longterm_counts['Echtes_Datum'] = pd.to_datetime(
                        longterm_counts['JAHR'].astype(str) + '-' + longterm_counts['MONAT'].astype(str) + '-01',
                        errors='coerce'
                    )
                    longterm_counts = longterm_counts.dropna(subset=['Echtes_Datum']).sort_values('Echtes_Datum')
                    
                    longterm_counts['Datum_Schoen'] = longterm_counts['MONAT'].map(monatsnamen_de) + " " + longterm_counts['JAHR'].astype(str)
                    longterm_counts['Glatter_Trend'] = longterm_counts['Anzahl Unfälle'].ewm(span=12, adjust=False).mean()
                    
                    fig_longterm = px.bar(
                        longterm_counts, x='Echtes_Datum', y='Anzahl Unfälle',
                        custom_data=['Datum_Schoen'],
                        labels={'Echtes_Datum': 'Jahr', 'Anzahl Unfälle': 'Unfälle gesamt'},
                        color_discrete_sequence=['rgba(255, 255, 255, 0.12)']
                    )
                    
                    fig_longterm.update_traces(
                        hovertemplate="<b>%{customdata[0]}</b><br>Echte Unfälle: %{y}<extra></extra>",
                        selector=dict(type='bar')
                    )
                    
                    fig_longterm.add_scatter(
                        x=longterm_counts['Echtes_Datum'], y=longterm_counts['Glatter_Trend'],
                        mode='lines', line=dict(color='#1f77b4', width=3, shape='spline'),
                        customdata=longterm_counts[['Datum_Schoen']],
                        hovertemplate="<b>%{customdata[0]}</b><br>Trend-Mittelwert: %{y:.1f}<extra></extra>",
                        name='Langzeit-Trend'
                    )
                    
                    fig_longterm.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'),
                        showlegend=False,
                        xaxis=dict(
                            gridcolor='rgba(255,255,255,0.1)', title=None,
                            dtick="M12",
                            tickformat="%Y"
                        ),
                        yaxis=dict(gridcolor='rgba(255,255,255,0.1)', title='Unfälle pro Monat (Echte Werte)'),
                        margin=dict(l=10, r=10, t=10, b=10)
                    )
                    st.plotly_chart(fig_longterm, use_container_width=True, config={'displayModeBar': False})
                    st.markdown("---")


        ##### Unfälle nach Stadtteilen
            st.markdown("### 🏙️ Verteilung der Unfälle nach Stadtteil (Boroughs)")
            if 'BOROUGH' in plot_df.columns:
                borough_counts = plot_df[plot_df['BOROUGH'].notna() & (plot_df['BOROUGH'] != '')]['BOROUGH'].value_counts()
                
                fig_borough = px.bar(
                    x=borough_counts.index, y=borough_counts.values,
                    labels={'x': 'Stadtteil', 'y': 'Anzahl der Unfälle'},
                    color=borough_counts.index,
                    color_discrete_sequence=px.colors.qualitative.Safe
                )
                fig_borough.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'),
                    xaxis=dict(automargin=True, title=None), yaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                    showlegend=False, margin=dict(l=10, r=10, t=10, b=10)
                )
                st.sidebar.markdown(f"") # Dummy line
                st.plotly_chart(fig_borough, use_container_width=True, config={'displayModeBar': False})
            
            st.markdown("---")
        

        ##### Personenschäden
            st.markdown("### 🩸 Personenschäden im Überblick")
            inj_col = 'NUMBER OF PEOPLE INJURED'
            kil_col = 'NUMBER OF PEOPLE KILLED'

            if inj_col in plot_df.columns and kil_col in plot_df.columns:
                total_injured = int(plot_df[inj_col].sum())
                total_killed = int(plot_df[kil_col].sum())
                
                kpi_col1, kpi_col2, _ = st.columns([3, 3, 4])
                with kpi_col1:
                    st.metric(label="Personen verletzt", value=f"{total_injured:,}")
                with kpi_col2:
                    st.metric(label="Personen getötet", value=f"{total_killed:,}")
                
                injury_data = pd.DataFrame({
                    'Status': ['Verletzt', 'Gestorben'],
                    'Anzahl': [total_injured, total_killed]
                })
                
                fig4 = px.bar(
                    injury_data, x='Status', y='Anzahl', color='Status',
                    color_discrete_map={'Verletzt': '#1f77b4', 'Gestorben': '#d62728'}, 
                    labels={'Status': 'Auswirkung', 'Anzahl': 'Gesamtanzahl'},
                    log_y=True
                )
                fig4.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'),
                    xaxis=dict(automargin=True, title=None), yaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                    showlegend=False, margin=dict(l=10, r=10, t=20, b=10)
                )
                st.plotly_chart(fig4, use_container_width=True, config={'displayModeBar': False})
            else:
                st.warning(f"Spalten '{inj_col}' oder '{kil_col}' wurden im Datensatz nicht gefunden.")

            st.markdown("---")


    # ------------------------------------------
    # UNTER-TAB 2: INTERAKTIVE KARTE
    # ------------------------------------------
    with sub_tab2:
        st.subheader("🗺️ Geografische Verteilung der Unfälle")
        st.markdown("Hier siehst du die exakten Unfallorte in New York City – farblich codiert nach Personenschäden:")
        
        if 'LATITUDE' in plot_df.columns and 'LONGITUDE' in plot_df.columns:
            # Daten bereinigen & Kopie erstellen
            map_data_full = plot_df.dropna(subset=['LATITUDE', 'LONGITUDE']).copy()
            map_data_full = map_data_full.rename(columns={'LATITUDE': 'latitude', 'LONGITUDE': 'longitude'})
            
            if not map_data_full.empty:
                # Dynamische Erkennung der Spaltennamen für Verletzte/Getötete
                inj_col = 'NUMBER OF PERSONS INJURED' if 'NUMBER OF PERSONS INJURED' in map_data_full.columns else ('NUMBER OF PEOPLE INJURED' if 'NUMBER OF PEOPLE INJURED' in map_data_full.columns else None)
                kil_col = 'NUMBER OF PERSONS KILLED' if 'NUMBER OF PERSONS KILLED' in map_data_full.columns else ('NUMBER OF PEOPLE KILLED' if 'NUMBER OF PEOPLE KILLED' in map_data_full.columns else None)
                
                if inj_col and kil_col:
                    max_inj = int(map_data_full[inj_col].max()) if pd.notna(map_data_full[inj_col].max()) else 0
                    max_kil = int(map_data_full[kil_col].max()) if pd.notna(map_data_full[kil_col].max()) else 0
                    
                    st.markdown("#### 🎛️ Filter nach Anzahl der Betroffenen:")
                    
                    # Formular für die Regler, um Live-Lags zu verhindern
                    with st.form("map_filter_form"):
                        col_slide1, col_slide2 = st.columns(2)
                        
                        with col_slide1:
                            filter_inj = st.slider(
                                "Anzahl Personen verletzt:",
                                min_value=0,
                                max_value=max_inj if max_inj > 0 else 1,
                                value=(0, max_inj if max_inj > 0 else 1),
                                step=1
                            )
                            
                        with col_slide2:
                            filter_kil = st.slider(
                                "Anzahl Personen getötet:",
                                min_value=0,
                                max_value=max_kil if max_kil > 0 else 1,
                                value=(0, max_kil if max_kil > 0 else 1),
                                step=1
                            )
                        
                        submit_button = st.form_submit_button("➔ Filter anwenden & Karte laden", type="primary", use_container_width=True)
                    
                    # ZUSTANDS-SPEICHER: Wurde der Button jemals gedrückt?
                    if 'karte_wurde_geladen' not in st.session_state:
                        st.session_state.karte_wurde_geladen = False
                        
                    if submit_button:
                        st.session_state.karte_wurde_geladen = True
                        
                    # Wenn der Button noch NIE gedrückt wurde, brechen wir hier ab und zeigen eine Info
                    if not st.session_state.karte_wurde_geladen:
                        st.info("💡 Bitte stelle die gewünschten Filter ein und klicke auf **'Filter anwenden & Karte laden'**, um die interaktive Karte anzuzeigen.")
                    else:
                        # Daten erst filtern, wenn die Karte explizit angefordert wurde
                        map_data = map_data_full[
                            (map_data_full[inj_col] >= filter_inj[0]) & (map_data_full[inj_col] <= filter_inj[1]) &
                            (map_data_full[kil_col] >= filter_kil[0]) & (map_data_full[kil_col] <= filter_kil[1])
                        ].copy()
                        
                        # Summe der Betroffenen berechnen
                        map_data['BETROFFENE'] = map_data[inj_col].fillna(0) + map_data[kil_col].fillna(0)
                        
                        if not map_data.empty:
                            # 1. EINDEUTIGE TEXT-KATEGORIEN ERSTELLEN
                            map_data['Schweregrad'] = map_data['BETROFFENE'].apply(
                                lambda val: "Unfall mit Personenschaden" if val >= 1 else "Nur Sachschaden (0 Verletzte/Getötete)"
                            )
                            
                            # 2. DATUM FORMATIEREN
                            if 'CRASH DATE' in map_data.columns:
                                datum_series = map_data['CRASH DATE'].dt.strftime('%d.%m.%Y')
                            else:
                                datum_series = "Unbekannt"
                                
                            # 🎯 3. UHRZEIT AUS 'CRASH HOUR' GENERIEREN
                            if 'CRASH HOUR' in map_data.columns:
                                # Werte sichern, in Ganzzahl konvertieren und Format 'HH:00 Uhr' bauen
                                time_series = map_data['CRASH HOUR'].dropna().astype(int).astype(str) + ":00 Uhr"
                                # Fehlende Werte wieder mit dem ursprünglichen Index abgleichen
                                time_series = time_series.reindex(map_data.index, fill_value="Unbekannte Uhrzeit")
                            else:
                                time_series = "Unbekannte Uhrzeit"
                            
                            # Popup HTML-Text zusammenbauen
                            map_data['unfall_info'] = (
                                "<b>Datum:</b> " + datum_series + "<br>" +
                                "<b>Uhrzeit:</b> ca. " + time_series + "<br>" +
                                "───────────────────────────<br>" +
                                "<b>Personen verletzt:</b> " + map_data[inj_col].fillna(0).astype(int).astype(str) + "<br>" +
                                "<b>Personen getötet:</b> " + map_data[kil_col].fillna(0).astype(int).astype(str)
                            )
                            
                            # 4. SORTIEREN: Cyan nach unten, Rot nach oben
                            map_data = map_data.sort_values(by='BETROFFENE', ascending=True)
                            
                            # Plotly Mapbox erstellen
                            fig_map = px.scatter_mapbox(
                                map_data,
                                lat='latitude',
                                lon='longitude',
                                color='Schweregrad',
                                color_discrete_map={
                                    "Nur Sachschaden (0 Verletzte/Getötete)": "#00ffff",
                                    "Unfall mit Personenschaden": "#ff0000"
                                },
                                text='unfall_info',
                                zoom=10
                            )
                            
                            fig_map.update_layout(
                                mapbox_style="carto-darkmatter",
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                showlegend=True,
                                legend=dict(
                                    yanchor="top",
                                    y=0.99,
                                    xanchor="left",
                                    x=0.01,
                                    bgcolor="rgba(0,0,0,0.5)"
                                ),
                                margin=dict(l=0, r=0, t=0, b=0)
                            )
                            
                            fig_map.update_traces(
                                mode='markers',
                                hovertemplate="%{text}<extra></extra>",
                                marker=dict(size=4)
                            )
                            
                            st.plotly_chart(fig_map, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': True})

                            
                            # Zählen der Kategorien
                            stats = map_data['Schweregrad'].value_counts()
                            anzahl_sach = stats.get("Nur Sachschaden (0 Verletzte/Getötete)", 0)
                            anzahl_pers = stats.get("Unfall mit Personenschaden", 0)
                            
                            stat_col1, stat_col2 = st.columns(2)
                            with stat_col1:
                                st.metric(label="Nur Sachschaden (Cyan)", value=f"{anzahl_sach:,}")
                            with stat_col2:
                                st.metric(label="Mit Personenschaden (Rot)", value=f"{anzahl_pers:,}")
                        else:
                            st.info("Keine Unfälle entsprechen den gewählten Filterkriterien der Schieberegler.")
            else:
                st.warning("Keine gültigen GPS-Daten im aktuellen Filter vorhanden.")
        else:
            st.warning("GPS-Spalten (LATITUDE/LONGITUDE) fehlen im Datensatz.")
            

    # ------------------------------------------
    # UNTER-TAB 3: KORRELATIONSDIAGRAMM
    # ------------------------------------------
    with sub_tab3:
        st.subheader("📉 Korrelations-Heatmap (Zusammenhänge)")
        st.markdown("Untersuchung von linearen Beziehungen zwischen den numerischen Werten:")
        
        numeric_cols = plot_df.select_dtypes(include=['number']).columns.tolist()
        cols_to_remove = ['ZIP CODE', 'COLLISION_ID']
        numeric_cols = [c for c in numeric_cols if c not in cols_to_remove]
        
        if len(numeric_cols) > 1:
            corr_matrix = plot_df[numeric_cols].corr()
            fig, ax = plt.subplots(figsize=(8, 5))
            sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt=".2f", linewidths=0.5, ax=ax)
            st.pyplot(fig)
        else:
            st.warning("Nicht genügend numerische Spalten für eine Matrix vorhanden.")
            

    # ------------------------------------------
    # UNTER-TAB 4: VERGLEICHE SEITE
    # ------------------------------------------
    with sub_tab4:
        st.subheader("🔄 Interaktiver Variablen-Vergleich (PointCloud)")
        st.markdown("Wähle zwei beliebige Merkmale aus, um deren Verteilung im direkten Comparison zu analysieren:")
        
        all_numeric = plot_df.select_dtypes(include=['number']).columns.tolist()
        
        if len(all_numeric) >= 2:
            col_sel1, col_sel2 = st.columns(2)
            with col_sel1:
                x_axis = st.selectbox("X-Achse auswählen:", all_numeric, index=all_numeric.index('CRASH HOUR') if 'CRASH HOUR' in all_numeric else 0)
            with col_sel2:
                y_default = 'NUMBER OF PERSONS INJURED' if 'NUMBER OF PERSONS INJURED' in all_numeric else all_numeric[1]
                y_axis = st.selectbox("Y-Achse auswählen:", all_numeric, index=all_numeric.index(y_default))
            
            st.markdown(f"### 📊 Plot: `{y_axis}` im Verhältnis zu `{x_axis}`")
            
            fig, ax = plt.subplots(figsize=(10, 4.5))
            sns.scatterplot(data=plot_df, x=x_axis, y=y_axis, alpha=0.5, color='#1f77b4', ax=ax)
            ax.set_title(f"Vergleich von {x_axis} und {y_axis}")
            ax.grid(True, linestyle='--', alpha=0.5)
            
            st.pyplot(fig)
        else:
            st.warning("Es werden mindestens zwei numerische Spalten für den X-Y-Vergleich benötigt.")