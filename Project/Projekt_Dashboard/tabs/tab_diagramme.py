import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import seaborn as sns

def render_diagramme(plot_df, selected_year):
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
            
            # DYNAMISCHE BESTIMMUNG DES ZIELJAHRES (Korrigiert für "Alle")
            if selected_year in ["Alle", "Alle Jahre"]:
                # Schaltjahre filtern für die fiktive Standardachse (2023)
                df_seasonal = df_seasonal[~((df_seasonal['CRASH DATE'].dt.month == 2) & (df_seasonal['CRASH DATE'].dt.day == 29))]
                ziel_jahr = "2023"  # Nutzt 2023 als fiktive X-Achse, um alle Jahre übereinanderzulegen
            else:
                ziel_jahr = str(int(selected_year))
            
            df_seasonal['MONAT_NUM'] = df_seasonal['CRASH DATE'].dt.month
            df_seasonal['TAG_NUM'] = df_seasonal['CRASH DATE'].dt.day
            
            seasonal_counts = df_seasonal.groupby(['MONAT_NUM', 'TAG_NUM']).size().reset_index(name='Anzahl Unfälle')
            
            # Zeitachse bauen 
            seasonal_counts['Anzeige_Datum'] = pd.to_datetime(
                seasonal_counts['MONAT_NUM'].astype(str) + '-' + seasonal_counts['TAG_NUM'].astype(str) + '-' + ziel_jahr, 
                errors='coerce'
            )
            seasonal_counts = seasonal_counts.dropna(subset=['Anzeige_Datum']).sort_values('Anzeige_Datum')
            
            monatsnamen_de = {
                1: "Januar", 2: "Februar", 3: "März", 4: "April", 5: "Mai", 6: "Juni",
                7: "Juli", 8: "August", 9: "September", 10: "Oktober", 11: "November", 12: "Dezember"
            }
            
            # Tooltip-Formatierung anpassen
            if selected_year in ["Alle", "Alle Jahre"]:
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


    ##### LANGFRISTIGER TREND ÜBER DIE JAHRE (Taucht nur auf bei "Alle")
        if selected_year in ["Alle", "Alle Jahre"]:
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