import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def generate_financial_pdf(exploitation_name, total_ca, total_depenses, benefice, parcelles_data):
    """Génère un document PDF propre et structuré contenant le bilan financier récapitulatif."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1b4332'),
        alignment=0
    )

    h2_style = ParagraphStyle(
        'Heading2Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#2d6a4f')
    )

    normal_style = styles['Normal']
    
    elements = []

    # En-tête du document
    elements.append(Paragraph(f"🌾 BILAN FINANCIER & COMPTABLE", title_style))
    elements.append(Paragraph(f"Exploitation : <b>{exploitation_name or 'Mon Exploitation'}</b>", normal_style))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1b4332'), spaceAfter=15))

    # Résumé global
    elements.append(Paragraph("Résumé financier global", h2_style))
    elements.append(Spacer(1, 5))

    kpi_data = [
        ["Chiffre d'Affaires Total", "Dépenses Totales", "Bénéfice Net Global"],
        [f"{total_ca:,.0f} FCFA", f"{total_depenses:,.0f} FCFA", f"{benefice:,.0f} FCFA"]
    ]

    t_kpi = Table(kpi_data, colWidths=[180, 180, 180])
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#475569')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TEXTCOLOR', (2, 1), (2, 1), colors.HexColor('#059669') if benefice >= 0 else colors.HexColor('#dc2626')),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, 1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1'))
    ]))
    elements.append(t_kpi)
    elements.append(Spacer(1, 20))

    # Tableau détaillé des campagnes
    elements.append(Paragraph("Détail par parcelle & campagne", h2_style))
    elements.append(Spacer(1, 8))

    table_data = [
        ["Parcelle", "Culture", "Superficie", "Dépenses", "Ventes", "Bénéfice"]
    ]

    for row in parcelles_data:
        table_data.append([
            row.get("Parcelle", ""),
            row.get("Culture", ""),
            f"{row.get('Superficie (ha)', 0)} ha",
            f"{row.get('Dépenses (FCFA)', 0):,.0f} F",
            f"{row.get('Chiffre d\'Affaires (FCFA)', 0):,.0f} F",
            f"{row.get('Bénéfice Net (FCFA)', 0):,.0f} F"
        ])

    t_detail = Table(table_data, colWidths=[100, 80, 70, 95, 95, 100])
    t_detail.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1b4332')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_detail)

    elements.append(Spacer(1, 30))
    elements.append(Paragraph("<i>Document généré automatiquement par l'Assistant Agricole Web</i>", styles['Italic']))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
