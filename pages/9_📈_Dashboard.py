import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import database
import theme

st.set_page_config(page_title="Dashboard", page_icon="📈", layout="wide")
database.init_db()
theme.apply_custom_theme()

import auth
auth.requiere_connexion()

user_id = st.session_state["user_id"]

st.title("📈 Tableau de Bord & Graphiques Analytiques")
st.caption("Vue d'ensemble et visualisations interactives de la santé financière et technique de l'exploitation.")

parcelles = database.get_parcelles(user_id)
campagnes = database.get_campagnes(user_id)
depenses = database.get_depenses(user_id)
ventes = database.get_ventes(user_id)
recoltes = database.get_recoltes(user_id)

if not campagnes:
    st.warning("⚠️ Vous devez d'abord créer au moins une campagne dans la page **Campagnes**.")
    st.stop()

# --- Chiffres Clés Consolidés ---
superficie_totale = sum(p["superficie"] for p in parcelles) if parcelles else 0.0
total_depenses = sum(d["montant"] for d in depenses)
total_ca = sum(v["montant"] for v in ventes)
total_recolte_kg = sum(r["quantite_kg"] for r in recoltes)
benefice = total_ca - total_depenses

col1, col2, col3, col4 = st.columns(4)
with col1:
    theme.render_kpi_card("Superficie Totale", f"{superficie_totale:g} ha", f"{len(parcelles)} parcelle(s)", icon="🌾")

with col2:
    theme.render_kpi_card("Dépenses Totales", f"{total_depenses:,.0f} FCFA".replace(",", " "), icon="💰", border_color="#d97706")

with col3:
    theme.render_kpi_card("Chiffre d'Affaires", f"{total_ca:,.0f} FCFA".replace(",", " "), icon="💵", border_color="#059669")

with col4:
    color_b = "#059669" if benefice >= 0 else "#dc2626"
    theme.render_kpi_card("Bénéfice Net Global", f"{benefice:,.0f} FCFA".replace(",", " "), icon="📈", border_color=color_b)

st.divider()

# --- GRAPHIQUES PLOTLY INTERACTIFS ---
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.subheader("💰 Répartition des Dépenses par Catégorie")
    if depenses:
        df_depenses = pd.DataFrame(depenses)
        dep_cat = df_depenses.groupby("categorie")["montant"].sum().reset_index()
        fig_pie = px.pie(
            dep_cat,
            names="categorie",
            values="montant",
            color_discrete_sequence=px.colors.sequential.Greens_r,
            hole=0.4
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("Aucune dépense enregistrée pour afficher le camembert.")

with row1_col2:
    st.subheader("💵 Chiffre d'Affaires par Culture")
    if ventes:
        df_ventes = pd.DataFrame(ventes)
        ventes_culture = df_ventes.groupby("culture")["montant"].sum().reset_index()
        ventes_culture["culture"] = ventes_culture["culture"].str.capitalize()
        fig_bar = px.bar(
            ventes_culture,
            x="culture",
            y="montant",
            labels={"culture": "Culture", "montant": "Revenu (FCFA)"},
            color="montant",
            color_continuous_scale="Greens"
        )
        fig_bar.update_layout(margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Aucune vente enregistrée pour afficher l'histogramme.")

st.divider()

row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.subheader("🌾 Récoltes Cumulées par Parcelle (kg)")
    if recoltes:
        df_recoltes = pd.DataFrame(recoltes)
        rec_parcelle = df_recoltes.groupby("campagne")["quantite_kg"].sum().reset_index()
        fig_rec = px.bar(
            rec_parcelle,
            x="campagne",
            y="quantite_kg",
            labels={"campagne": "Parcelle / Campagne", "quantite_kg": "Quantité (kg)"},
            color_discrete_sequence=["#2d6a4f"]
        )
        fig_rec.update_layout(margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_rec, use_container_width=True)
    else:
        st.info("Aucune récolte enregistrée pour le moment.")

with row2_col2:
    st.subheader("📊 Comparatif Coûts vs Recettes")
    if depenses or ventes:
        fig_comp = go.Figure(data=[
            go.Bar(name='Dépenses Totales', x=['Exploitation'], y=[total_depenses], marker_color='#d97706'),
            go.Bar(name='Chiffre d\'Affaires', x=['Exploitation'], y=[total_ca], marker_color='#059669')
        ])
        fig_comp.update_layout(barmode='group', margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_comp, use_container_width=True)
    else:
        st.info("Saisissez vos dépenses et ventes pour voir le comparatif.")