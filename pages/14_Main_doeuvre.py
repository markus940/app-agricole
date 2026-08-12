import streamlit as st
import database
import theme
import auth
from datetime import date

st.set_page_config(page_title="Main d'œuvre", page_icon="👷", layout="wide")
database.init_db()
theme.apply_custom_theme()

auth.requiere_connexion()
user_id = st.session_state["user_id"]

st.title("👷 Gestion de la Main d'œuvre")
st.caption("Suivez vos ouvriers et les jours de travail effectués sur vos parcelles et campagnes.")

# Récupération des données
ouvriers = database.get_ouvriers(user_id)
jours = database.get_jours_travail(user_id)
parcelles = database.get_parcelles(user_id) if hasattr(database, "get_parcelles") else []
campagnes = database.get_campagnes(user_id) if hasattr(database, "get_campagnes") else []

# ====================== STATISTIQUES ======================
total_depense = sum(j["nombre_jours"] * j["salaire_journalier"] for j in jours)
jours_totaux = sum(j["nombre_jours"] for j in jours)

col1, col2, col3 = st.columns(3)
with col1:
    theme.render_kpi_card("Ouvriers enregistrés", f"{len(ouvriers)}", "Personnes", icon="👷", border_color="#1b4332")
with col2:
    theme.render_kpi_card("Jours travaillés", f"{jours_totaux:g}", "Total cumulé", icon="📅", border_color="#d97706")
with col3:
    theme.render_kpi_card("Dépense totale", f"{total_depense:,.0f} FCFA", "Main d'œuvre", icon="💰", border_color="#dc2626")

st.divider()

# ====================== AJOUTER UN OUVRIER ======================
st.subheader("Ajouter un ouvrier")

with st.form("form_ouvrier", clear_on_submit=True):
    col_a, col_b = st.columns(2)
    with col_a:
        nom_ouvrier = st.text_input("Nom de l'ouvrier *", placeholder="ex: Ibrahima Sarr")
        telephone = st.text_input("Téléphone", placeholder="ex: 77 123 45 67")
    with col_b:
        specialite = st.text_input("Spécialité (optionnel)", placeholder="ex: Traitement, Récolte, Labour...")

    if st.form_submit_button("Enregistrer l'ouvrier", type="primary"):
        if nom_ouvrier:
            database.add_ouvrier(user_id, {
                "nom": nom_ouvrier,
                "telephone": telephone,
                "specialite": specialite
            })
            st.success(f"✅ Ouvrier « {nom_ouvrier} » ajouté !")
            st.rerun()
        else:
            st.warning("⚠️ Le nom est obligatoire.")

st.divider()

# ====================== ENREGISTRER UN JOUR DE TRAVAIL ======================
st.subheader("Enregistrer un jour de travail")

if not ouvriers:
    st.info("Ajoutez d'abord au moins un ouvrier.")
else:
    with st.form("form_jour", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            ouvrier_options = {f"{o['nom']}": o['id'] for o in ouvriers}
            ouvrier_nom = st.selectbox("Ouvrier *", options=list(ouvrier_options.keys()))
            date_travail = st.date_input("Date du travail", value=date.today())

        with col2:
            nombre_jours = st.number_input("Nombre de jours", min_value=0.5, max_value=30.0, value=1.0, step=0.5)
            salaire_journalier = st.number_input("Salaire journalier (FCFA)", min_value=0, value=3000, step=500)

        with col3:
            type_lien = st.selectbox("Lier à", options=["Aucun", "Parcelle", "Campagne"])

            parcelle_id = None
            campagne_id = None

            if type_lien == "Parcelle" and parcelles:
                parcelle_options = {f"{p['nom']}": p['id'] for p in parcelles}
                parcelle_nom = st.selectbox("Parcelle", options=list(parcelle_options.keys()))
                parcelle_id = parcelle_options[parcelle_nom]
            elif type_lien == "Campagne" and campagnes:
                campagne_options = {f"{c.get('culture', '')} - {c.get('parcelle', '')}": c['id'] for c in campagnes}
                campagne_nom = st.selectbox("Campagne", options=list(campagne_options.keys()))
                campagne_id = campagne_options[campagne_nom]

        remarque = st.text_input("Remarque (optionnel)")

        if st.form_submit_button("Enregistrer le jour de travail", type="primary"):
            database.add_jour_travail(user_id, {
                "ouvrier_id": ouvrier_options[ouvrier_nom],
                "date_travail": str(date_travail),
                "nombre_jours": nombre_jours,
                "salaire_journalier": salaire_journalier,
                "parcelle_id": parcelle_id,
                "campagne_id": campagne_id,
                "remarque": remarque
            })

           # Si le jour de travail est lié à une campagne OU une parcelle, on l'ajoute
            # aussi automatiquement comme dépense, pour qu'il compte dans la Rentabilité.
            nom_parcelle_liee = None
            culture_liee = None

            if campagne_id is not None:
                campagne_obj = next(c for c in campagnes if c["id"] == campagne_id)
                nom_parcelle_liee = campagne_obj["parcelle"]
                culture_liee = campagne_obj["culture"]
            elif parcelle_id is not None:
                parcelle_obj = next(p for p in parcelles if p["id"] == parcelle_id)
                nom_parcelle_liee = parcelle_obj["nom"]
                culture_liee = parcelle_obj["culture"]

            if nom_parcelle_liee is not None:
                montant_main_oeuvre = nombre_jours * salaire_journalier

                database.add_depense(user_id, {
                    "date": date_travail,
                    "categorie": "Main-d'œuvre",
                    "description": f"{nombre_jours:g} j — {ouvrier_nom}",
                    "quantite": nombre_jours,
                    "prix_unitaire": salaire_journalier,
                    "montant": montant_main_oeuvre,
                    "campagne": nom_parcelle_liee,
                    "culture": culture_liee,
                })

            st.success("✅ Jour de travail enregistré !")
            st.rerun()

st.divider()

# ====================== LISTE DES JOURS DE TRAVAIL ======================
st.subheader(f"Historique des jours de travail ({len(jours)})")

if not jours:
    st.info("Aucun jour de travail enregistré pour le moment.")
else:
    for j in jours:
        cout = j["nombre_jours"] * j["salaire_journalier"]
        with st.container(border=True):
            col_info, col_cout, col_del = st.columns([5, 2, 1])

            with col_info:
                st.markdown(f"### {j['ouvrier_nom']}")
                st.caption(f"📅 {j['date_travail']} • {j['nombre_jours']:g} jour(s)")
                if j.get("remarque"):
                    st.caption(f"Note : {j['remarque']}")

            with col_cout:
                st.markdown(f"### {cout:,.0f} FCFA")
                st.caption(f"{j['salaire_journalier']:,.0f} FCFA / jour")

            with col_del:
                if st.button("🗑️", key=f"del_jour_{j['id']}", help="Supprimer"):
                    database.delete_jour_travail(user_id, j['id'])
                    st.rerun()

st.divider()

# ====================== LISTE DES OUVRIERS ======================
st.subheader(f"Mes ouvriers ({len(ouvriers)})")

if ouvriers:
    for o in ouvriers:
        with st.container(border=True):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"**{o['nom']}**")
                info = []
                if o.get("telephone"):
                    info.append(f"📱 {o['telephone']}")
                if o.get("specialite"):
                    info.append(f"🛠️ {o['specialite']}")
                if info:
                    st.caption(" • ".join(info))
            with col2:
                if st.button("Supprimer", key=f"del_ouv_{o['id']}", type="secondary"):
                    database.delete_ouvrier(user_id, o['id'])
                    st.rerun()
