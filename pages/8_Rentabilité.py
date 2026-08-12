import io
import pandas as pd
import streamlit as st
import database
import theme
import pdf_generator

st.set_page_config(page_title="Rentabilité", page_icon="📊", layout="wide")


database.init_db()
theme.apply_custom_theme()

import auth
auth.requiere_connexion()

user_id = st.session_state["user_id"]

st.title("📊 Rentabilité & Bilans Financiers")
st.caption("Analyse du bilan économique par campagne : coûts de production, chiffre d'affaires, marge brute et coût de revient au kilo.")

exploitation = database.get_exploitation(user_id)
campagnes = database.get_campagnes(user_id)
all_depenses = database.get_depenses(user_id)
all_recoltes = database.get_recoltes(user_id)
all_ventes = database.get_ventes(user_id)

if not campagnes:
    st.warning("⚠️ Vous devez d'abord créer au moins une campagne dans la page **Campagnes**.")
    st.stop()

bilan_data = []

for c in campagnes:
    nom_parcelle = c["parcelle"]
    culture = c["culture"]
    superficie = c["superficie"]
    statut = c["statut"]

    depenses_c = [d for d in all_depenses if d["campagne"] == nom_parcelle]
    recoltes_c = [r for r in all_recoltes if r["campagne"] == nom_parcelle]
    ventes_c = [v for v in all_ventes if v["campagne"] == nom_parcelle]

    total_depenses = sum(d["montant"] for d in depenses_c)
    total_recolte_kg = sum(r["quantite_kg"] for r in recoltes_c)
    total_ca = sum(v["montant"] for v in ventes_c)

    benefice = total_ca - total_depenses
    marge_pct = (benefice / total_ca * 100) if total_ca > 0 else 0.0
    cout_par_kg = (total_depenses / total_recolte_kg) if total_recolte_kg > 0 else 0.0
    rendement_kg_ha = (total_recolte_kg / superficie) if superficie > 0 else 0.0

    bilan_data.append({
        "Parcelle": nom_parcelle,
        "Culture": culture.capitalize(),
        "Superficie (ha)": superficie,
        "Statut": statut,
        "Dépenses (FCFA)": total_depenses,
        "Récolte (kg)": total_recolte_kg,
        "Chiffre d'Affaires (FCFA)": total_ca,
        "Bénéfice Net (FCFA)": benefice,
        "Marge (%)": round(marge_pct, 1),
        "Coût de revient (FCFA/kg)": round(cout_par_kg, 1),
        "Rendement (kg/ha)": round(rendement_kg_ha, 1)
    })

st.subheader("📥 Exporter le bilan comptable")

df_bilan = pd.DataFrame(bilan_data)
total_ca_global = sum(d["Chiffre d'Affaires (FCFA)"] for d in bilan_data)
total_dep_global = sum(d["Dépenses (FCFA)"] for d in bilan_data)
benefice_global = total_ca_global - total_dep_global

col_exp1, col_exp2, col_exp3 = st.columns(3)

with col_exp1:
    buffer_excel = io.BytesIO()
    with pd.ExcelWriter(buffer_excel, engine="openpyxl") as writer:
        df_bilan.to_excel(writer, sheet_name="Bilan_Rentabilite", index=False)
    buffer_excel.seek(0)

    st.download_button(
        label="📊 Bilan Excel (.xlsx)",
        data=buffer_excel,
        file_name="Bilan_Agricole_Rentabilite.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

with col_exp2:
    csv_data = df_bilan.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="📄 Bilan CSV (.csv)",
        data=csv_data,
        file_name="Bilan_Agricole_Rentabilite.csv",
        mime="text/csv",
        use_container_width=True
    )

with col_exp3:
    pdf_bytes = pdf_generator.generate_financial_pdf(
        exploitation.get("nom", "Mon Exploitation"),
        total_ca_global,
        total_dep_global,
        benefice_global,
        bilan_data
    )
    st.download_button(
        label="📄 Imprimer Rapport PDF (.pdf)",
        data=pdf_bytes,
        file_name="Rapport_Financier_Agricole.pdf",
        mime="application/pdf",
        use_container_width=True,
        type="primary"
    )

st.divider()

st.subheader("Détail par campagne")

for row in bilan_data:
    with st.container(border=True):
        st.markdown(f"### **{row['Parcelle']}** — {row['Culture']}")
        st.markdown(f"Superficie : **{row['Superficie (ha)']} ha** | Statut : {theme.get_badge_html(row['Statut'])}", unsafe_allow_html=True)
        st.markdown(" ")

        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Dépenses Totales", f"{row['Dépenses (FCFA)']:,.0f} FCFA".replace(",", " "))
        col2.metric("💵 Chiffre d'Affaires", f"{row['Chiffre d\'Affaires (FCFA)']:,.0f} FCFA".replace(",", " "))

        marge_label = f"{row['Marge (%)']}% de marge" if row["Chiffre d'Affaires (FCFA)"] > 0 else "0% de marge"
        col3.metric(
            "📈 Bénéfice Net",
            f"{row['Bénéfice Net (FCFA)']:,.0f} FCFA".replace(",", " "),
            delta=marge_label if row['Bénéfice Net (FCFA)'] >= 0 else f"-{marge_label}"
        )

        col4, col5 = st.columns(2)
        rendement_str = f"{row['Rendement (kg/ha)']:,.0f} kg/ha".replace(",", " ") if row['Rendement (kg/ha)'] > 0 else "—"
        col4.metric("🌾 Rendement réel", rendement_str)

        cout_kg_str = f"{row['Coût de revient (FCFA/kg)']:,.0f} FCFA/kg".replace(",", " ") if row['Coût de revient (FCFA/kg)'] > 0 else "—"
        col5.metric("💸 Coût de revient par kg", cout_kg_str)
