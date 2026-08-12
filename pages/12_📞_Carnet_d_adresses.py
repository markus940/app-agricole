import streamlit as st
import database
import theme
import auth

st.set_page_config(page_title="Carnet d'adresses", page_icon="📞", layout="wide")
database.init_db()
theme.apply_custom_theme()

auth.requiere_connexion()

# Récupération de l'utilisateur connecté
user_id = st.session_state["user_id"]

st.title("📞 Carnet d'Adresses — Acheteurs & Fournisseurs")
st.caption("Conservez les coordonnées de vos acheteurs, grossistes, fournisseurs d'engrais et partenaires agricoles.")

contacts = database.get_contacts(user_id)

# --- FORMULAIRE D'AJOUT ---
st.subheader("Ajouter un contact")

with st.form(key="form_contact", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        nom = st.text_input("Nom / Raison sociale :", placeholder="ex: Mamadou Diallo (Grossiste Marché Thiès)")
        role = st.selectbox("Type de contact :", options=["🛒 Acheteur / Grossiste", "🌱 Fournisseur d'Intrants", "🚜 Prestataire / Transporteur", "🤝 Coopérative / Partenaire"])
        telephone = st.text_input("Numéro de Téléphone / WhatsApp :", placeholder="ex: +221 77 000 00 00")
    with col2:
        localite = st.text_input("Localité / Marché :", placeholder="ex: Marché Central de Thiès")
        produits = st.text_input("Produits / Services associés :", placeholder="ex: Achète Tomates, Oignons en gros")
        remarques = st.text_area("Remarques / Conditions :", placeholder="ex: Paye au comptant, livraison sur place", height=68)

    ajouter = st.form_submit_button("Enregistrer le contact", type="primary")

    if ajouter:
        if nom:
            database.add_contact(user_id, {
                "nom": nom,
                "role": role,
                "telephone": telephone,
                "localite": localite,
                "produits": produits,
                "remarques": remarques
            })
            st.success(f"✅ Contact « {nom} » enregistré avec succès !")
            st.rerun()
        else:
            st.warning("⚠️ Indiquez au moins le nom du contact.")

st.divider()

# --- LISTE DES CONTACTS ---
st.subheader(f"Mes contacts enregistrés ({len(contacts)})")

if not contacts:
    st.info("Aucun contact enregistré pour le moment.")
else:
    # Filtre par rôle
    filtre_role = st.radio("Filtrer par type :", options=["Tous", "🛒 Acheteur / Grossiste", "🌱 Fournisseur d'Intrants", "🚜 Prestataire / Transporteur", "🤝 Coopérative / Partenaire"], horizontal=True)

    contacts_filtr = contacts if filtre_role == "Tous" else [c for c in contacts if c["role"] == filtre_role]

    for c in contacts_filtr:
        with st.container(border=True):
            col_info, col_contact, col_del = st.columns([4, 3, 1])
            with col_info:
                st.markdown(f"### **{c['nom']}**")
                st.markdown(f"🏷️ **{c['role']}** | 📍 Localité : {c['localite'] or 'Non spécifiée'}")
                if c.get("produits"):
                    st.caption(f"Produits : {c['produits']}")
                if c.get("remarques"):
                    st.caption(f"Notes : {c['remarques']}")
            with col_contact:
                if c.get("telephone"):
                    st.markdown(f"📱 **Téléphone / WhatsApp** :\n`{c['telephone']}`")
            with col_del:
                if st.button("Supprimer", key=f"del_ctc_{c['id']}", type="secondary"):
                    database.delete_contact(user_id, c['id'])
                    st.success("Contact supprimé !")
                    st.rerun()