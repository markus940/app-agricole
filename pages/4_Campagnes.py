import json
from datetime import timedelta
import streamlit as st
import database
import theme

st.set_page_config(page_title="Campagnes", page_icon="📋", layout="wide")
database.init_db()
theme.apply_custom_theme()

import auth
auth.requiere_connexion()

user_id = st.session_state["user_id"]

with open("cultures.json", "r", encoding="utf-8") as f:
    cultures = json.load(f)

st.title("📋 Campagnes agricoles")
st.caption("Associez une parcelle à une date de semis et suivez le calendrier prévisionnel de récolte dans SQLite.")

parcelles = database.get_parcelles(user_id)
campagnes = database.get_campagnes(user_id)

if not parcelles:
    st.warning("⚠️ Vous devez d'abord créer au moins une parcelle dans la page **Mes parcelles** avant de démarrer une campagne.")
    st.stop()

# --- Formulaire d'ajout ---
st.subheader("Démarrer une nouvelle campagne")

with st.form(key="form_campagne", clear_on_submit=True):
    noms_parcelles = [p["nom"] for p in parcelles]
    nom_parcelle_choisie = st.selectbox("Parcelle de destination :", options=noms_parcelles)

    # Récupération automatique de la culture et de la superficie de la parcelle
    parcelle_obj = next(p for p in parcelles if p["nom"] == nom_parcelle_choisie)
    culture = parcelle_obj["culture"]
    st.info(f"🌾 Culture pré-sélectionnée : **{culture.capitalize()}** — Superficie : **{parcelle_obj['superficie']} ha**")

    date_semis = st.date_input("Date de semis / plantation :")

    statut = st.selectbox(
        "Statut de la campagne :",
        options=["🟡 Planifiée", "🔵 En cours", "🟢 Récoltée", "⚫ Terminée"],
        index=1,
    )

    demarrer = st.form_submit_button("Créer la campagne", type="primary")

    if demarrer:
        calendrier = cultures.get(culture, {}).get("calendrier")
        date_recolte_prevue = None
        if calendrier:
            dernier_evenement = max(calendrier, key=lambda e: e["jour"])
            date_recolte_prevue = date_semis + timedelta(days=dernier_evenement["jour"])

        database.add_campagne(user_id, {
            "parcelle": nom_parcelle_choisie,
            "culture": culture,
            "superficie": parcelle_obj["superficie"],
            "date_semis": date_semis,
            "date_recolte_prevue": date_recolte_prevue,
            "statut": statut,
        })
        st.success(f"✅ Campagne créée avec succès pour la parcelle « {nom_parcelle_choisie} » !")
        st.rerun()

# --- Liste des campagnes enregistrées ---
campagnes = database.get_campagnes(user_id)

st.divider()
st.subheader(f"Mes campagnes enregistrées ({len(campagnes)})")

if not campagnes:
    st.info("Aucune campagne enregistrée pour le moment.")
else:
    for c in campagnes:
        with st.container(border=True):
            col_info, col_stat, col_bouton = st.columns([4, 2, 1])
            with col_info:
                st.markdown(f"### **{c['parcelle']}** — {c['culture'].capitalize()}")
                st.markdown(f"📏 Superficie : **{c['superficie']} ha**")
                date_semis_str = c['date_semis']
                recolte_str = f" · Récolte estimée : **{c['date_recolte_prevue']}**" if c.get('date_recolte_prevue') else ""
                st.caption(f"Semis : {date_semis_str}{recolte_str}")
            with col_stat:
                st.markdown(theme.get_badge_html(c['statut']), unsafe_allow_html=True)
            with col_bouton:
                if st.button("Supprimer", key=f"suppr_camp_{c['id']}", type="secondary"):
                    database.delete_campagne(user_id, c['id'])
                    st.success("Campagne supprimée !")
                    st.rerun()
