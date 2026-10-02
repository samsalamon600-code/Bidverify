import os
import uuid
import datetime
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from backend.app.config import settings

def generate_vendor_pdf_report(
    vendor: Dict[str, Any],
    verification_results: list,
    compliance_checks: list,
    risk_assessment: Dict[str, Any],
    report_id: str = None
) -> str:
    """
    Generates a professional executive verification dossier in PDF using ReportLab.
    Saves to the configured reports/ directory and returns the absolute file path.
    """
    if not report_id:
        report_id = f"REP-{uuid.uuid4().hex[:8].upper()}"

    filename = f"Verification_Dossier_{vendor.get('id', 'X')}_{report_id}.pdf"
    file_path = os.path.join(settings.REPORT_DIR, filename)

    doc = SimpleDocTemplate(
        file_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0F172A')
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748B')
    )

    h2_style = ParagraphStyle(
        'Heading2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=12,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155')
    )

    bold_body_style = ParagraphStyle(
        'BoldBody',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#0F172A')
    )

    score_val_style = ParagraphStyle(
        'ScoreVal',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        alignment=1,  # Center
        textColor=colors.HexColor('#0F172A')
    )

    score_lbl_style = ParagraphStyle(
        'ScoreLbl',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        alignment=1,  # Center
        textColor=colors.HexColor('#64748B')
    )

    story = []

    # 1. Header with branding
    header_data = [
        [
            Paragraph("<b>BIDVERIFY</b> | Enterprise Procurement Verification", title_style),
            Paragraph(f"<b>REPORT ID:</b> {report_id}<br/><b>DATE:</b> {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", subtitle_style)
        ]
    ]
    header_table = Table(header_data, colWidths=[4.2 * inch, 3.0 * inch])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563EB'), spaceBefore=8, spaceAfter=12))

    # 2. Executive Score Strip
    comp_score = vendor.get('compliance_score', 0.0)
    risk_score = vendor.get('risk_score', 0.0)
    match_score = vendor.get('match_score', 0.0)
    ocr_conf = vendor.get('ocr_confidence', 0.0)
    anomaly_score = vendor.get('anomaly_score', 0.0)

    # Color codes
    risk_color = colors.HexColor('#16A34A') if risk_score <= 30 else (colors.HexColor('#D97706') if risk_score <= 60 else colors.HexColor('#DC2626'))
    comp_color = colors.HexColor('#16A34A') if comp_score >= 80 else (colors.HexColor('#D97706') if comp_score >= 60 else colors.HexColor('#DC2626'))

    score_boxes = [
        [
            Paragraph(f"<font color='{comp_color.hexval()}'>{comp_score:.1f}%</font>", score_val_style),
            Paragraph(f"<font color='{risk_color.hexval()}'>{risk_score:.1f}%</font>", score_val_style),
            Paragraph(f"{match_score:.1f}%", score_val_style),
            Paragraph(f"{ocr_conf:.1f}%", score_val_style),
            Paragraph(f"{anomaly_score:.2f}", score_val_style)
        ],
        [
            Paragraph("COMPLIANCE SCORE", score_lbl_style),
            Paragraph("RISK SCORE", score_lbl_style),
            Paragraph("DATA MATCH SCORE", score_lbl_style),
            Paragraph("OCR CONFIDENCE", score_lbl_style),
            Paragraph("ANOMALY SCORE (ML)", score_lbl_style)
        ]
    ]
    score_table = Table(score_boxes, colWidths=[1.44 * inch] * 5)
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 10))

    # 3. Vendor Profile Overview
    story.append(Paragraph("1. Vendor Identity & Corporate Overview", h2_style))
    v_info = [
        [Paragraph("<b>Company Legal Name:</b>", bold_body_style), Paragraph(vendor.get('name', 'N/A'), body_style),
         Paragraph("<b>Verification Status:</b>", bold_body_style), Paragraph(f"<b>{vendor.get('verification_status', 'Pending')}</b>", bold_body_style)],
        [Paragraph("<b>GSTIN:</b>", bold_body_style), Paragraph(vendor.get('gstin', 'N/A'), body_style),
         Paragraph("<b>Permanent Account No (PAN):</b>", bold_body_style), Paragraph(vendor.get('pan', 'N/A'), body_style)],
        [Paragraph("<b>CIN:</b>", bold_body_style), Paragraph(vendor.get('cin', 'N/A') or "Not Provided", body_style),
         Paragraph("<b>Udyam MSME No:</b>", bold_body_style), Paragraph(vendor.get('udyam_number', 'N/A') or "Not Provided", body_style)],
        [Paragraph("<b>Registered Address:</b>", bold_body_style), Paragraph(vendor.get('address', 'N/A'), body_style),
         Paragraph("<b>State / Pincode:</b>", bold_body_style), Paragraph(f"{vendor.get('state', '')} - {vendor.get('pincode', '')}", body_style)],
        [Paragraph("<b>Contact Details:</b>", bold_body_style), Paragraph(f"{vendor.get('contact_email', 'N/A')} | {vendor.get('contact_phone', 'N/A')}", body_style),
         Paragraph("<b>Turnover / Employees:</b>", bold_body_style), Paragraph(f"INR {vendor.get('turnover_cr', 0.0)} Cr | {vendor.get('employee_count', 0)} staff", body_style)]
    ]
    vendor_table = Table(v_info, colWidths=[1.7 * inch, 2.1 * inch, 1.8 * inch, 1.6 * inch])
    vendor_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F1F5F9')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#F1F5F9')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(vendor_table)
    story.append(Spacer(1, 10))

    # 4. Cross-Verification Matrix
    story.append(Paragraph("2. Cross-Verification & Registry Match Matrix", h2_style))
    matrix_rows = [
        [
            Paragraph("<b>Verification Field</b>", bold_body_style),
            Paragraph("<b>Document Value (OCR)</b>", bold_body_style),
            Paragraph("<b>Government Registry Record</b>", bold_body_style),
            Paragraph("<b>Match Status</b>", bold_body_style),
            Paragraph("<b>Similarity</b>", bold_body_style)
        ]
    ]
    for r in verification_results:
        m_type = r.get('match_type', 'MISMATCH')
        m_color = colors.HexColor('#16A34A') if m_type == 'EXACT' else (colors.HexColor('#D97706') if m_type == 'PARTIAL' else colors.HexColor('#DC2626'))
        matrix_rows.append([
            Paragraph(r.get('field_name', ''), body_style),
            Paragraph(str(r.get('doc_value', ''))[:40], body_style),
            Paragraph(str(r.get('portal_value', ''))[:40], body_style),
            Paragraph(f"<font color='{m_color.hexval()}'><b>{m_type}</b></font>", body_style),
            Paragraph(f"{r.get('similarity_score', 0.0)}%", body_style)
        ])

    matrix_table = Table(matrix_rows, colWidths=[1.5 * inch, 2.0 * inch, 2.0 * inch, 1.0 * inch, 0.7 * inch])
    matrix_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E2E8F0')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(matrix_table)
    story.append(Spacer(1, 10))

    # 5. Risk Assessment & Recommended Action
    story.append(Paragraph("3. Multi-Factor Risk Assessment & Recommended Action", h2_style))
    factors = risk_assessment.get('factors', [])
    factor_rows = [
        [
            Paragraph("<b>Risk Dimension</b>", bold_body_style),
            Paragraph("<b>Weight</b>", bold_body_style),
            Paragraph("<b>Raw Risk</b>", bold_body_style),
            Paragraph("<b>Weighted Impact</b>", bold_body_style),
            Paragraph("<b>Finding Status</b>", bold_body_style)
        ]
    ]
    for f in factors:
        st_val = f.get('status', 'PASS')
        s_color = colors.HexColor('#16A34A') if st_val == 'PASS' else (colors.HexColor('#D97706') if st_val == 'ELEVATED' else colors.HexColor('#DC2626'))
        factor_rows.append([
            Paragraph(f.get('factor_name', ''), body_style),
            Paragraph(f"{f.get('weight_percent', 0)}%", body_style),
            Paragraph(f"{f.get('raw_risk', 0.0)}%", body_style),
            Paragraph(f"{f.get('weighted_impact', 0.0)}%", body_style),
            Paragraph(f"<font color='{s_color.hexval()}'><b>{st_val}</b></font>", body_style)
        ])

    factor_table = Table(factor_rows, colWidths=[2.8 * inch, 0.9 * inch, 1.1 * inch, 1.2 * inch, 1.2 * inch])
    factor_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E2E8F0')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(factor_table)
    story.append(Spacer(1, 8))

    rec_action = risk_assessment.get('recommended_action', 'Proceed with standard procurement workflow.')
    action_box = [
        [Paragraph(f"<b>RECOMMENDED PROCUREMENT ACTION:</b><br/>{rec_action}", bold_body_style)]
    ]
    action_table = Table(action_box, colWidths=[7.2 * inch])
    action_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#EFF6FF')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#3B82F6')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(action_table)
    story.append(Spacer(1, 10))

    # 6. Audit & Ethical Sign-Off
    story.append(Paragraph("4. Explainability & Human-in-the-Loop Sign-Off", h2_style))
    disclaimer = (
        "<i>Notice: This automated report is generated by Bidverify AI Decision Support Systems. "
        "The scoring engines assist authorized procurement personnel and do not make autonomous purchasing "
        "or rejection determinations. Findings indicate pattern consistency with official registries.</i>"
    )
    story.append(Paragraph(disclaimer, body_style))
    story.append(Spacer(1, 14))

    sign_data = [
        [
            Paragraph("<b>Verified By:</b> ___________________________<br/>Procurement Verification Officer", body_style),
            Paragraph("<b>Approved By:</b> ___________________________<br/>Chief Procurement Officer (CPO)", body_style),
            Paragraph("<b>Digital Audit Hash:</b><br/>" + str(uuid.uuid4()).upper()[:16], body_style)
        ]
    ]
    sign_table = Table(sign_data, colWidths=[2.5 * inch, 2.5 * inch, 2.2 * inch])
    sign_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(sign_table)

    # Build PDF
    doc.build(story)
    return file_path
