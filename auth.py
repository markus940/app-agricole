import streamlit as st


def requiere_connexion():
    """À appeler en haut de chaque page protégée : redirige vers la connexion si non connecté."""
    if "user_id" not in st.session_state:
        st.warning("🔐 Tu dois être connecté pour accéder à cette page.")
        st.page_link("pages/0_connexion.py", label="Aller à la page de connexion", icon="🔐")
        st.stop()