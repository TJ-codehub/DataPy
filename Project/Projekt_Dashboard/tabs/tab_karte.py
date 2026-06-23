import streamlit as st
import plotly.express as px
import pandas as pd

def render_karte(plot_df):
    if 'LATITUDE' in plot_df.columns and 'LONGITUDE' in plot_df.columns:
        # Daten bereinigen & Kopie erstellen (ungültige GPS-Daten entfernen)
        map_data = plot_df.dropna(subset=['LATITUDE', 'LONGITUDE']).copy()
        map_data = map_data.rename(columns={'LATITUDE': 'latitude', 'LONGITUDE': 'longitude'})
        
        if not map_data.empty:
            # Dynamische Erkennung der Spaltennamen für Verletzte/Getötete
            inj_col = 'NUMBER OF PERSONS INJURED' if 'NUMBER OF PERSONS INJURED' in map_data.columns else ('NUMBER OF PEOPLE INJURED' if 'NUMBER OF PEOPLE INJURED' in map_data.columns else None)
            kil_col = 'NUMBER OF PERSONS KILLED' if 'NUMBER OF PERSONS KILLED' in map_data.columns else ('NUMBER OF PEOPLE KILLED' if 'NUMBER OF PEOPLE KILLED' in map_data.columns else None)
            
            if inj_col and kil_col:
                # Summe der Betroffenen direkt berechnen
                map_data['BETROFFENE'] = map_data[inj_col].fillna(0) + map_data[kil_col].fillna(0)
                
                # 1. EINDEUTIGE TEXT-KATEGORIEN ERSTELLEN
                map_data['Schweregrad'] = map_data['BETROFFENE'].apply(
                    lambda val: "Unfall mit Personenschaden" if val >= 1 else "Nur Sachschaden (0 Verletzte/Getötete)"
                )
                
                # 2. DATUM FORMATIEREN
                if 'CRASH DATE' in map_data.columns:
                    datum_series = map_data['CRASH DATE'].dt.strftime('%d.%m.%Y')
                else:
                    datum_series = "Unbekannt"
                    
                # 3. UHRZEIT AUS 'CRASH HOUR' GENERIEREN
                if 'CRASH HOUR' in map_data.columns:
                    # Werte sichern, in Ganzzahl konvertieren und Format 'HH:00 Uhr' bauen
                    time_series = map_data['CRASH HOUR'].dropna().astype(int).astype(str) + ":00 Uhr"
                    # Fehlende Werte wieder mit dem ursprünglichen Index abgleichen
                    time_series = time_series.reindex(map_data.index, fill_value="Unbekannte Uhrzeit")
                else:
                    time_series = "Unbekannte Uhrzeit"
                
                # 🏙️ 4. STADTTEIL (BOROUGH) EXTRAHIEREN
                if 'BOROUGH' in map_data.columns:
                    borough_series = map_data['BOROUGH'].fillna('Unbekannt').astype(str)
                else:
                    borough_series = "Unbekannt"
                
                # Popup HTML-Text (Tooltip) zusammenbauen (Borough unter der Uhrzeit)
                map_data['unfall_info'] = (
                    "<b>Datum:</b> " + datum_series + "<br>" +
                    "<b>Uhrzeit:</b> ca. " + time_series + "<br>" +
                    "<b>Stadtteil:</b> " + borough_series + "<br>" +
                    "───────────────────────────<br>" +
                    "<b>Personen verletzt:</b> " + map_data[inj_col].fillna(0).astype(int).astype(str) + "<br>" +
                    "<b>Personen getötet:</b> " + map_data[kil_col].fillna(0).astype(int).astype(str)
                )
                
                # 5. SORTIEREN: Cyan (Sachschaden) nach unten, Rot (Personenschaden) nach oben
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
                    height=700,
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
                
                # Karte direkt ausgeben
                st.plotly_chart(fig_map, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': True})
                
                # Zählen und Anzeigen der Kategorien für die KPIs darunter
                stats = map_data['Schweregrad'].value_counts()
                anzahl_sach = stats.get("Nur Sachschaden (0 Verletzte/Getötete)", 0)
                anzahl_pers = stats.get("Unfall mit Personenschaden", 0)
                
                stat_col1, stat_col2 = st.columns(2)
                with stat_col1:
                    st.metric(label="Nur Sachschaden (Cyan)", value=f"{anzahl_sach:,}")
                with stat_col2:
                    st.metric(label="Mit Personenschaden (Rot)", value=f"{anzahl_pers:,}")
        else:
            st.info("Keine Unfälle entsprechen den aktuell gewählten globalen Filterkriterien.")
    else:
        st.warning("GPS-Spalten (LATITUDE/LONGITUDE) fehlen im Datensatz.")