import streamlit as st
import database
import theme

st.set_page_config(page_title="Connexion", page_icon="🔐")
database.init_db()
theme.apply_custom_theme()

st.title("🔐 Connexion")

if "user_id" in st.session_state:
    st.success(f"Tu es déjà connecté en tant que **{st.session_state['username']}**.")
    if st.button("Se déconnecter"):
        del st.session_state["user_id"]
        del st.session_state["username"]
        st.rerun()
    st.stop()

tab_connexion, tab_inscription = st.tabs(["Se connecter", "Créer un compte"])

with tab_connexion:
    with st.form(key="form_connexion"):
        username = st.text_input("Nom d'utilisateur :")
        mot_de_passe = st.text_input("Mot de passe :", type="password")
        valider = st.form_submit_button("Se connecter")

        if valider:
            user_id = database.verifier_utilisateur(username, mot_de_passe)
            if user_id:
                st.session_state["user_id"] = user_id
                st.session_state["username"] = username
                st.success("Connexion réussie !")
                st.rerun()
            else:
                st.error("Nom d'utilisateur ou mot de passe incorrect.")

with tab_inscription:
    with st.form(key="form_inscription"):
        nouveau_username = st.text_input("Choisis un nom d'utilisateur :")
        nouveau_mdp = st.text_input("Choisis un mot de passe :", type="password")
        confirmation = st.text_input("Confirme le mot de passe :", type="password")
        creer = st.form_submit_button("Créer mon compte")

        if creer:
            if not nouveau_username or not nouveau_mdp:
                st.warning("Remplis tous les champs.")
            elif nouveau_mdp != confirmation:
                st.warning("Les mots de passe ne correspondent pas.")
            else:
                reussi = database.creer_utilisateur(nouveau_username, nouveau_mdp)
                if reussi:
                    st.success("Compte créé ! Tu peux maintenant te connecter dans l'onglet à côté.")
                else:
                    st.error("Ce nom d'utilisateur existe déjà.")
