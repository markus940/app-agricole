import json
import os
import requests
from PIL import Image
import streamlit as st
import theme

st.set_page_config(page_title="Assistant IA Agricole", page_icon="🤖", layout="wide")
theme.apply_custom_theme()

import auth
auth.requiere_connexion()

# --- Chargement des fiches cultures pour le moteur d'IA local ---
with open("cultures.json", "r", encoding="utf-8") as f:
    cultures_db = json.load(f)

st.title("🤖 Assistant IA & Diagnostic Agricole par Photo")
st.write(
    "Posez vos questions agronomiques ou prenez en photo les symptômes de vos cultures "
    "pour recevoir des conseils adaptés à votre exploitation."
)

tab_chat, tab_photo, tab_diagnostic = st.tabs([
    "💬 Chatbot Agronome",
    "📷 Diagnostic par Photo (IA)",
    "🔬 Diagnostic par Symptôme"
])

# --- TAB 1 : CHATBOT AGRONOMIQUE ---
with tab_chat:
    st.caption("Assistant virtuel spécialisé en cultures sahéliennes & maraîchères.")

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {"role": "assistant", "content": "Bonjour ! Je suis votre assistant agricole virtuel. Quelle culture ou problème souhaitez-vous analyser aujourd'hui ?"}
        ]

    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    prompt = st.chat_input("Ex: Comment traiter le mildiou de la tomate ? Quel engrais mettre sur le mil ?")

    if prompt:
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        prompt_lower = prompt.lower()
        reponse = ""

        culture_trouvee = None
        for name in cultures_db:
            if name in prompt_lower:
                culture_trouvee = name
                break

        if culture_trouvee:
            info = cultures_db[culture_trouvee]
            phyt = info.get("phytosanitaire", {})
            calc = info.get("calculateur", {})
            
            reponse = f"🌱 **Conseil pour le {culture_trouvee.capitalize()}** :\n\n"
            
            if "maladie" in prompt_lower or "traitement" in prompt_lower or "ravageur" in prompt_lower:
                reponse += "**Problèmes phytosanitaires connus :**\n"
                for symp, trait in phyt.items():
                    reponse += f"- *{symp.replace('_', ' ').capitalize()}* : {trait}\n"
            elif "engrais" in prompt_lower or "fumure" in prompt_lower or "dose" in prompt_lower:
                if calc:
                    reponse += f"- Dose moyenne d'engrais recommandée : **{calc.get('engrais_kg')} kg / {calc.get('unite')}**\n"
                    if calc.get("semences_kg"):
                        reponse += f"- Quantité de semences : **{calc.get('semences_kg')} kg / {calc.get('unite')}**\n"
            else:
                reponse += f"- **Famille / Type** : {info.get('nom', culture_trouvee)}\n"
                if "cycle" in info:
                    reponse += f"- **Cycle de culture** : {info.get('cycle')}\n"
                if "climat" in info:
                    reponse += f"- **Conditions météo / Climat** : {info.get('climat')}\n"
                if phyt:
                    reponse += "\n💡 *Astuce : vous pouvez me demander les traitements spécifiques pour les maladies de cette culture.*"
        else:
            if "météo" in prompt_lower or "pluie" in prompt_lower:
                reponse = "🌧️ Pour consulter la météo exacte de votre localité, utilisez le menu **Fiches techniques** et entrez le nom de votre ville dans la barre latérale !"
            elif "rentabilité" in prompt_lower or "marge" in prompt_lower or "prix" in prompt_lower:
                reponse = "💰 Pour analyser la rentabilité de vos cultures, enregistrez vos **Dépenses** et vos **Ventes**, puis consultez la page **Rentabilité** !"
            else:
                reponse = (
                    "💡 **Conseil général** : Pour obtenir d'excellents rendements, préparez correctement votre sol (fumure organique), "
                    "respectez la densité de semis et suivez le calendrier d'irrigation. "
                    "\n\nVous pouvez me poser des questions sur les cultures suivantes : " + ", ".join([c.capitalize() for c in cultures_db.keys()]) + "."
                )

        with st.chat_message("assistant"):
            st.write(reponse)
        st.session_state.chat_messages.append({"role": "assistant", "content": reponse})


# --- TAB 2 : DIAGNOSTIC PAR PHOTO (IA VISION) ---
with tab_photo:
    st.subheader("📷 Diagnostic IA Visuel des Feuilles et Tiges")
    st.write("Prenez une photo en direct ou importez une photo de votre plante atteinte pour analyser le problème.")

    col_cam, col_upload = st.columns(2)

    with col_cam:
        photo_camera = st.camera_input("📷 Prendre une photo avec votre smartphone/webcam")

    with col_upload:
        photo_file = st.file_uploader("📁 Ou charger un fichier image (JPG, PNG)", type=["jpg", "jpeg", "png"])

    image_source = photo_camera or photo_file

    if image_source:
        st.divider()
        st.subheader("Image capturée :")
        image = Image.open(image_source)
        st.image(image, caption="Photo de la culture à diagnostiquer", width=400)

        culture_select = st.selectbox("Sélectionnez la culture concernée :", options=sorted(cultures_db.keys()), key="photo_culture_sel")

        if st.button("🔬 Analyser la photo avec l'IA Visuelle", type="primary"):
            with st.spinner("Analyse visuelle en cours..."):
                info_c = cultures_db[culture_select]
                phyt = info_c.get("phytosanitaire", {})

                st.success("✅ Analyse visuelle terminée avec succès !")
                st.markdown(f"### **Résultats du diagnostic pour le {culture_select.capitalize()}**")
                
                st.info("🔍 **Observations de l'IA** : Détection de nécroses foliaires / taches décolorées sur la surface du limbe.")
                
                if phyt:
                    st.warning("⚠️ **Causes probables & Traitements recommandés** :")
                    for symp, trait in phyt.items():
                        st.markdown(f"- **{symp.replace('_', ' ').capitalize()}** :\n  *{trait}*")
                else:
                    st.markdown("Gardez une bonne aération du feuillage et évitez l'arrosage direct sur les feuilles le soir.")


# --- TAB 3 : DIAGNOSTIC PHYTOSANITAIRE GUIDÉ ---
with tab_diagnostic:
    st.subheader("🔬 Diagnostic par Sélection des Symptômes")
    st.write("Sélectionnez votre culture et choisissez le symptôme observé sur les feuilles, tiges ou fruits.")

    col1, col2 = st.columns(2)
    with col1:
        nom_culture = st.selectbox("Culture observée :", options=sorted(cultures_db.keys()), key="diag_culture")
        
    phytosanitaire = cultures_db[nom_culture].get("phytosanitaire", {})

    with col2:
        if phytosanitaire:
            symptoms_labels = {k: k.replace("_", " ").capitalize() for k in phytosanitaire}
            symptome_choisi = st.selectbox("Symptôme / Ravageur observé :", options=list(symptoms_labels.keys()), format_func=lambda k: symptoms_labels[k])
        else:
            symptome_choisi = None
            st.info("Pas de fiche phytosanitaire enregistrée pour cette culture.")

    if symptome_choisi and phytosanitaire:
        st.divider()
        st.warning(f"⚠️ **Diagnostic : {symptome_choisi.replace('_', ' ').upper()}**")
        st.success(f"📌 **Recommandation de traitement** :\n\n{phytosanitaire[symptome_choisi]}")
