import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import itertools

def render_fahrzeug_kombinationen(plot_df):
    st.subheader("🤝 Fahrzeug-Kombinationen bei Unfällen")
    st.markdown("Welche Fahrzeugtypen kollidieren am häufigsten miteinander? Diese Heatmap analysiert alle 5 Fahrzeug-Spalten und zeigt, welche Kombinationen am häufigsten gemeinsam in einen Unfall verwickelt sind.")

    # Alle 5 relevanten Fahrzeug-Spalten definieren
    v_cols = [
        'VEHICLE TYPE CODE 1', 'VEHICLE TYPE CODE 2', 
        'VEHICLE TYPE CODE 3', 'VEHICLE TYPE CODE 4', 
        'VEHICLE TYPE CODE 5'
    ]
    
    # Prüfen, ob die Spalten existieren
    vorhandene_cols = [c for c in v_cols if c in plot_df.columns]
    
    if len(vorhandene_cols) >= 2:
        # Direkter Zugriff auf die Spalten (kein inline .str.upper() oder .strip() mehr nötig)
        df_vehicles = plot_df[vorhandene_cols]
        
        alle_paarungen = []
        
        # Schleife über die Zeilen als Liste für maximale Performance
        for row in df_vehicles.values.tolist():
            # Da die Daten bereits sauber sind, filtern wir nur noch echte fehlende Werte (NaN/None) heraus
            gueltige_fahrzeuge = [v for v in row if pd.notna(v) and v != '']
            
            # Wenn mindestens 2 Fahrzeuge beteiligt waren, bilden wir Paare
            if len(gueltige_fahrzeuge) >= 2:
                for paar in itertools.combinations(gueltige_fahrzeuge, 2):
                    # Sortieren für die Symmetrie (SEDAN+SUV == SUV+SEDAN)
                    alle_paarungen.append(sorted(paar))
        
        if not alle_paarungen:
            st.warning("Keine ausreichenden Fahrzeug-Kombinationen im aktuellen Filter/Sample gefunden.")
            return
            
        # DataFrame aus allen gefundenen Paaren erstellen
        df_paare = pd.DataFrame(alle_paarungen, columns=['Fahrzeug_A', 'Fahrzeug_B'])
        
        # Alle einzigartigen Fahrzeugtypen aus den Paaren für das Multiselect ermitteln
        alle_verfuegbaren_typen = sorted(list(set(df_paare['Fahrzeug_A'].unique()) | set(df_paare['Fahrzeug_B'].unique())))
        
        # Die Top 10 für die Standard-Vorauswahl bestimmen
        top_10_default = pd.concat([df_paare['Fahrzeug_A'], df_paare['Fahrzeug_B']]).value_counts().head(10).index.tolist()
        
        # Multiselect-Box für den User
        ausgewaehlte_typen = st.multiselect(
            "📋 Zu analysierende Fahrzeugtypen auswählen:",
            options=alle_verfuegbaren_typen,
            default=top_10_default,
            help="Füge Fahrzeuge hinzu oder entferne sie, um die Heatmap-Matrix anzupassen."
        )
        
        # Absicherung: Mindestens 2 Typen für die Matrix
        if len(ausgewaehlte_typen) < 2:
            st.warning("⚠️ Bitte wähle mindestens 2 Fahrzeugtypen aus, um die Kombinationen-Matrix anzuzeigen.")
            return

        # Nur Paarungen behalten, bei denen beide Fahrzeuge ausgewählt wurden
        df_paare_filtered = df_paare[
            df_paare['Fahrzeug_A'].isin(ausgewaehlte_typen) & 
            df_paare['Fahrzeug_B'].isin(ausgewaehlte_typen)
        ]
        
        # Symmetrische Matrix mit Nullen vorbereiten
        matrix = pd.DataFrame(0, index=ausgewaehlte_typen, columns=ausgewaehlte_typen)
        
        # Häufigkeiten zählen und eintragen
        counts = df_paare_filtered.groupby(['Fahrzeug_A', 'Fahrzeug_B']).size().reset_index(name='Anzahl')
        for _, row in counts.iterrows():
            v1, v2, anzahl = row['Fahrzeug_A'], row['Fahrzeug_B'], row['Anzahl']
            if v1 in matrix.index and v2 in matrix.columns:
                matrix.loc[v1, v2] += anzahl
                if v1 != v2:
                    matrix.loc[v2, v1] += anzahl
                
        # --- PLOT ERSTELLEN (TRANSPARENT) ---
        fig, ax = plt.subplots(figsize=(10, 8), facecolor='none')
        ax.set_facecolor('none')
        
        sns.heatmap(matrix, annot=True, fmt="d", cmap="YlOrRd", linewidths=0.5, ax=ax)
        
        ax.tick_params(colors='white')
        plt.setp(ax.get_xticklabels(), color="white", rotation=45, ha='right')
        plt.setp(ax.get_yticklabels(), color="white")
        
        st.pyplot(fig, transparent=True)
        
        st.info("💡 **Interpretationshilfe:** Die Diagonale (z. B. SEDAN vs. SEDAN) zeigt Unfälle, bei denen zwei Fahrzeuge des exakt selben Typs kollidiert sind.")

    else:
        st.warning("Die Fahrzeug-Spalten wurden im Datensatz nicht gefunden.")