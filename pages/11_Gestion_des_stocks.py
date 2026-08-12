import streamlit as st
import database
import theme
import auth

st.set_page_config(page_title="Gestion des Stocks", page_icon="📦", layout="wide")
database.init_db()
theme.apply_custom_theme()

auth.requiere_connexion()

# Récupération de l'utilisateur connecté
user_id = st.session_state["user_id"]

st.title("📦 Magasin & Gestion des Stocks d'Intrants")
st.caption("Suivez les quantités de vos engrais, semences et produits phytosanitaires. Alertes automatiques en cas de niveau bas.")

stocks = database.get_stocks(user_id)

# --- ALERTES NIVEAU BAS ---
stocks_alertes = [s for s in stocks if s["quantite"] <= s["seuil_alerte"]]

if stocks_alertes:
    st.error("⚠️ **Alertes Niveau Bas de Stock** : Les articles suivants ont atteint ou dépassé leur seuil critique !")
    for s in stocks_alertes:
        st.markdown(f"- 🔴 **{s['nom']}** ({s['categorie']}) : **{s['quantite']:g} {s['unite']}** restants (Seuil d'alerte : {s['seuil_alerte']:g} {s['unite']})")
    st.divider()

# --- ACCÈS RAPIDE / STATISTIQUES ---
col1, col2, col3 = st.columns(3)
with col1:
    theme.render_kpi_card("Total Articles en Stock", f"{len(stocks)}", "Engrais, semences, phyto...", icon="📦", border_color="#1b4332")
with col2:
    theme.render_kpi_card("Articles Critiques", f"{len(stocks_alertes)}", "Stock <= Seuil d'alerte", icon="⚠️", border_color="#dc2626" if stocks_alertes else "#059669")
with col3:
    categories_distinctes = len(set(s["categorie"] for s in stocks)) if stocks else 0
    theme.render_kpi_card("Catégories d'Intrants", f"{categories_distinctes}", "Diversité du magasin", icon="🏷️", border_color="#d97706")

st.divider()

# --- FORMULAIRE D'AJOUT D'UN ARTICLE ---
st.subheader("Ajouter un nouvel article en stock")

CATEGORIES_STOCK = ["Engrais", "Semences / Plants", "Produits Phyto", "Fumure Organique", "Carburant", "Outillage / Matériel", "Autres"]

with st.form(key="form_stock", clear_on_submit=True):
    col_a, col_b = st.columns(2)
    with col_a:
        nom_stock = st.text_input("Nom de l'intrant / produit :", placeholder="ex: Engrais NPK 15-15-15 (Sac 50kg)")
        categorie = st.selectbox("Catégorie :", options=CATEGORIES_STOCK)
        emplacement = st.text_input("Emplacement de stockage :", value="Magasin Principal")
    with col_b:
        quantite = st.number_input("Quantité initiale :", min_value=0.0, value=10.0, step=1.0)
        unite = st.selectbox("Unité de mesure :", options=["kg", "sacs", "litres", "unités", "tonnes", "boîtes"])
        seuil_alerte = st.number_input("Seuil d'alerte critique :", min_value=0.0, value=2.0, step=1.0)

    ajouter = st.form_submit_button("Enregistrer en stock", type="primary")

    if ajouter:
        if nom_stock:
            database.add_stock(user_id, {
                "nom": nom_stock,
                "categorie": categorie,
                "quantite": quantite,
                "unite": unite,
                "seuil_alerte": seuil_alerte,
                "emplacement": emplacement
            })
            st.success(f"✅ Article « {nom_stock} » ajouté au magasin !")
            st.rerun()
        else:
            st.warning("⚠️ Indiquez au moins le nom du produit.")

st.divider()

# --- LISTE ET AJUSTEMENT DES STOCKS ---
st.subheader(f"Inventaire du magasin ({len(stocks)})")

if not stocks:
    st.info("Aucun intrant enregistré dans le magasin pour le moment.")
else:
    for s in stocks:
        is_low = s["quantite"] <= s["seuil_alerte"]
        card_border = "#dc2626" if is_low else "#2d6a4f"

        with st.container(border=True):
            col_info, col_qty, col_actions = st.columns([4, 3, 2])

            with col_info:
                st.markdown(f"### **{s['nom']}**")
                st.caption(f"Catégorie : **{s['categorie']}** | Emplacement : {s['emplacement']}")
                if is_low:
                    st.markdown("<span style='color: red; font-weight: bold;'>⚠ NIVEAU CRITIQUE</span>", unsafe_allow_html=True)

            with col_qty:
                st.markdown(f"### **{s['quantite']:g} {s['unite']}**")
                st.caption(f"Seuil minimal : {s['seuil_alerte']:g} {s['unite']}")

            with col_actions:
                col_plus, col_minus, col_del = st.columns(3)
                with col_plus:
                    if st.button("➕", key=f"add_{s['id']}", help="Ajouter +1"):
                        database.update_stock_quantite(user_id, s['id'], 1)
                        st.rerun()
                with col_minus:
                    if st.button("➖", key=f"sub_{s['id']}", help="Retirer -1"):
                        database.update_stock_quantite(user_id, s['id'], -1)
                        st.rerun()
                with col_del:
                    if st.button("🗑️", key=f"del_{s['id']}", help="Supprimer l'article"):
                        database.delete_stock(user_id, s['id'])
                        st.success("Article supprimé !")
                        st.rerun()
