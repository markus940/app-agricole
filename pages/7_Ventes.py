from datetime import date
import streamlit as st
import database
import theme

st.set_page_config(page_title="Ventes", page_icon="💵", layout="wide")
database.init_db()
theme.apply_custom_theme()

import auth
auth.requiere_connexion()

user_id = st.session_state["user_id"]

st.title("💵 Suivi des Ventes")
st.caption("Enregistrez vos ventes de produits agricoles et calculez votre chiffre d'affaires global.")

campagnes = database.get_campagnes(user_id)
ventes = database.get_ventes(user_id)

if not campagnes:
    st.warning("⚠️ Vous devez d'abord créer au moins une campagne dans la page **Campagnes** avant d'enregistrer des ventes.")
    st.stop()

# --- Formulaire d'ajout ---
st.subheader("Enregistrer une nouvelle vente")

with st.form(key="form_vente", clear_on_submit=True):
    labels_campagnes = [
        f"{c['parcelle']} — {c['culture'].capitalize()} ({c['statut']})"
        for c in campagnes
    ]
    index_choisi = st.selectbox(
        "Campagne d'origine :", options=range(len(labels_campagnes)), format_func=lambda i: labels_campagnes[i]
    )
    campagne_choisie = campagnes[index_choisi]

    date_vente = st.date_input("Date de transaction :", value=date.today())
    acheteur = st.text_input("Acheteur / Client :", placeholder="ex: Grossiste Marché Central de Thiès")

    col1, col2 = st.columns(2)
    with col1:
        quantite_kg = st.number_input("Quantité vendue (kg) :", min_value=0.0, step=50.0)
    with col2:
        prix_unitaire = st.number_input("Prix de vente (FCFA/kg) :", min_value=0.0, step=25.0)

    montant = quantite_kg * prix_unitaire
    st.markdown(f"#### Chiffre d'affaires de la vente : **{montant:,.0f} FCFA**".replace(",", " "))

    ajouter = st.form_submit_button("Enregistrer la vente", type="primary")

    if ajouter:
        if quantite_kg > 0 and prix_unitaire > 0:
            database.add_vente(user_id, {
                "date": date_vente,
                "campagne": campagne_choisie["parcelle"],
                "culture": campagne_choisie["culture"],
                "acheteur": acheteur,
                "quantite_kg": quantite_kg,
                "prix_unitaire": prix_unitaire,
                "montant": montant,
            })
            st.success("✅ Vente enregistrée avec succès dans SQLite !")
            st.rerun()
        else:
            st.warning("⚠️ Indiquez une quantité et un prix unitaires valides.")

# --- Liste des ventes enregistrées ---
ventes = database.get_ventes(user_id)

st.divider()
st.subheader(f"Mes ventes enregistrées ({len(ventes)})")

if not ventes:
    st.info("Aucune vente enregistrée pour le moment.")
else:
    total_ca = sum(v["montant"] for v in ventes)
    st.metric("Chiffre d'affaires cumulé", f"{total_ca:,.0f} FCFA".replace(",", " "))

    for v in ventes:
        with st.container(border=True):
            col_info, col_montant, col_bouton = st.columns([4, 2, 1])
            with col_info:
                st.markdown(f"### **{v['culture'].capitalize()}** — {v['quantite_kg']:,.0f} kg".replace(",", " "))
                acheteur_str = f" Client : {v['acheteur']}" if v.get("acheteur") else ""
                st.caption(f"Date : {v['date']} | Campagne : {v['campagne']}{acheteur_str}")
            with col_montant:
                st.markdown(f"### **{v['montant']:,.0f} FCFA**".replace(",", " "))
                st.caption(f"Prix unit. : {v['prix_unitaire']:,.0f} FCFA/kg".replace(",", " "))
            with col_bouton:
                if st.button("Supprimer", key=f"suppr_vente_{v['id']}", type="secondary"):
                    database.delete_vente(user_id, v['id'])
                    st.success("Vente supprimée !")
                    st.rerun()
