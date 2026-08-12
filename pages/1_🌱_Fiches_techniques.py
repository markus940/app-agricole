import json
import os
from datetime import date, timedelta

import requests
import streamlit as st
import database
import theme

# --- Configuration de la page (une seule fois) ---
st.set_page_config(page_title="Fiches techniques agricoles", page_icon="🌾", layout="wide")
database.init_db()
theme.apply_custom_theme()

import auth
auth.requiere_connexion()

user_id = st.session_state["user_id"]

# --- Chargement des données ---
with open("cultures.json", "r", encoding="utf-8") as f:
    cultures = json.load(f)


def afficher_meteo():
    """Affiche la météo actuelle et les prévisions à 5 jours pour une localité donnée."""
    st.sidebar.header("🌦️ Météo de ta zone")
    
    # On pré-remplit la ville avec la localité de l'exploitation si renseignée
    exploitation = database.get_exploitation(user_id)
    default_ville = exploitation.get("localite", "") if exploitation else ""
    
    ville = st.sidebar.text_input("Ta localité :", value=default_ville, placeholder="ex: Thiès, Dakar, Saint-Louis...")

    if not ville:
        st.sidebar.caption("Tape le nom de ta ville pour voir la météo.")
        return

    try:
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        geo_resp = requests.get(geo_url, params={"name": ville, "count": 1, "language": "fr"}, timeout=10)
        geo_data = geo_resp.json()

        if not geo_data.get("results"):
            st.sidebar.warning("Localité introuvable, vérifie l'orthographe.")
            return

        lieu = geo_data["results"][0]
        lat, lon = lieu["latitude"], lieu["longitude"]
        nom_trouve = lieu.get("name", ville)
        pays = lieu.get("country", "")

        meteo_url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max",
            "timezone": "auto",
            "forecast_days": 5,
        }
        meteo_resp = requests.get(meteo_url, params=params, timeout=10)
        meteo_data = meteo_resp.json()

        st.sidebar.success(f"📍 {nom_trouve}, {pays}")

        jours = meteo_data["daily"]["time"]
        tmax = meteo_data["daily"]["temperature_2m_max"]
        tmin = meteo_data["daily"]["temperature_2m_min"]
        pluie_mm = meteo_data["daily"]["precipitation_sum"]
        pluie_pct = meteo_data["daily"]["precipitation_probability_max"]

        for i in range(len(jours)):
            st.sidebar.markdown(
                f"**{jours[i]}** : {tmin[i]:.0f}°C - {tmax[i]:.0f}°C, "
                f"pluie {pluie_pct[i]}% ({pluie_mm[i]:.1f} mm)"
            )

        if pluie_mm[0] >= 5:
            st.sidebar.info("🌧️ Pluie significative prévue aujourd'hui : tu peux réduire ou reporter l'irrigation.")
        elif pluie_mm[0] < 1:
            st.sidebar.info("☀️ Pas de pluie prévue aujourd'hui : pense à irriguer si besoin.")

    except requests.exceptions.RequestException:
        st.sidebar.error("Impossible de récupérer la météo pour le moment (problème réseau).")


def afficher_fiche(nom_culture, infos):
    """Affiche la fiche technique d'une culture avec une mise en page Streamlit."""
    st.header(f"🌱 Fiche technique : {nom_culture.capitalize()}")

    sections_a_ignorer = {"calculateur", "calendrier"}

    for section, contenu in infos.items():
        if section in sections_a_ignorer:
            continue
        if isinstance(contenu, dict):
            st.subheader(section.capitalize())
            for cle, valeur in contenu.items():
                st.markdown(f"- **{cle}** : {valeur}")
        else:
            st.markdown(f"**{section.capitalize()}** : {contenu}")


def afficher_diagnostic(nom_culture, phytosanitaire):
    """Permet de choisir un symptôme observé et affiche le traitement recommandé."""
    if not phytosanitaire:
        return

    st.divider()
    st.subheader("🐛 Maladies & Ravageurs")
    st.write("Qu'observes-tu sur ta culture ?")

    labels = {cle: cle.replace("_", " ").capitalize() for cle in phytosanitaire}
    symptome_choisi = st.selectbox(
        "Symptôme / ravageur :",
        options=list(labels.keys()),
        format_func=lambda cle: labels[cle],
        key=f"symptome_{nom_culture}",
    )

    if symptome_choisi:
        st.warning(f"**{labels[symptome_choisi]}** → {phytosanitaire[symptome_choisi]}")


