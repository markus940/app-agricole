from datetime import date
import streamlit as st
import database
import theme

st.set_page_config(page_title="Récoltes", page_icon="🌾", layout="wide")
database.init_db()
theme.apply_custom_theme()

import auth
auth.requiere_connexion()

user_id = st.session_state["user_id"]

st.title("🌾 Suivi des Récoltes")
st.caption("Enregistrez les quantités récoltées et suivez le rendement réel en kg/ha par parcelle.")

campagnes = database.get_campagnes(user_id)
recoltes = database.get_recoltes(user_id)

if not campagnes:
    st.warning("⚠️ Vous devez d'abord créer au moins une campagne dans la page **Campagnes** avant d'enregistrer des récoltes.")
    st.stop()

# --- Formulaire d'ajout ---
st.subheader("Enregistrer une nouvelle récolte")

with st.form(key="form_recolte", clear_on_submit=True):
    labels_campagnes = [
        f"{c['parcelle']} — {c['culture'].capitalize()} ({c['statut']})"
        for c in campagnes
    ]
    index_choisi = st.selectbox(
        "Campagne concernée :", options=range(len(labels_campagnes)), format_func=lambda i: labels_campagnes[i]
    )
    campagne_choisie = campagnes[index_choisi]

    date_recolte = st.date_input("Date de récolte :", value=date.today())
    quantite_kg = st.number_input("Quantité récoltée (kg) :", min_value=0.0, step=100.0)

    ajouter = st.form_submit_button("Enregistrer la récolte", type="primary")

    if ajouter:
        if quantite_kg > 0:
            superficie = campagne_choisie["superficie"]
            rendement_kg_ha = quantite_kg / superficie if superficie > 0 else None

            database.add_recolte(user_id, {
                "date": date_recolte,
                "campagne": campagne_choisie["parcelle"],
                "culture": campagne_choisie["culture"],
                "superficie": superficie,
                "quantite_kg": quantite_kg,
                "rendement_kg_ha": rendement_kg_ha,
            })
            st.success("✅ Récolte enregistrée avec succès dans SQLite !")
            st.rerun()
        else:
            st.warning("⚠️ Indiquez une quantité récoltée valide.")

# --- Liste des récoltes enregistrées ---
recoltes = database.get_recoltes(user_id)

st.divider()
st.subheader(f"Mes récoltes enregistrées ({len(recoltes)})")

if not recoltes:
    st.info("Aucune récolte enregistrée pour le moment.")
else:
    total_kg = sum(r["quantite_kg"] for r in recoltes)
    st.metric("Cumul total récolté", f"{total_kg:,.0f} kg".replace(",", " "))

    for r in recoltes:
        with st.container(border=True):
            col_info, col_rendement, col_bouton = st.columns([4, 2, 1])
            with col_info:
                st.markdown(f"### **{r['campagne']}** — {r['culture'].capitalize()}")
                st.caption(f"Date : {r['date']}")
            with col_rendement:
                st.markdown(f"### **{r['quantite_kg']:,.0f} kg**".replace(",", " "))
                if r.get("rendement_kg_ha"):
                    st.caption(f"Rendement : {r['rendement_kg_ha']:,.0f} kg/ha".replace(",", " "))
            with col_bouton:
                if st.button("Supprimer", key=f"suppr_rec_{r['id']}", type="secondary"):
                    database.delete_recolte(user_id, r['id'])
                    st.success("Récolte supprimée !")
                    st.rerun()