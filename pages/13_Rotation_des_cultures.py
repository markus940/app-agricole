import json
import pandas as pd
import plotly.express as px
import streamlit as st
import database
import theme

st.set_page_config(page_title="Rotation & Pluviométrie", page_icon="🌱", layout="wide")
database.init_db()
theme.apply_custom_theme()

import auth
auth.requiere_connexion()

user_id = st.session_state["user_id"]

with open("cultures.json", "r", encoding="utf-8") as f:
    cultures_db = json.load(f)

st.title("🌱 Rotation des Cultures & Suivi de Pluviométrie")
st.caption("Optimisez l'azote de votre sol grâce à l'assolement et enregistrez les précipitations réelles sur vos parcelles.")

tab_rotation, tab_pluvio = st.tabs(["🌱 Conseiller de Rotation des Cultures", "🌧️ Suivi de Pluviométrie (mm)"])

# --- TAB 1 : CONSEILLER DE ROTATION DES CULTURES ---
with tab_rotation:
    st.subheader("💡 Recommandation d'Assolement & Succession")
    st.write("La rotation des cultures évite l'épuisement des sols et brise le cycle des maladies et ravageurs.")

    col_rot1, col_rot2 = st.columns(2)
    with col_rot1:
        derniere_culture = st.selectbox("Dernière culture récoltée sur la parcelle :", options=sorted(cultures_db.keys()))

    FAMILLES = {
        "riz": "Graminée (Céréale)",
        "maïs": "Graminée (Céréale)",
        "mil": "Graminée (Céréale)",
        "sorgho": "Graminée (Céréale)",
        "arachide": "Légumineuse (Fixatrice d'Azote)",
        "niébé": "Légumineuse (Fixatrice d'Azote)",
        "soja": "Légumineuse (Fixatrice d'Azote)",
        "tomate": "Solanacée (Gourmande en nutriments)",
        "poivron": "Solanacée (Gourmande en nutriments)",
        "aubergine": "Solanacée (Gourmande en nutriments)",
        "oignon": "Alliacée (Racine / Bulbe)",
        "manioc": "Tubercules",
        "patate douce": "Tubercules"
    }

    famille_actuelle = FAMILLES.get(derniere_culture, "Famille végétale")

    with col_rot2:
        st.info(f"Famille botanique actuelle : **{famille_actuelle}**")

    st.divider()

    st.markdown("### 📌 Succession recommandée pour la prochaine campagne :")

    if "Légumineuse" in famille_actuelle:
        st.success("✅ **Excellente nouvelle !** La parcelle a bénéficié d'une fixation d'azote naturel par la légumineuse.\n\n"
                   "👉 **Recommandation** : Plantez une **Céréale gourmande** (Maïs, Riz, Mil) ou une Solanacée (Tomate, Poivron) qui profitera de la fertilité du sol.")
    elif "Céréale" in famille_actuelle or "Gourmande" in famille_actuelle:
        st.warning("⚠️ **Attention** : Le sol a été fortement sollicité en azote.\n\n"
                   "👉 **Recommandation** : Plantez une **Légumineuse fixatrice d'azote** (Arachide, Niébé, Soja) ou une Alliacée (Oignon) pour restaurer la fertilité naturelle du sol et éviter la propagation des champignons du sol.")
    else:
        st.info("👉 **Recommandation** : Alternez avec une **Légumineuse** (Arachide, Niébé) ou une Céréale (Mil, Maïs). Evitez de replanter la même famille 2 années de suite sur le même morceau de terre.")


# --- TAB 2 : SUIVI DE PLUVIOMÉTRIE (MM PLUIE) ---
with tab_pluvio:
    st.subheader("🌧️ Relevé de Pluviométrie (Pluie en mm)")
    st.caption("Enregistrez les mm d'eau mesurés avec votre pluviomètre par parcelle.")

    parcelles = database.get_parcelles(user_id)

    with st.form(key="form_pluvio", clear_on_submit=True):
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            date_pluie = st.date_input("Date de la pluie :")
        with col_p2:
            noms_parc = [p["nom"] for p in parcelles] if parcelles else ["Toute l'exploitation"]
            parcelle_pluie = st.selectbox("Parcelle / Zone :", options=noms_parc)
        with col_p3:
            mm_pluie = st.number_input("Hauteur d'eau (mm) :", min_value=0.0, value=15.0, step=1.0)

        remarques_pluie = st.text_input("Remarques (ex: Orage violent, pluie fine) :")

        ajouter_pluie = st.form_submit_button("Enregistrer la pluie", type="primary")

        if ajouter_pluie:
            if mm_pluie > 0:
                database.add_pluviometrie({
                    "date": date_pluie,
                    "parcelle": parcelle_pluie,
                    "mm_pluie": mm_pluie,
                    "remarques": remarques_pluie
                })
                st.success(f"✅ Relevé de {mm_pluie} mm enregistré !")
                st.rerun()
            else:
                st.warning("⚠️ Indiquez une quantité de pluie valide.")

    pluv_list = database.get_pluviometrie()

    if pluv_list:
        st.divider()
        st.subheader("📊 Graphique de Pluviométrie Cumulée")
        df_pluv = pd.DataFrame(pluv_list)
        df_pluv["mm_pluie"] = df_pluv["mm_pluie"].astype(float)
        
        fig_pluv = px.bar(
            df_pluv,
            x="date",
            y="mm_pluie",
            color="parcelle",
            labels={"date": "Date", "mm_pluie": "Précipitations (mm)"},
            title="Précipitations par date (mm)"
        )
        st.plotly_chart(fig_pluv, use_container_width=True)

        st.markdown(f"**Total cumulé des pluies relevées** : **{df_pluv['mm_pluie'].sum():.1f} mm**")