def afficher_marche(nom_culture):
    """Affiche les prix récents enregistrés dans SQLite et permet d'en ajouter un."""
    st.divider()
    st.subheader("🛒 Prix du Marché Collaboratifs")
    st.caption("Prix rapportés par les utilisateurs de l'appli, à titre indicatif.")

    prix_recents = database.get_prix_marche(nom_culture)

    if prix_recents:
        for ligne in prix_recents:
            st.markdown(f"- **{ligne['date']}** — {ligne['localite']} : **{ligne['prix_fcfa_kg']:,.0f} FCFA/kg**".replace(",", " "))
    else:
        st.write("Aucun prix rapporté pour cette culture pour le moment. Sois le premier !")

    with st.form(key=f"form_prix_{nom_culture}"):
        localite = st.text_input("Ton marché / ta localité :")
        prix = st.number_input("Prix observé (FCFA/kg) :", min_value=0.0, step=25.0)
        envoye = st.form_submit_button("Enregistrer ce prix")

        if envoye:
            if localite and prix > 0:
                database.add_prix_marche(nom_culture, localite, prix)
                st.success("Merci, ton prix a été enregistré !")
                st.rerun()
            else:
                st.warning("Indique une localité et un prix validé avant d'enregistrer.")


def afficher_calculateur(nom_culture, calc):
    """Affiche un calculateur qui adapte les quantités à la surface du producteur."""
    if calc is None:
        return None, None, None

    st.divider()
    st.subheader("🧮 Calcule tes quantités")

    unite = calc["unite"]
    label_unite = "hectares" if unite == "ha" else "m²"

    surface = st.number_input(
        f"Ta surface ({label_unite}) :",
        min_value=0.0,
        value=1.0 if unite == "ha" else 100.0,
        step=0.1 if unite == "ha" else 10.0,
        key=f"surface_{nom_culture}",
    )

    engrais_estime = None
    semences_estimees = None
    rendement_estime = None

    if surface > 0:
        ratio = surface / calc["surface_ref"]

        engrais_estime = calc["engrais_kg"] * ratio
        st.markdown(f"**Engrais minéral total estimé** : {engrais_estime:.1f} kg")

        if calc["semences_kg"] is not None:
            semences_estimees = calc["semences_kg"] * ratio
            st.markdown(f"**Semences estimées** : {semences_estimees:.2f} kg")
        else:
            st.caption("Quantité de semences non disponible pour cette culture (plants/tubercules/repiquage).")

        if calc.get("rendement_kg") is not None:
            rendement_estime = calc["rendement_kg"] * ratio
            st.markdown(f"**Rendement estimé** : {rendement_estime:.1f} kg")

        st.caption("Estimations basées sur les doses indiquées dans la fiche technique, à ajuster selon ton terrain.")

    return engrais_estime, semences_estimees, rendement_estime


def afficher_calendrier(nom_culture, evenements):
    """Affiche un calendrier de culture à partir d'une date de semis choisie."""
    if not evenements:
        return

    st.divider()
    st.subheader("📅 Ton calendrier de culture")

    date_semis = st.date_input("Date de semis :", key=f"date_{nom_culture}")

    st.write(f"Calendrier estimé à partir du **{date_semis.strftime('%d/%m/%Y')}** :")

    for event in evenements:
        date_event = date_semis + timedelta(days=event["jour"])
        st.markdown(f"- **{date_event.strftime('%d/%m/%Y')}** (jour {event['jour']}) : {event['evenement']}")

    st.caption("Dates estimées à partir des fourchettes indiquées dans la fiche technique.")


# --- Interface principale ---
afficher_meteo()

st.title("🌾 Fiches techniques agricoles")
st.write("Choisis une culture pour voir sa fiche technique complète.")

noms_cultures = sorted(cultures.keys())
culture_choisie = st.selectbox("Culture :", noms_cultures)

if culture_choisie:
    infos = cultures[culture_choisie]
    afficher_fiche(culture_choisie, infos)
    afficher_diagnostic(culture_choisie, infos.get("phytosanitaire"))
    engrais_estime, semences_estimees, rendement_estime = afficher_calculateur(culture_choisie, infos.get("calculateur"))
    afficher_calendrier(culture_choisie, infos.get("calendrier"))
    afficher_marche(culture_choisie)