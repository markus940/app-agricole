import json
import streamlit as st

# --- Configuration de la page ---
st.set_page_config(page_title="Fiches techniques agricoles", page_icon="🌾")

# --- Chargement des données ---
with open("cultures.json", "r", encoding="utf-8") as f:
    cultures = json.load(f)


def afficher_fiche(nom_culture, infos):
    """Affiche la fiche technique d'une culture avec une mise en page Streamlit."""
    st.header(f"🌱 {nom_culture.capitalize()}")

    for section, contenu in infos.items():
        if isinstance(contenu, dict):
            st.subheader(section.capitalize())
            for cle, valeur in contenu.items():
                st.markdown(f"- **{cle}** : {valeur}")
        else:
            st.markdown(f"**{section.capitalize()}** : {contenu}")


# --- Interface principale ---
st.title("🌾 Fiches techniques agricoles")
st.write("Choisis une culture pour voir sa fiche technique complète.")

# Liste déroulante avec toutes les cultures, triée par ordre alphabétique
noms_cultures = sorted(cultures.keys())
culture_choisie = st.selectbox("Culture :", noms_cultures)

if culture_choisie:
    afficher_fiche(culture_choisie, cultures[culture_choisie])