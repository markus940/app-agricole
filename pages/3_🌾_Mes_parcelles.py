import json
import pandas as pd
import pydeck as pdk
import streamlit as st
import database
import theme

st.set_page_config(page_title="Mes parcelles", page_icon="🌾", layout="wide")
database.init_db()
theme.apply_custom_theme()

import auth
auth.requiere_connexion()

user_id = st.session_state["user_id"]

with open("cultures.json", "r", encoding="utf-8") as f:
    cultures = json.load(f)

st.title("🌾 Mes parcelles & Cartographie Satellite")
st.caption("Gérez vos parcelles et géolocalisez-les directement sur la carte satellite interactive.")

# --- FORMULAIRE D'AJOUT ---
st.subheader("Ajouter une nouvelle parcelle")

with st.form(key="form_parcelle", clear_on_submit=True):
    nom_parcelle = st.text_input("Nom de la parcelle :", placeholder="ex: Parcelle P01 - Bas-fond")

    col1, col2 = st.columns(2)
    with col1:
        superficie = st.number_input("Superficie (ha) :", min_value=0.0, step=0.1)
        culture = st.selectbox("Culture principale :", options=sorted(cultures.keys()))
    with col2:
        localisation = st.text_input("Localisation / Secteur :", placeholder="ex: Sinthiou Garba")
        campagne = st.text_input("Campagne d'origine :", placeholder="ex: 2026")

    col_lat, col_lon, col_stat = st.columns(3)
    with col_lat:
        latitude = st.number_input("Latitude GPS :", value=14.79, format="%.5f", help="ex: 14.7900 pour Thiès/Dakar")
    with col_lon:
        longitude = st.number_input("Longitude GPS :", value=-16.92, format="%.5f", help="ex: -16.9200")
    with col_stat:
        statut = st.selectbox(
            "Statut initial :",
            options=["🟡 Planifiée", "🔵 En cours", "🟢 Récoltée", "⚫ Terminée"],
        )

    ajouter = st.form_submit_button("Ajouter la parcelle", type="primary")

    if ajouter:
        if nom_parcelle and superficie > 0:
            database.add_parcelle(user_id, {
                "nom": nom_parcelle,
                "superficie": superficie,
                "culture": culture,
                "localisation": localisation,
                "campagne": campagne,
                "statut": statut,
                "latitude": latitude,
                "longitude": longitude
            })
            st.success(f"✅ Parcelle « {nom_parcelle} » géolocalisée et ajoutée avec succès !")
            st.rerun()
        else:
            st.warning("⚠️ Indiquez au moins un nom et une superficie valide.")

parcelles = database.get_parcelles(user_id)

st.divider()

# --- CARTOGRAPHIE SATELLITE PYDECK ---
st.subheader("🗺️ Carte Satellite des Parcelles")

if parcelles:
    df_parcelles = pd.DataFrame(parcelles)
    df_parcelles["culture_cap"] = df_parcelles["culture"].str.capitalize()
    df_parcelles["tooltip_text"] = df_parcelles.apply(
        lambda r: f"🌾 {r['nom']} ({r['culture_cap']})\n📏 {r['superficie']} ha - {r['statut']}", axis=1
    )

    # Position moyenne pour le centrage de la carte
    mean_lat = df_parcelles["latitude"].mean()
    mean_lon = df_parcelles["longitude"].mean()

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=df_parcelles,
        get_position=["longitude", "latitude"],
        get_color="[27, 67, 50, 200]",
        get_radius=150,
        pickable=True,
    )

    view_state = pdk.ViewState(
        latitude=mean_lat,
        longitude=mean_lon,
        zoom=11,
        pitch=30,
    )

    r = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"text": "{tooltip_text}"},
        map_style="mapbox://styles/mapbox/satellite-v9"
    )

    st.pydeck_chart(r)
else:
    st.info("Ajoutez des parcelles géolocalisées pour afficher la carte satellite.")

st.divider()

# --- LISTE DES PARCELLES EXISTANTES ---
st.subheader(f"Mes parcelles enregistrées ({len(parcelles)})")

if not parcelles:
    st.info("Aucune parcelle enregistrée en base de données pour le moment.")
else:
    for p in parcelles:
        with st.container(border=True):
            col_info, col_stat, col_bouton = st.columns([4, 2, 1])
            with col_info:
                st.markdown(f"### **{p['nom']}** — {p['culture'].capitalize()}")
                st.markdown(f"📐 Superficie : **{p['superficie']} ha** | 📍 GPS : `{p['latitude']:.4f}, {p['longitude']:.4f}`")
                if p.get("localisation"):
                    st.caption(f"Secteur : {p['localisation']}")
            with col_stat:
                st.markdown(theme.get_badge_html(p['statut']), unsafe_allow_html=True)
            with col_bouton:
                if st.button("Supprimer", key=f"suppr_parc_{p['id']}", type="secondary"):
                    database.delete_parcelle(p['id'])
                    st.success("Parcelle supprimée !")
                    st.rerun()