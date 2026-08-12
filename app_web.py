import streamlit as st
import database
import theme

st.markdown("""
    <style>
    /* ===== MENU LATÉRAL - COULEURS UNIQUEMENT ===== */
    
    /* Fond du menu */
    section[data-testid="stSidebar"] {
        background-color: #1e293b !important;
    }
    
    /* Texte et icônes en blanc */
    section[data-testid="stSidebar"] * {
        color: #f1f5f9 !important;
    }
    
    /* Survol */
    section[data-testid="stSidebar"] a:hover {
        background-color: #334155 !important;
        color: #4ade80 !important;
    }
    
    /* Page active */
    section[data-testid="stSidebar"] a[aria-current="page"] {
        background-color: #0f766e !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- Configuration de la page ---
st.set_page_config(page_title="Assistant agricole", page_icon="🌾", layout="wide")

# --- Initialisation de la BDD & Thème ---
database.init_db()
theme.apply_custom_theme()

import auth
auth.requiere_connexion()

user_id = st.session_state["user_id"]

# --- Chargement des données dynamiques SQLite ---
exploitation = database.get_exploitation(user_id)
parcelles = database.get_parcelles(user_id)
campagnes = database.get_campagnes(user_id)
depenses = database.get_depenses(user_id)
ventes = database.get_ventes(user_id)
stocks = database.get_stocks()
contacts = database.get_contacts()
pluviometrie = database.get_pluviometrie()
nombre_prix = database.count_prix_marche()

total_superficie = sum(p["superficie"] for p in parcelles) if parcelles else exploitation.get("superficie_totale", 0.0)
total_ca = sum(v["montant"] for v in ventes)
total_depenses = sum(d["montant"] for d in depenses)
benefice = total_ca - total_depenses
total_mm_pluie = sum(float(p["mm_pluie"]) for p in pluviometrie) if pluviometrie else 0.0

# --- En-tête Principal ---
col_title, col_info = st.columns([3, 1])
with col_title:
    nom_ferme = exploitation.get("nom") if exploitation.get("nom") else "Mon Exploitation"
    st.title(f"🌾 Assistant Agricole — {nom_ferme}")
    localite_str = f"📍 {exploitation['localite']}, {exploitation['region']}" if exploitation.get("localite") else "📍 Localité non configurée"
    st.markdown(f"*{localite_str} | Cartographie satellite, PDF, Magasin, Rotation des sols & IA*")

with col_info:
    st.markdown(" ")
    if st.button("🤖 Assistant IA & Photo", type="primary", use_container_width=True):
        st.switch_page("pages/10_assistant_ia.py")

st.divider()

# --- Cartes d'Indicateurs Métriques (KPIs) ---
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    theme.render_kpi_card(
        "Superficie gérée",
        f"{total_superficie:g} ha",
        f"{len(parcelles)} parcelle(s) géolocalisée(s)",
        icon="🚜",
        border_color="#1b4332"
    )

with kpi2:
    theme.render_kpi_card(
        "Pluviométrie totale",
        f"{total_mm_pluie:.1f} mm",
        f"{len(pluviometrie)} relevé(s) enregistrés",
        icon="🌧️",
        border_color="#2563eb"
    )

with kpi3:
    theme.render_kpi_card(
        "Chiffre d'Affaires",
        f"{total_ca:,.0f} FCFA".replace(",", " "),
        f"Dépenses : {total_depenses:,.0f} FCFA".replace(",", " "),
        icon="💵",
        border_color="#059669"
    )

with kpi4:
    color_b = "#059669" if benefice >= 0 else "#dc2626"
    theme.render_kpi_card(
        "Bénéfice Net",
        f"{benefice:,.0f} FCFA".replace(",", " "),
        "Bilan financier consolidé",
        icon="📈",
        border_color=color_b
    )

# --- Navigation Rapide & Services Agricoles ---
st.subheader("⚡ Services & Outils Agricoles")

col_a, col_b, col_c, col_d = st.columns(4)

with col_a:
    with st.container(border=True):
        st.markdown("#### 🗺️ Cartographie & GPS")
        st.write("Visualisez vos parcelles sur carte satellite avec leurs coordonnées GPS.")
        if st.button("Carte Satellite", key="nav_parcelles", use_container_width=True):
            st.switch_page("pages/3_Mes_parcelles.py")

with col_b:
    with st.container(border=True):
        st.markdown("#### 📦 Magasin & Stocks")
        st.write("Suivez le niveau des réserves d'engrais, semences et phyto avec alerte stock bas.")
        if st.button("Magasin Stocks", key="nav_stocks", use_container_width=True):
            st.switch_page("pages/11_Gestion_des_stocks.py")

with col_c:
    with st.container(border=True):
        st.markdown("#### 🌱 Rotation & Pluie")
        st.write("Recommandations d'assolement de sol et relevés de pluviométrie en mm.")
        if st.button("Rotation & Pluie", key="nav_rot", use_container_width=True):
            st.switch_page("pages/13_Rotation_des_cultures.py")

with col_d:
    with st.container(border=True):
        st.markdown("#### 📞 Carnet d'Adresses")
        st.write("Gérez vos contacts d'acheteurs grossistes et fournisseurs d'intrants.")
        if st.button("Carnet d'Adresses", key="nav_ctc", use_container_width=True):
            st.switch_page("pages/12_Carnet_d_adresses.py")

st.divider()

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📄 Bilan PDF & Exports Excel")
    st.write("Téléchargez vos rapports financiers complets en **PDF imprimable**, **Excel** ou **CSV**.")
    if st.button("Générer Bilan PDF / Excel", key="nav_pdf_rent", use_container_width=True):
        st.switch_page("pages/8_Rentabilité.py")

with col_right:
    st.subheader("🔒 Sauvegarde SQLite & Restauration")
    st.success("Toutes vos données (contacts, pluviométrie, finances) sont sauvegardées dans SQLite. Téléchargez un backup en 1 clic dans **Mon exploitation**.")