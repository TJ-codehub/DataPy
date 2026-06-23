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
        # Kopie der Daten ziehen
        df_vehicles = plot_df[vorhandene_cols].copy()
        
        # Bereinigung: Alles in Großbuchstaben umwandeln und Whitespaces entfernen
        for col in vorhandene_cols:
            df_vehicles[col] = df_vehicles[col].astype(str).str.strip().str.upper()
            
        ungueltige_werte = ['UNSPECIFIED', 'UNKNOWN', 'NAN', '<NA>', 'NAT', 'NONE', '']
        
        # Kombinationen (Paare) über alle Spalten hinweg pro Zeile sammeln
        alle_paarungen = []
        
        # Effiziente Schleife über die Zeilen (als Liste von Listen für maximale Performance)
        for row in df_vehicles.values.tolist():
            # Nur echte, gültige Fahrzeugtypen filtern
            gueltige_fahrzeuge = [v for v in row if v not in ungueltige_werte and pd.notna(v)]
            
            # Wenn mindestens 2 Fahrzeuge beteiligt waren, bilden wir Paare
            if len(gueltige_fahrzeuge) >= 2:
                # itertools.combinations baut automatisch alle Paare, z.B. bei 3 Autos: (A,B), (A,C), (B,C)
                for paar in itertools.combinations(gueltige_fahrzeuge, 2):
                    # Sortieren, damit "SEDAN + SUV" das gleiche ist wie "SUV + SEDAN" (Unabhängig von der Reihenfolge)
                    alle_paarungen.append(sorted(paar))
        
        if not alle_paarungen:
            st.warning("Keine ausreichenden Fahrzeug-Kombinationen im aktuellen Filter/Sample gefunden.")
            return
            
        # DataFrame aus allen gefundenen Paaren erstellen
        df_paare = pd.DataFrame(alle_paarungen, columns=['Fahrzeug_A', 'Fahrzeug_B'])
        
        # Die Top 10 der am häufigsten vorkommenden Fahrzeugtypen ermitteln (für eine übersichtliche Matrix)
        top_10_typen = pd.concat([df_paare['Fahrzeug_A'], df_paare['Fahrzeug_B']]).value_counts().head(15).index.tolist()
        
        # Nur Paarungen behalten, bei denen beide Fahrzeuge zu den Top 10 gehören
        df_paare_filtered = df_paare[
            df_paare['Fahrzeug_A'].isin(top_10_typen) & 
            df_paare['Fahrzeug_B'].isin(top_10_typen)
        ]
        
        # Symmetrische Matrix mit Nullen vorbereiten
        matrix = pd.DataFrame(0, index=top_10_typen, columns=top_10_typen)
        
        # Häufigkeiten zählen und in die Matrix eintragen
        counts = df_paare_filtered.groupby(['Fahrzeug_A', 'Fahrzeug_B']).size().reset_index(name='Anzahl')
        for _, row in counts.iterrows():
            v1, v2, anzahl = row['Fahrzeug_A'], row['Fahrzeug_B'], row['Anzahl']
            matrix.loc[v1, v2] += anzahl
            if v1 != v2:
                matrix.loc[v2, v1] += anzahl # Symmetrisch spiegeln für bessere Lesbarkeit
                
        # --- PLOT ERSTELLEN (TRANSPARENT) ---
        fig, ax = plt.subplots(figsize=(10, 8), facecolor='none')
        ax.set_facecolor('none')
        
        # Heatmap zeichnen (YlOrRd = Yellow-Orange-Red passt gut auf dunklen Hintergrund)
        sns.heatmap(matrix, annot=True, fmt="d", cmap="YlOrRd", linewidths=0.5, ax=ax)
        
        # Design anpassen (Schriftfarben weiß für dein Theme)
        ax.tick_params(colors='white')
        plt.setp(ax.get_xticklabels(), color="white", rotation=45, ha='right')
        plt.setp(ax.get_yticklabels(), color="white")
        
        # Anzeigen im Streamlit
        st.pyplot(fig, transparent=True)
        
        st.info("💡 **Interpretationshilfe:** Die Diagonale (z. B. SEDAN vs. SEDAN) zeigt Unfälle, bei denen zwei Fahrzeuge des exakt selben Typs kollidiert sind. Sehr hohe Werte (wie Sedan vs. SUV) liegen natürlich auch daran, dass diese beiden Fahrzeugklassen generell am häufigsten in NYC unterwegs sind.")

    else:
        st.warning("Die Fahrzeug-Spalten wurden im Datensatz nicht gefunden.")