import streamlit as st


def apply_custom_theme():
    """Injecte du CSS personnalisé pour toute l'application (à appeler sur chaque page)."""
    custom_css = """
    <style>
    /* Importation de la police Google Inter */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    :root {
        --agri-primary: #1b4332;
        --agri-primary-light: #2d6a4f;
        --agri-accent: #d97706;
        --agri-bg-card: #ffffff;
        --agri-border: #e2e8f0;
        --agri-text: #1e293b;
    }

    /* En-têtes et titres */
    h1, h2, h3 {
        color: #1b4332 !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
    }

    /* MENU LATÉRAL - FOND SOMBRE + POLICE UNIFORME */
    section[data-testid="stSidebar"] {
        background-color: #1e293b !important;
        font-family: 'Inter', sans-serif !important;
    }

    section[data-testid="stSidebar"] > div {
        background-color: #1e293b !important;
    }

    section[data-testid="stSidebar"] * {
        color: #f1f5f9 !important;
        font-size: 0.92rem !important;
        font-family: 'Inter', sans-serif !important;
    }

    section[data-testid="stSidebar"] button,
    section[data-testid="stSidebar"] a,
    section[data-testid="stSidebar"] div[role="button"] {
        background-color: #334155 !important;
        color: #f1f5f9 !important;
        border-radius: 8px !important;
        padding: 6px 12px !important;
        margin: 4px 0 !important;
        min-height: 36px !important;
        font-size: 0.92rem !important;
        border: none !important;
    }

    section[data-testid="stSidebar"] button:hover,
    section[data-testid="stSidebar"] a:hover {
        background-color: #475569 !important;
        color: #4ade80 !important;
    }

    section[data-testid="stSidebar"] button[kind="primary"],
    section[data-testid="stSidebar"] a[aria-current="page"] {
        background-color: #0f766e !important;
        color: white !important;
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)


def render_kpi_card(title, value, subtitle="", icon="🌾", border_color="#2d6a4f"):
    """Génère une carte d'indicateur KPI stylisée (utile pour le futur tableau de bord)."""
    card_html = f"""
    <div class="agri-kpi-card" style="border-left: 5px solid {border_color};">
        <div class="agri-kpi-header">
            <span>{title}</span>
            <span style="font-size: 1.2rem;">{icon}</span>
        </div>
        <div class="agri-kpi-value">{value}</div>
        {'<div class="agri-kpi-sub">' + subtitle + '</div>' if subtitle else ''}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def get_badge_html(statut):
    """Retourne le HTML pour un badge de statut coloré (utile pour parcelles/campagnes)."""
    statut_clean = statut.lower()
    if "planifi" in statut_clean:
        cls = "badge-planifie"
    elif "cours" in statut_clean:
        cls = "badge-encours"
    elif "récolt" in statut_clean or "recolt" in statut_clean:
        cls = "badge-recolte"
    else:
        cls = "badge-termine"
    return f'<span class="agri-badge {cls}">{statut}</span>'