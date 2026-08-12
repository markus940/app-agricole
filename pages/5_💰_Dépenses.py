from datetime import date
import streamlit as st
import database
import theme

st.set_page_config(page_title="Dépenses", page_icon="💰", layout="wide")
database.init_db()
theme.apply_custom_theme()

import auth
auth.requiere_connexion()

user_id = st.session_state["user_id"]

st.title("💰 Suivi des Dépenses")
st.caption("Enregistrez vos coûts de production par campagne pour suivre précisément votre budget.")

campagnes = database.get_campagnes(user_id)
depenses = database.get_depenses(user_id)

if not campagnes:
    st.warning("⚠️ Vous devez d'abord créer au moins une campagne dans la page **Campagnes** avant d'enregistrer des dépenses.")
    st.stop()

CATEGORIES = [
    "Semences", "Plants", "Engrais", "Fumure", "Produits phytosanitaires",
    "Main-d'œuvre", "Irrigation", "Carburant", "Transport", "Matériel", "Autres",
]

# --- Formulaire d'ajout ---
st.subheader("Ajouter une dépense d'intrant ou de main-d'œuvre")

with st.form(key="form_depense", clear_on_submit=True):
    labels_campagnes = [
        f"{c['parcelle']} — {c['culture'].capitalize()} ({c['statut']})"
        for c in campagnes
    ]
    index_choisi = st.selectbox(
        "Campagne concernée :", options=range(len(labels_campagnes)), format_func=lambda i: labels_campagnes[i]
    )
    campagne_choisie = campagnes[index_choisi]

    date_depense = st.date_input("Date du paiement :", value=date.today())
    categorie = st.selectbox("Catégorie de dépense :", options=CATEGORIES)
    description = st.text_input("Description / Libellé :", placeholder="ex: 2 sacs d'engrais NPK 15-15-15")

    col1, col2 = st.columns(2)
    with col1:
        quantite = st.number_input("Quantité :", min_value=0.0, value=1.0, step=1.0)
    with col2:
        prix_unitaire = st.number_input("Prix unitaire (FCFA) :", min_value=0.0, step=500.0)

    montant = quantite * prix_unitaire
    st.markdown(f"#### Montant total calculé : **{montant:,.0f} FCFA**".replace(",", " "))

    ajouter = st.form_submit_button("Enregistrer la dépense", type="primary")

    if ajouter:
        if description and montant > 0:
            database.add_depense(user_id, {
                "date": date_depense,
                "date": date_depense,
                "categorie": categorie,
                "description": description,
                "quantite": quantite,
                "prix_unitaire": prix_unitaire,
                "montant": montant,
                "campagne": campagne_choisie["parcelle"],
                "culture": campagne_choisie["culture"],
            })
            st.success("✅ Dépense enregistrée et sauvegardée dans SQLite !")
            st.rerun()
        else:
            st.warning("⚠️ Indiquez une description et un montant valide.")

# --- Liste des dépenses enregistrées ---
depenses = database.get_depenses(user_id)

st.divider()
st.subheader(f"Mes dépenses enregistrées ({len(depenses)})")

if not depenses:
    st.info("Aucune dépense enregistrée pour le moment.")
else:
    total = sum(d["montant"] for d in depenses)
    st.metric("Cumul total des dépenses", f"{total:,.0f} FCFA".replace(",", " "))

    for d in depenses:
        with st.container(border=True):
            col_info, col_montant, col_bouton = st.columns([4, 2, 1])
            with col_info:
                st.markdown(f"**{d['categorie']}** — {d['description']}")
                st.caption(f"Date : {d['date']} | Campagne : {d['campagne']} ({d['culture'].capitalize()})")
            with col_montant:
                st.markdown(f"### **{d['montant']:,.0f} FCFA**".replace(",", " "))
                if d['quantite'] > 0 and d['prix_unitaire'] > 0:
                    st.caption(f"{d['quantite']:g} x {d['prix_unitaire']:,.0f} FCFA".replace(",", " "))
            with col_bouton:
                if st.button("Supprimer", key=f"suppr_dep_{d['id']}", type="secondary"):
                    database.delete_depense(user_id, d['id'])
                    st.success("Dépense supprimée !")
                    st.rerun()