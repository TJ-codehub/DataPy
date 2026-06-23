import streamlit as st
import time

def render_ml_prediction(df):
    st.title("🧠 Machine Learning Prediction")
    
    # Session State zur Speicherung des Trainings-Status
    if 'model_trained' not in st.session_state:
        st.session_state.model_trained = False
        st.session_state.last_model = None

    sub_tab1, sub_tab2 = st.tabs(["Training & Evaluation", "Vorhersage"])

    with sub_tab1:
        st.subheader("Training & Evaluation")
        
        col1, col2 = st.columns(2)
        with col1:
            model_type = st.selectbox("Wähle ein Modell:", 
                                      ["Random Forest", "Decision Tree", "Linear Regression"])
        with col2:
            split_size = st.slider("Train/Test Split (%):", 60, 90, 80)
            
        if st.button("Start Training"):
            with st.spinner(f"Trainiere {model_type} mit {split_size}% Trainingsdaten..."):
                # Simulation des Trainingsprozesses
                time.sleep(2) 
                st.session_state.model_trained = True
                st.session_state.last_model = model_type
                st.success(f"Modell '{model_type}' erfolgreich trainiert!")
                st.info("Performance Metrik: Accuracy 87.4% (Simuliert)")

    with sub_tab2:
        st.subheader("Vorhersage")
        
        if not st.session_state.model_trained:
            st.warning("Bitte trainiere zuerst ein Modell im 'Training & Evaluation' Tab!")
        else:
            st.write(f"Aktives Modell: **{st.session_state.last_model}**")
            
            # Eingabefelder für eine "Unfall"-Vorhersage
            st.markdown("Gib die Parameter für den Unfall ein:")
            c1, c2 = st.columns(2)
            with c1:
                hour = st.number_input("Stunde (0-23):", 0, 23, 12)
                borough = st.selectbox("Stadtteil:", ["MANHATTAN", "BROOKLYN", "QUEENS", "BRONX", "STATEN ISLAND"])
            with c2:
                injuries = st.number_input("Erwartete Verletzte:", 0, 10, 0)
                
            if st.button("Vorhersage starten"):
                with st.spinner("Analysiere Daten..."):
                    time.sleep(1)
                    # Zufälliges Ergebnis simulieren
                    result = "Hohes Risiko" if injuries > 2 else "Geringes Risiko"
                    st.success(f"Ergebnis der Vorhersage: **{result}**")