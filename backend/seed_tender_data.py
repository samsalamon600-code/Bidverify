"""
seed_tender_data.py
Populates the BidVerify platform with official production-grade procurement records:
1. Procurement Officer: narsingh@gmail.com / narsing@
2. Three Bidders:
   - Sam tech: samtech@gmail.com / narsing@ (Tender 3: Renewable-Energy Equipment)
   - Swasthika industry: swasthika@gmail.com / narsing@ (Tender 1: Networking Equipment)
   - Mokshi laboratory: mokshi@gmail.com / narsing@ (Tender 2: Laboratory Equipment)
3. Three Tenders:
   - TDR-01-NET-2026: Networking Equipment (24-port managed network switch) -> LOW RISK (Compliant)
   - OCT-02-LAB-2026: Laboratory Equipment (Digital weighing balance) -> HIGH RISK (Critical Exceptions)
   - TDR-03-SOLAR-2026: Renewable-Energy Equipment (Solar LED street light) -> MEDIUM RISK (Manual Review Required)
4. Realistic PDF document files generated on disk with ReportLab.
5. Structured technical requirements, compliance results, evidence, and risk analysis records.
"""

import os
import sys
import json
from datetime import datetime, timezone

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from werkzeug.security import generate_password_hash

from backend.config import Config
from backend.extensions import db
from backend.models.models import (
    Role,
    User,
    Officer,
    Company,
    Tender,
    TenderRequirement,
    Bid,
    BidItem,
    Document,
    DocumentExtraction,
    ComplianceResult,
    RiskResult,
    Evidence,
    AuditLog,
)
from backend.services.audit_service import record_audit_log


def utc_now():
    return datetime.now(timezone.utc)


def generate_pdf_doc(filename: str, title: str, subtitle: str, metadata: dict, sections: list) -> tuple[str, int, int]:
    """Generates a professional, genuine PDF document using ReportLab."""
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    pdf_path = os.path.join(Config.UPLOAD_FOLDER, filename)
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#0f2942'),
        alignment=1,
        fontName='Helvetica-Bold'
    )
    sub_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#526071'),
        alignment=1
    )
    h2_style = ParagraphStyle(
        'DocH2',
        parent=styles['Heading2'],
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#1e3a5f'),
        fontName='Helvetica-Bold'
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#1e293b')
    )

    story = []
    # Header Banner
    story.append(Paragraph("GOVERNMENT OF INDIA &bull; GOVERNMENT E-MARKETPLACE (GeM)", sub_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(title, title_style))
    if subtitle:
        story.append(Spacer(1, 3))
        story.append(Paragraph(subtitle, sub_style))
    story.append(Spacer(1, 14))

    # Metadata Box
    meta_data = []
    meta_keys = list(metadata.keys())
    for i in range(0, len(meta_keys), 2):
        row = []
        k1 = meta_keys[i]
        row.append(Paragraph(f"<b>{k1}:</b> {metadata[k1]}", body_style))
        if i + 1 < len(meta_keys):
            k2 = meta_keys[i + 1]
            row.append(Paragraph(f"<b>{k2}:</b> {metadata[k2]}", body_style))
        else:
            row.append("")
        meta_data.append(row)

    if meta_data:
        meta_table = Table(meta_data, colWidths=[260, 260])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 14))

    # Sections
    for heading, content in sections:
        story.append(Paragraph(heading, h2_style))
        story.append(Spacer(1, 4))
        if isinstance(content, list) and content and isinstance(content[0], (list, tuple)):
            # Table content
            formatted_data = []
            for r_idx, row in enumerate(content):
                f_row = []
                for cell in row:
                    f_row.append(Paragraph(str(cell), body_style))
                formatted_data.append(f_row)
            col_count = len(content[0])
            col_w = 520 / col_count
            t = Table(formatted_data, colWidths=[col_w] * col_count)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ]))
            story.append(t)
        else:
            story.append(Paragraph(str(content), body_style))
        story.append(Spacer(1, 10))

    # Footer verification notice
    story.append(Spacer(1, 10))
    story.append(Paragraph("<i>This electronic document was submitted and verified under the GeM statutory procurement verification framework.</i>", sub_style))

    doc.build(story)
    size_bytes = os.path.getsize(pdf_path)
    page_count = 1 if len(sections) <= 3 else 2
    return pdf_path, size_bytes, page_count


def seed_procurement_data():
    """Populates all requested accounts, tenders, bids, documents, and compliance results."""
    print("Beginning BidVerify production database configuration...")

    # 1. ROLES
    role_officer = Role.query.filter_by(name="PROCUREMENT_OFFICER").first()
    if not role_officer:
        role_officer = Role(name="PROCUREMENT_OFFICER", description="Procurement Officer Role")
        db.session.add(role_officer)
        db.session.flush()

    role_company = Role.query.filter_by(name="COMPANY").first()
    if not role_company:
        role_company = Role(name="COMPANY", description="Offering Company / Bidder Role")
        db.session.add(role_company)
        db.session.flush()

    # 2. PROCUREMENT OFFICER: narsingh@gmail.com / narsing@
    officer_user = User.query.filter_by(email="narsingh@gmail.com").first()
    if not officer_user:
        officer_user = User(
            email="narsingh@gmail.com",
            password_hash=generate_password_hash("narsing@"),
            full_name="Narsingh",
            role_id=role_officer.id,
            role_name="PROCUREMENT_OFFICER",
            is_active=True,
        )
        db.session.add(officer_user)
        db.session.flush()
    else:
        officer_user.password_hash = generate_password_hash("narsing@")
        officer_user.role_id = role_officer.id
        officer_user.role_name = "PROCUREMENT_OFFICER"
        officer_user.is_active = True

    officer_profile = Officer.query.filter_by(user_id=officer_user.id).first()
    if not officer_profile:
        officer_profile = Officer(
            user_id=officer_user.id,
            employee_id="GEM-OFF-2101",
            department="Central Procurement Division",
            designation="Senior Procurement Officer",
            ministry="Ministry of Commerce & Industry (GeM)",
            phone="+91-11-23061000",
        )
        db.session.add(officer_profile)
    else:
        officer_profile.department = "Central Procurement Division"
        officer_profile.designation = "Senior Procurement Officer"
    db.session.flush()

    # 3. THREE BIDDERS
    # Bidder 1: Sam tech (for Tender 3)
    # Bidder 2: Swasthika industry (for Tender 1)
    # Bidder 3: Mokshi laboratory (for Tender 2)
    bidders_data = [
        {
            "key": "samtech",
            "name": "Sam tech",
            "company_name": "Sam Tech",
            "email": "samtech@gmail.com",
            "gstin": "36AAECS4321B1Z3",
            "pan": "AAECS4321B",
            "udyam": "UDYAM-TS-09-0014321",
            "etype": "Small Enterprise",
            "lc": 60.0,
            "address": "Plot 14, Hi-Tech City, Madhapur, Hyderabad, Telangana - 500081",
            "phone": "+91-9849012345",
        },
        {
            "key": "swasthika",
            "name": "Swasthika industry",
            "company_name": "Swasthika industry Private Limited",
            "email": "swasthika@gmail.com",
            "gstin": "29AAGCS1234F1Z8",
            "pan": "AAGCS1234F",
            "udyam": "UDYAM-KR-03-0045678",
            "etype": "Medium Enterprise",
            "lc": 65.0,
            "address": "Phase 1, Peenya Industrial Area, Bengaluru, Karnataka - 560058",
            "phone": "+91-9880054321",
        },
        {
            "key": "mokshi",
            "name": "Mokshi laboratory",
            "company_name": "Mokshi Laboratory",
            "email": "mokshi@gmail.com",
            "gstin": "27AABCM5678D1Z2",
            "pan": "AABCM5678D",
            "udyam": "UDYAM-MH-01-0056789",
            "etype": "Small Enterprise",
            "lc": 50.0,
            "address": "MIDC Industrial Area, Turbhe, Navi Mumbai, Maharashtra - 400705",
            "phone": "+91-9820067890",
        },
    ]

    bidder_companies = {}
    for b_info in bidders_data:
        u = User.query.filter_by(email=b_info["email"]).first()
        if not u:
            u = User(
                email=b_info["email"],
                password_hash=generate_password_hash("narsing@"),
                full_name=b_info["name"],
                role_id=role_company.id,
                role_name="COMPANY",
                is_active=True,
            )
            db.session.add(u)
            db.session.flush()
        else:
            u.password_hash = generate_password_hash("narsing@")
            u.full_name = b_info["name"]
            u.role_id = role_company.id
            u.role_name = "COMPANY"
            u.is_active = True

        comp = Company.query.filter_by(user_id=u.id).first()
        if not comp:
            comp = Company(
                user_id=u.id,
                company_name=b_info["company_name"],
                registration_number=f"U{u.id:05d}DL2019PTC340000",
                gstin=b_info["gstin"],
                pan=b_info["pan"],
                udyam_number=b_info["udyam"],
                enterprise_type=b_info["etype"],
                incorporation_year=2019,
                local_content_percent=b_info["lc"],
                address=b_info["address"],
                contact_phone=b_info["phone"],
                is_msme=True,
                is_startup=False,
            )
            db.session.add(comp)
        else:
            comp.company_name = b_info["company_name"]
            comp.gstin = b_info["gstin"]
            comp.pan = b_info["pan"]
            comp.udyam_number = b_info["udyam"]
            comp.enterprise_type = b_info["etype"]
            comp.local_content_percent = b_info["lc"]
            comp.address = b_info["address"]
            comp.contact_phone = b_info["phone"]
        db.session.flush()
        bidder_companies[b_info["key"]] = comp

    # 4. THREE TENDERS
    # Tender 1: TDR-01-NET-2026
    # Tender 2: OCT-02-LAB-2026
    # Tender 3: TDR-03-SOLAR-2026
    std_docs_list = json.dumps([
        "Technical Bid",
        "GST Certificate",
        "PAN",
        "Udyam/MSME Certificate",
        "OEM Authorization",
    ])

    tenders_spec = [
        {
            "key": "t1",
            "code": "TDR-01-NET-2026",
            "title": "Procurement of 24-Port Managed Network Switches",
            "category": "Networking Equipment",
            "department": "Department of Telecommunications & IT Infrastructure",
            "desc": "Supply, installation, and commissioning of 24-port managed network switches with Gigabit ports, VLAN segmentation, Quality of Service (QoS), standard 19-inch rack mounting kit, and 3-year comprehensive warranty.",
            "est_val": 4500000.0,
            "pub_date": "2026-10-01",
            "close_date": "2026-11-20",
            "lc": 50.0,
            "tech_req": "24 Gigabit ports, VLAN, Quality of Service (QoS), Rack mounting, Three-year warranty, Delivery within 30 calendar days.",
            "stat_req": "Active 15-digit GSTIN, Valid Corporate PAN, Udyam MSME Certificate, EPFO & ESIC statutory compliance.",
            "oem_req": "Tender-specific Manufacturer Authorization Form (MAF) from OEM.",
            "company_key": "swasthika",
            "struct_reqs": [
                ("Gigabit Ports", ">=", "24", "Ports", "24 Gigabit Ethernet ports"),
                ("VLAN Support", "==", "Supported", "", "802.1Q VLAN support"),
                ("Quality of Service (QoS)", "==", "Supported", "", "Quality of Service (QoS) traffic prioritization"),
                ("Mounting", "==", "Rack Mounting", "", "Standard 19-inch rack mounting"),
                ("Warranty", ">=", "3", "Years", "Three-year comprehensive warranty"),
                ("Delivery Time", "<=", "30", "Days", "Delivery within 30 calendar days"),
            ],
        },
        {
            "key": "t2",
            "code": "OCT-02-LAB-2026",
            "title": "Procurement of Precision Digital Weighing Balances",
            "category": "Laboratory Equipment",
            "department": "Department of Science & Technology - National Research Laboratories",
            "desc": "Supply, calibration, and delivery of precision digital weighing balances with 0.01 g readability, tare function, calibration capability, overload protection mechanism, and 2-year warranty.",
            "est_val": 2500000.0,
            "pub_date": "2026-10-01",
            "close_date": "2026-11-25",
            "lc": 50.0,
            "tech_req": "0.01 g readability, Tare function, Calibration capability, Overload protection, Two-year warranty, Delivery within 45 calendar days.",
            "stat_req": "Active GSTIN, Valid PAN, Udyam MSME Certificate, Labour Statutory compliance.",
            "oem_req": "Valid tender-specific OEM Authorization Form (MAF) from manufacturer.",
            "company_key": "mokshi",
            "struct_reqs": [
                ("Readability", "<=", "0.01", "g", "0.01 g readability precision threshold"),
                ("Tare Function", "==", "Supported", "", "Tare function support"),
                ("Calibration Capability", "==", "Supported", "", "Internal / automatic calibration capability"),
                ("Overload Protection", "==", "Supported", "", "Overload protection mechanism"),
                ("Warranty", ">=", "2", "Years", "Two-year comprehensive warranty"),
                ("Delivery Time", "<=", "45", "Days", "Delivery within 45 calendar days"),
            ],
        },
        {
            "key": "t3",
            "code": "TDR-03-SOLAR-2026",
            "title": "Procurement of Standalone Solar LED Street Lights",
            "category": "Renewable-Energy Equipment",
            "department": "Ministry of New and Renewable Energy (MNRE)",
            "desc": "Design, supply, installation, and commissioning of standalone integrated solar LED street lighting systems with 60 W LED luminaire, lithium battery, dusk-to-dawn control, IP65 weatherproof enclosure, and 3-year warranty.",
            "est_val": 6000000.0,
            "pub_date": "2026-10-01",
            "close_date": "2026-11-30",
            "lc": 50.0,
            "tech_req": "60 W LED, Lithium battery, Dusk-to-dawn control, IP65 enclosure, Three-year warranty, Delivery within 60 calendar days.",
            "stat_req": "Active GSTIN, Valid PAN, Udyam MSME Certificate, EPFO/ESIC compliance.",
            "oem_req": "Tender-specific OEM Authorization Form with clear validity date and authorized signature.",
            "company_key": "samtech",
            "struct_reqs": [
                ("LED Luminaire", ">=", "60", "W", "60 W LED luminaire rating"),
                ("Battery Type", "==", "Lithium Battery", "", "Lithium battery (LiFePO4)"),
                ("Dusk-to-Dawn Control", "==", "Supported", "", "Dusk-to-dawn automatic control"),
                ("Enclosure Rating", "==", "IP65 Enclosure", "", "IP65 weatherproof enclosure"),
                ("Warranty", ">=", "3", "Years", "Three-year warranty"),
                ("Delivery Time", "<=", "60", "Days", "Delivery within 60 calendar days"),
            ],
        },
    ]

    tenders_dict = {}
    for t_spec in tenders_spec:
        t = Tender.query.filter_by(tender_code=t_spec["code"]).first()
        if not t:
            t = Tender(
                tender_code=t_spec["code"],
                title=t_spec["title"],
                category=t_spec["category"],
                department=t_spec["department"],
                description=t_spec["desc"],
                estimated_value=t_spec["est_val"],
                publication_date=t_spec["pub_date"],
                closing_date=t_spec["close_date"],
                local_content_requirements=t_spec["lc"],
                technical_requirements=t_spec["tech_req"],
                statutory_requirements=t_spec["stat_req"],
                oem_requirements=t_spec["oem_req"],
                required_documents=std_docs_list,
                status="PUBLISHED",
                created_by=officer_user.id,
            )
            db.session.add(t)
            db.session.flush()
        else:
            t.title = t_spec["title"]
            t.category = t_spec["category"]
            t.department = t_spec["department"]
            t.description = t_spec["desc"]
            t.estimated_value = t_spec["est_val"]
            t.local_content_requirements = t_spec["lc"]
            t.technical_requirements = t_spec["tech_req"]
            t.statutory_requirements = t_spec["stat_req"]
            t.oem_requirements = t_spec["oem_req"]
            t.required_documents = std_docs_list
            t.status = "PUBLISHED"
            db.session.flush()

        # Update structured requirements
        TenderRequirement.query.filter_by(tender_id=t.id).delete()
        for p_name, op, val, unit, desc in t_spec["struct_reqs"]:
            tr = TenderRequirement(
                tender_id=t.id,
                category="TECHNICAL",
                parameter_name=p_name,
                operator=op,
                required_value=val,
                unit=unit,
                is_mandatory=True,
                description=desc,
            )
            db.session.add(tr)
        db.session.flush()
        tenders_dict[t_spec["key"]] = t

    # 5. CREATE BIDS, DOCUMENTS & COMPLIANCE FINDINGS
    # -------------------------------------------------------------
    # TENDER 1 BID: Swasthika industry Private Limited -> LOW RISK
    # -------------------------------------------------------------
    t1 = tenders_dict["t1"]
    comp1 = bidder_companies["swasthika"]
    bid1 = Bid.query.filter_by(tender_id=t1.id, company_id=comp1.id).first()
    if not bid1:
        bid1 = Bid(
            bid_number="GEM-BID-2026-NET01",
            tender_id=t1.id,
            company_id=comp1.id,
            quoted_amount=4180000.0,
            warranty_years=3.0,
            delivery_days=25,
            local_content_declared=65.0,
            oem_status="Authorized OEM Partner with MAF",
            product_name="Swasthika NetSwitch 24G Enterprise Switch",
            product_model="SNS-24G-MGD",
            technical_summary="24 Gigabit Ethernet Managed Network Switch with 802.1Q VLAN, Advanced QoS, 19-inch rack mounting kit, 3-year onsite warranty, and 25-day delivery.",
            declarations_accepted=True,
            submission_status="SUBMITTED",
            verification_status="VERIFIED",
            officer_review_status="VERIFIED",
            officer_review_comments="All required documents are present. Bidder identity information is consistent. Technical requirements are satisfied. Warranty and delivery commitments meet the requirement. OEM authorization matches the bidder, product, and tender.",
            reviewed_by=officer_user.id,
            reviewed_at=utc_now(),
            overall_compliance_score=100.0,
            document_compliance_score=100.0,
            statutory_compliance_score=100.0,
            technical_compliance_score=100.0,
            tender_compliance_score=100.0,
            risk_level="LOW",
        )
        db.session.add(bid1)
        db.session.flush()
    else:
        bid1.quoted_amount = 4180000.0
        bid1.warranty_years = 3.0
        bid1.delivery_days = 25
        bid1.local_content_declared = 65.0
        bid1.product_name = "Swasthika NetSwitch 24G Enterprise Switch"
        bid1.product_model = "SNS-24G-MGD"
        bid1.overall_compliance_score = 100.0
        bid1.document_compliance_score = 100.0
        bid1.statutory_compliance_score = 100.0
        bid1.technical_compliance_score = 100.0
        bid1.tender_compliance_score = 100.0
        bid1.risk_level = "LOW"
        bid1.verification_status = "VERIFIED"
        bid1.officer_review_status = "VERIFIED"
        bid1.officer_review_comments = "All required documents are present. Bidder identity information is consistent. Technical requirements are satisfied. Warranty and delivery commitments meet the requirement. OEM authorization matches the bidder, product, and tender."
        db.session.flush()

    # Clear previous sub-records for clean idempotent seed
    Evidence.query.filter_by(bid_id=bid1.id).delete()
    ComplianceResult.query.filter_by(bid_id=bid1.id).delete()
    RiskResult.query.filter_by(bid_id=bid1.id).delete()
    Document.query.filter_by(bid_id=bid1.id).delete()
    BidItem.query.filter_by(bid_id=bid1.id).delete()
    db.session.flush()

    # BidItems for Bid 1
    db.session.add_all([
        BidItem(bid_id=bid1.id, item_category="TECHNICAL", parameter_name="Gigabit Ports", submitted_value="24", unit="Ports", source_document="Swasthika_Technical_Bid.pdf", source_page=2),
        BidItem(bid_id=bid1.id, item_category="TECHNICAL", parameter_name="VLAN Support", submitted_value="Supported", unit="", source_document="Swasthika_Technical_Bid.pdf", source_page=2),
        BidItem(bid_id=bid1.id, item_category="TECHNICAL", parameter_name="Quality of Service (QoS)", submitted_value="Supported", unit="", source_document="Swasthika_Technical_Bid.pdf", source_page=2),
        BidItem(bid_id=bid1.id, item_category="TECHNICAL", parameter_name="Mounting", submitted_value="Rack Mounting", unit="", source_document="Swasthika_Technical_Bid.pdf", source_page=3),
        BidItem(bid_id=bid1.id, item_category="TECHNICAL", parameter_name="Warranty", submitted_value="3", unit="Years", source_document="Swasthika_Technical_Bid.pdf", source_page=3),
        BidItem(bid_id=bid1.id, item_category="TECHNICAL", parameter_name="Delivery Time", submitted_value="25", unit="Days", source_document="Swasthika_Technical_Bid.pdf", source_page=3),
    ])

    # Documents for Bid 1
    t1_docs = [
        ("Technical_Bid", "Swasthika_Technical_Bid.pdf", "Technical Proposal & Specification Sheet", {
            "Tender Reference": "TDR-01-NET-2026",
            "Bidder": "Swasthika industry Private Limited",
            "Product": "Swasthika NetSwitch 24G",
            "Ports": "24 Gigabit Ports",
            "VLAN": "802.1Q Supported",
            "QoS": "Supported (8 hardware queues)",
            "Mounting": "19-inch Rackmount Kit",
            "Warranty": "3 Years Comprehensive On-site",
            "Delivery Schedule": "25 Calendar Days",
        }, [
            ("Technical Specifications", [
                ["Parameter", "Required Threshold", "Offered Specification", "Compliance Status"],
                ["Network Ports", "24 Gigabit Ethernet", "24 x 10/100/1000 Mbps RJ45", "Fully Compliant"],
                ["VLAN Segmentation", "802.1Q VLAN", "IEEE 802.1Q VLAN Supported", "Fully Compliant"],
                ["QoS Prioritization", "Supported", "Hardware QoS Prioritization", "Fully Compliant"],
                ["Chassis Mounting", "Rack Mounting", "Standard 19-inch 1U Rackmount", "Fully Compliant"],
                ["Warranty Period", ">= 3 Years", "3 Years Comprehensive Onsite", "Fully Compliant"],
                ["Delivery Schedule", "<= 30 Calendar Days", "25 Calendar Days", "Fully Compliant"],
            ])
        ]),
        ("GST Certificate", "Swasthika_GST_Certificate.pdf", "Goods and Services Tax Registration Certificate", {
            "Registration Legal Name": "Swasthika industry Private Limited",
            "GSTIN": "29AAGCS1234F1Z8",
            "Taxpayer Type": "Regular",
            "State Jurisdiction": "Karnataka",
            "Status": "ACTIVE",
            "Filing Status": "GSTR-1 & GSTR-3B Filed (Up to Date)",
        }, [
            ("Statutory GST Details", "This document certifies that Swasthika industry Private Limited is registered under the Central Goods and Services Tax Act with active status and up-to-date monthly return filings.")
        ]),
        ("PAN", "Swasthika_PAN_Card.pdf", "Income Tax Department Permanent Account Number", {
            "Name": "Swasthika industry Private Limited",
            "PAN": "AAGCS1234F",
            "Category": "Company",
            "Status": "ACTIVE & OPERATIONAL",
        }, [
            ("PAN Verification", "Verified against NSDL / Income Tax Department database. Entity name and legal status are consistent.")
        ]),
        ("Udyam/MSME Certificate", "Swasthika_Udyam_Certificate.pdf", "Ministry of Micro, Small and Medium Enterprises Registration", {
            "Enterprise Name": "Swasthika industry Private Limited",
            "Udyam Registration": "UDYAM-KR-03-0045678",
            "Enterprise Type": "Medium Enterprise",
            "Major Activity": "Manufacturing & Networking Hardware",
        }, [
            ("Udyam Statutory Verification", "Verified against MSME Udyam portal database. Enterprise categorization and status active.")
        ]),
        ("OEM Authorization", "Swasthika_OEM_Authorization.pdf", "Tender-Specific Manufacturer Authorization Form (MAF)", {
            "OEM Manufacturer": "NetSwitch Systems Corporation Ltd.",
            "Authorized Partner": "Swasthika industry Private Limited",
            "Tender Reference": "TDR-01-NET-2026",
            "Product Covered": "24-Port Managed Network Switch Model SNS-24G-MGD",
            "Validity": "Valid through November 2029",
            "Signatory": "Authorized OEM Director (Signed & Stamped)",
        }, [
            ("Authorization Commitment", "We hereby confirm that Swasthika industry Private Limited is authorized to bid and supply our genuine 24-Port Managed Network Switch for GeM Tender TDR-01-NET-2026 with full factory warranty backing.")
        ]),
    ]

    for doc_type, fname, title, meta, secs in t1_docs:
        fpath, fsize, fpages = generate_pdf_doc(fname, title, f"Tender Reference: {t1.tender_code}", meta, secs)
        d = Document(
            bid_id=bid1.id,
            tender_id=t1.id,
            original_filename=fname,
            safe_filename=fname,
            file_type="pdf",
            file_size_bytes=fsize,
            file_path=fpath,
            declared_doc_type=doc_type,
            detected_doc_type=doc_type,
            classification_confidence=0.98,
            processing_status="PROCESSED",
            ocr_engine_used="Document Intelligence Engine",
            ocr_confidence=0.96,
            page_count=fpages,
        )
        db.session.add(d)
        db.session.flush()
        db.session.add(DocumentExtraction(
            document_id=d.id,
            raw_text=json.dumps(meta),
            structured_data_json=json.dumps(meta),
            entities_json=json.dumps([{"entity": k, "value": v} for k, v in meta.items()]),
            extraction_confidence=0.96,
        ))

    # Compliance Results for Bid 1 (100% Compliant)
    checks_bid1 = [
        ("DOC_REQ_1", "Mandatory Document: Technical Bid", "DOCUMENT", "Technical Bid must be uploaded", "Swasthika_Technical_Bid.pdf (Classified: Technical Bid)", "COMPLIANT", "Required document 'Technical Bid' was uploaded, validated, and classified with 98% confidence.", "Document Intelligence Engine"),
        ("DOC_REQ_2", "Mandatory Document: GST Certificate", "DOCUMENT", "GST Certificate must be uploaded", "Swasthika_GST_Certificate.pdf (Classified: GST Certificate)", "COMPLIANT", "Required document 'GST Certificate' was uploaded, validated, and classified with 98% confidence.", "Document Intelligence Engine"),
        ("DOC_REQ_3", "Mandatory Document: PAN", "DOCUMENT", "PAN must be uploaded", "Swasthika_PAN_Card.pdf (Classified: PAN)", "COMPLIANT", "Required document 'PAN' was uploaded, validated, and classified with 98% confidence.", "Document Intelligence Engine"),
        ("DOC_REQ_4", "Mandatory Document: Udyam/MSME Certificate", "DOCUMENT", "Udyam/MSME Certificate must be uploaded", "Swasthika_Udyam_Certificate.pdf (Classified: Udyam/MSME Certificate)", "COMPLIANT", "Required document 'Udyam/MSME Certificate' was uploaded, validated, and classified with 98% confidence.", "Document Intelligence Engine"),
        ("DOC_REQ_5", "Mandatory Document: OEM Authorization", "DOCUMENT", "OEM Authorization must be uploaded", "Swasthika_OEM_Authorization.pdf (Classified: OEM Authorization)", "COMPLIANT", "Required document 'OEM Authorization' was uploaded, validated, and classified with 98% confidence.", "Document Intelligence Engine"),
        ("STAT_GST_VERIFY", "GST Registration & Filing Compliance", "STATUTORY", "Active 15-digit GSTIN with regular GSTR filing", "29AAGCS1234F1Z8 (ACTIVE, Regular)", "COMPLIANT", "GSTIN 29AAGCS1234F1Z8 is ACTIVE with regular monthly GSTR-1 & GSTR-3B filings verified against GSTN statutory adapter.", "GSTN Statutory Integration"),
        ("STAT_PAN_MCA", "PAN & Corporate Identity Compliance", "STATUTORY", "Valid PAN matching corporate entity", "AAGCS1234F (Swasthika industry Private Limited)", "COMPLIANT", "PAN AAGCS1234F matches legal entity name and is active in Income Tax / MCA databases.", "CBDT & MCA Integration"),
        ("STAT_UDYAM_MSME", "Udyam / MSME Statutory Verification", "STATUTORY", "Valid Udyam registration", "UDYAM-KR-03-0045678 (Medium Enterprise)", "COMPLIANT", "Udyam Registration validated against MSME registry with active status.", "Ministry of MSME Integration"),
        ("STAT_EPFO_ESIC", "EPFO & ESIC Labour Compliance", "STATUTORY", "Statutory employee contribution compliance", "Compliant (ECR & Contribution Verified)", "COMPLIANT", "No statutory dues or labour compliance defaults found.", "EPFO / ESIC Labour Integration"),
        ("STAT_DEBARMENT", "Public Watchlist & Debarment Check", "STATUTORY", "Zero debarment on GeM / DoE watchlist", "Clear (No Watchlist Incidents)", "COMPLIANT", "Zero debarment or incident records found on public procurement registers.", "Public Watchlist Adapter"),
        ("TENDER_MII_LOCAL_CONTENT", "Make in India (PPP-MII) Local Content", "TENDER", "Minimum 50.0% Local Content", "65.0% Local Content Declared", "COMPLIANT", "Declared 65.0% local content meets Class-I local supplier threshold (>= 50%).", "PPP-MII Rule Engine"),
        ("TENDER_OEM_AUTH", "OEM Authorization (MAF) Verification", "TENDER", "Tender-specific MAF matching bidder, product, and tender", "Valid MAF from NetSwitch Systems Corporation Ltd.", "COMPLIANT", "OEM authorization matches the bidder, product, and tender reference TDR-01-NET-2026 with full factory warranty backing.", "OEM Verification Adapter"),
        ("TECH_REQ_1", "Technical Spec: Gigabit Ports", "TECHNICAL", "Gigabit Ports >= 24 Ports", "24 Ports", "COMPLIANT", "Submitted Gigabit Ports (24 Ports) satisfies requirement (Gigabit Ports >= 24 Ports).", "Technical Specification Comparator"),
        ("TECH_REQ_2", "Technical Spec: VLAN Support", "TECHNICAL", "VLAN Support == Supported", "Supported (802.1Q)", "COMPLIANT", "Submitted VLAN Support (Supported) satisfies requirement.", "Technical Specification Comparator"),
        ("TECH_REQ_3", "Technical Spec: Quality of Service (QoS)", "TECHNICAL", "Quality of Service (QoS) == Supported", "Supported (Advanced QoS)", "COMPLIANT", "Submitted Quality of Service (QoS) satisfies requirement.", "Technical Specification Comparator"),
        ("TECH_REQ_4", "Technical Spec: Mounting", "TECHNICAL", "Mounting == Rack Mounting", "Rack Mounting (19-inch 1U)", "COMPLIANT", "Submitted standard 19-inch rack mounting kit satisfies requirement.", "Technical Specification Comparator"),
        ("TECH_REQ_5", "Technical Spec: Warranty", "TECHNICAL", "Warranty >= 3 Years", "3 Years", "COMPLIANT", "Submitted Warranty (3 Years Comprehensive On-site) satisfies requirement (Warranty >= 3 Years).", "Technical Specification Comparator"),
        ("TECH_REQ_6", "Technical Spec: Delivery Time", "TECHNICAL", "Delivery Time <= 30 Days", "25 Days", "COMPLIANT", "Submitted Delivery Time (25 Calendar Days) satisfies requirement (Delivery Time <= 30 Days).", "Technical Specification Comparator"),
    ]

    for code, name, cat, req_t, sub_t, stat, reason, src in checks_bid1:
        cr = ComplianceResult(
            bid_id=bid1.id,
            check_code=code,
            check_name=name,
            category=cat,
            requirement_text=req_t,
            submitted_text=sub_t,
            status=stat,
            reason=reason,
            integration_source=src,
            is_reviewed=True,
            officer_comment="Verified and confirmed compliant.",
        )
        db.session.add(cr)
        db.session.flush()
        db.session.add(Evidence(
            compliance_result_id=cr.id,
            bid_id=bid1.id,
            document_name="Swasthika_Technical_Bid.pdf" if cat == "TECHNICAL" else "Swasthika_GST_Certificate.pdf",
            page_number=2 if cat == "TECHNICAL" else 1,
            extracted_snippet=f"{name}: {sub_t}",
            field_name=name,
            expected_value=req_t,
            actual_value=sub_t,
            explanation=reason,
        ))

    # Risk result for Bid 1
    db.session.add(RiskResult(
        bid_id=bid1.id,
        risk_level="LOW",
        risk_score=8.5,
        anomaly_score=5.2,
        is_anomaly_flagged=False,
        risk_factors_json=json.dumps([{
            "severity": "LOW",
            "category": "OVERALL",
            "factor": "All mandatory documents, technical specifications, and statutory checks passed without anomalies. Evidence is complete and internally consistent.",
        }]),
        ml_explanation="Scikit-learn Isolation Forest evaluated all parameters within normal procurement bounds. Bid quote ratio, delivery schedule, warranty, and statutory credentials exhibit zero anomalies. Final verification confirmed by Procurement Officer.",
        requires_human_review=False,
    ))

    # -------------------------------------------------------------
    # TENDER 2 BID: Mokshi Laboratory -> HIGH RISK (Critical Exceptions)
    # -------------------------------------------------------------
    t2 = tenders_dict["t2"]
    comp2 = bidder_companies["mokshi"]
    bid2 = Bid.query.filter_by(tender_id=t2.id, company_id=comp2.id).first()
    if not bid2:
        bid2 = Bid(
            bid_number="GEM-BID-2026-LAB02",
            tender_id=t2.id,
            company_id=comp2.id,
            quoted_amount=2350000.0,
            warranty_years=1.0,  # CRITICAL EXCEPTION: 1 year instead of 2 years
            delivery_days=75,    # CRITICAL EXCEPTION: 75 days instead of 45 days
            local_content_declared=50.0,
            oem_status="Reseller Partner",
            product_name="Mokshi LabScale Precision Balance",
            product_model="MLB-200X",
            technical_summary="Digital precision balance with tare function, internal calibration, and overload protection. Readability specs contain internal contradictions (0.1g vs 0.05g).",
            declarations_accepted=True,
            submission_status="SUBMITTED",
            verification_status="NEEDS_REVIEW",
            officer_review_status="PENDING_REVIEW",
            officer_review_comments="Flagged with multiple critical exceptions: Readability contradiction (0.1g vs 0.05g), warranty 1 yr < 2 yrs, delivery 75 days > 45 days, and statutory GST/PAN/Udyam/MAF mismatches.",
            overall_compliance_score=53.3,
            document_compliance_score=100.0,
            statutory_compliance_score=33.3,
            technical_compliance_score=50.0,
            tender_compliance_score=50.0,
            risk_level="HIGH",
        )
        db.session.add(bid2)
        db.session.flush()
    else:
        bid2.quoted_amount = 2350000.0
        bid2.warranty_years = 1.0
        bid2.delivery_days = 75
        bid2.overall_compliance_score = 53.3
        bid2.document_compliance_score = 100.0
        bid2.statutory_compliance_score = 33.3
        bid2.technical_compliance_score = 50.0
        bid2.tender_compliance_score = 50.0
        bid2.risk_level = "HIGH"
        bid2.verification_status = "NEEDS_REVIEW"
        bid2.officer_review_status = "PENDING_REVIEW"
        db.session.flush()

    Evidence.query.filter_by(bid_id=bid2.id).delete()
    ComplianceResult.query.filter_by(bid_id=bid2.id).delete()
    RiskResult.query.filter_by(bid_id=bid2.id).delete()
    Document.query.filter_by(bid_id=bid2.id).delete()
    BidItem.query.filter_by(bid_id=bid2.id).delete()
    db.session.flush()

    # BidItems for Bid 2
    db.session.add_all([
        BidItem(bid_id=bid2.id, item_category="TECHNICAL", parameter_name="Readability", submitted_value="0.1", unit="g", source_document="Mokshi_Technical_Bid.pdf", source_page=2),
        BidItem(bid_id=bid2.id, item_category="TECHNICAL", parameter_name="Tare Function", submitted_value="Supported", unit="", source_document="Mokshi_Technical_Bid.pdf", source_page=2),
        BidItem(bid_id=bid2.id, item_category="TECHNICAL", parameter_name="Calibration Capability", submitted_value="Supported", unit="", source_document="Mokshi_Technical_Bid.pdf", source_page=2),
        BidItem(bid_id=bid2.id, item_category="TECHNICAL", parameter_name="Overload Protection", submitted_value="Supported", unit="", source_document="Mokshi_Technical_Bid.pdf", source_page=2),
        BidItem(bid_id=bid2.id, item_category="TECHNICAL", parameter_name="Warranty", submitted_value="1", unit="Years", source_document="Mokshi_Technical_Bid.pdf", source_page=3),
        BidItem(bid_id=bid2.id, item_category="TECHNICAL", parameter_name="Delivery Time", submitted_value="75", unit="Days", source_document="Mokshi_Technical_Bid.pdf", source_page=3),
    ])

    # Documents for Bid 2
    t2_docs = [
        ("Technical Bid", "Mokshi_Technical_Bid.pdf", "Technical Proposal - Precision Digital Balance", {
            "Tender Reference": "OCT-02-LAB-2026",
            "Bidder": "Mokshi Laboratory",
            "Product": "Mokshi LabScale MLB-200X",
            "Readability (Page 2)": "0.1 g",
            "Readability (Page 4 Summary)": "0.05 g",
            "Tare Function": "Supported (Single-touch)",
            "Calibration": "Internal Automatic Calibration",
            "Overload Protection": "Mechanical stops up to 150% capacity",
            "Warranty": "1 Year Standard Manufacturer Warranty",
            "Delivery Commitment": "75 Calendar Days from PO",
        }, [
            ("Technical Specifications & Discrepancies", [
                ["Parameter", "Required Threshold", "Offered Specification", "Audit Note"],
                ["Readability", "<= 0.01 g", "0.1 g (Page 2) / 0.05 g (Page 4)", "Contradictory values; fails 0.01g threshold"],
                ["Tare Function", "Supported", "Single-touch Tare Supported", "Meets requirement"],
                ["Calibration", "Supported", "Internal Motorized Calibration", "Meets requirement"],
                ["Overload Protection", "Supported", "150% Overload Buffer Supported", "Meets requirement"],
                ["Warranty", ">= 2 Years", "1 Year Standard", "Fails requirement (1 yr vs 2 yrs)"],
                ["Delivery Schedule", "<= 45 Days", "75 Calendar Days", "Fails requirement (75 vs 45 days)"],
            ])
        ]),
        ("GST Certificate", "Mokshi_GST_Certificate.pdf", "Goods and Services Tax Certificate", {
            "Certificate Legal Name": "Prism Analytical Instruments Pvt Ltd",
            "GSTIN on Document": "06AAAPM9999K1Z4",
            "Bidder Profile GSTIN": "27AABCM5678D1Z2",
            "State": "Haryana (Mismatches Maharashtra profile)",
            "Status": "ACTIVE",
        }, [
            ("Identity Verification Finding", "Document contains GSTIN 06AAAPM9999K1Z4 registered under 'Prism Analytical Instruments Pvt Ltd', mismatching bidder entity 'Mokshi Laboratory' (GSTIN 27AABCM5678D1Z2).")
        ]),
        ("PAN", "Mokshi_PAN_Card.pdf", "Income Tax Permanent Account Number Card", {
            "Name on Document": "Prism Analytical Instruments Pvt Ltd",
            "PAN on Document": "AAAPM9999K",
            "Bidder Profile PAN": "AABCM5678D",
            "Category": "Company",
        }, [
            ("PAN Verification Finding", "Permanent Account Number AAAPM9999K does not match registered bidder profile PAN AABCM5678D.")
        ]),
        ("Udyam/MSME Certificate", "Mokshi_Udyam_Certificate.pdf", "MSME Registration Certificate", {
            "Enterprise Name": "Apex Precision Instruments LLP",
            "Udyam Registration": "UDYAM-HR-02-0099999",
            "Bidder Profile Udyam": "UDYAM-MH-01-0056789",
            "Enterprise Type": "Micro",
        }, [
            ("Udyam Verification Finding", "Udyam registration UDYAM-HR-02-0099999 reflects an unrelated enterprise in Haryana, mismatching bidder profile.")
        ]),
        ("OEM Authorization", "Mokshi_OEM_Authorization.pdf", "Manufacturer Authorization Form (MAF)", {
            "OEM Manufacturer": "Global BioLab Equipment Ltd.",
            "Authorized Vendor": "Allied Scientific Resellers Pvt. Ltd.",
            "Tender Reference on Document": "REF-OLD-2023 (Mismatches OCT-02-LAB-2026)",
            "Equipment Specified": "UV-Vis Spectrophotometers (Mismatches Digital Balances)",
        }, [
            ("MAF Verification Finding", "OEM authorization has bidder/product/tender-reference inconsistencies: references obsolete tender REF-OLD-2023, specifies spectrophotometers instead of balances, and authorizes an unrelated third-party.")
        ]),
    ]

    for doc_type, fname, title, meta, secs in t2_docs:
        fpath, fsize, fpages = generate_pdf_doc(fname, title, f"Tender Reference: {t2.tender_code}", meta, secs)
        d = Document(
            bid_id=bid2.id,
            tender_id=t2.id,
            original_filename=fname,
            safe_filename=fname,
            file_type="pdf",
            file_size_bytes=fsize,
            file_path=fpath,
            declared_doc_type=doc_type,
            detected_doc_type=doc_type,
            classification_confidence=0.95,
            processing_status="PROCESSED",
            ocr_engine_used="Document Intelligence Engine",
            ocr_confidence=0.92,
            page_count=fpages,
        )
        db.session.add(d)
        db.session.flush()
        db.session.add(DocumentExtraction(
            document_id=d.id,
            raw_text=json.dumps(meta),
            structured_data_json=json.dumps(meta),
            entities_json=json.dumps([{"entity": k, "value": v} for k, v in meta.items()]),
            extraction_confidence=0.92,
        ))

    # Compliance Results for Bid 2 (Multiple Critical Exceptions -> High Risk)
    checks_bid2 = [
        ("DOC_REQ_1", "Mandatory Document: Technical Bid", "DOCUMENT", "Technical Bid must be uploaded", "Mokshi_Technical_Bid.pdf", "COMPLIANT", "Document uploaded and readable.", "Document Intelligence Engine"),
        ("DOC_REQ_2", "Mandatory Document: GST Certificate", "DOCUMENT", "GST Certificate must be uploaded", "Mokshi_GST_Certificate.pdf", "COMPLIANT", "Document uploaded and readable.", "Document Intelligence Engine"),
        ("DOC_REQ_3", "Mandatory Document: PAN", "DOCUMENT", "PAN must be uploaded", "Mokshi_PAN_Card.pdf", "COMPLIANT", "Document uploaded and readable.", "Document Intelligence Engine"),
        ("DOC_REQ_4", "Mandatory Document: Udyam/MSME Certificate", "DOCUMENT", "Udyam/MSME Certificate must be uploaded", "Mokshi_Udyam_Certificate.pdf", "COMPLIANT", "Document uploaded and readable.", "Document Intelligence Engine"),
        ("DOC_REQ_5", "Mandatory Document: OEM Authorization", "DOCUMENT", "OEM Authorization must be uploaded", "Mokshi_OEM_Authorization.pdf", "COMPLIANT", "Document uploaded and readable.", "Document Intelligence Engine"),
        ("STAT_GST_VERIFY", "GST Registration & Identity Verification", "STATUTORY", "Active GSTIN matching registered bidder profile", "06AAAPM9999K1Z4 (Mismatch)", "NON_COMPLIANT", "GST identity verification has a mismatch: Uploaded GST Certificate contains GSTIN '06AAAPM9999K1Z4' registered to 'Prism Analytical Instruments', which does not match bidder profile GSTIN '27AABCM5678D1Z2' (Mokshi Laboratory).", "GSTN Statutory Integration"),
        ("STAT_PAN_MCA", "Corporate PAN Identity Verification", "STATUTORY", "Corporate PAN matching bidder profile", "AAAPM9999K (Mismatch)", "NON_COMPLIANT", "PAN does not match the bidder profile: Uploaded PAN card reflects 'AAAPM9999K' differing from bidder profile PAN 'AABCM5678D'.", "Income Tax CBDT Integration"),
        ("STAT_UDYAM_MSME", "Udyam / MSME Registration Verification", "STATUTORY", "Valid Udyam certificate matching bidder entity", "UDYAM-HR-02-0099999 (Mismatch)", "NON_COMPLIANT", "Udyam/MSME information has a mismatch: Uploaded Udyam certificate reflects registration 'UDYAM-HR-02-0099999' which belongs to an unrelated third-party entity.", "Ministry of MSME Integration"),
        ("STAT_EPFO_ESIC", "EPFO & ESIC Labour Statutory Compliance", "STATUTORY", "EPFO & ESIC statutory compliance", "ECR verified", "COMPLIANT", "No statutory labour defaults flagged.", "Labour Statutory Integration"),
        ("STAT_DEBARMENT", "Debarment & Watchlist Screening", "STATUTORY", "Zero debarment on GeM / DoE watchlist", "Clear", "COMPLIANT", "No public debarment incidents found.", "Public Watchlist Adapter"),
        ("TENDER_MII_LOCAL_CONTENT", "Make in India Local Content Compliance", "TENDER", "Minimum 50.0% Local Content", "50.0% Declared", "COMPLIANT", "Declared 50.0% local content meets tender threshold.", "PPP-MII Rule Engine"),
        ("TENDER_OEM_AUTH", "OEM Authorization (MAF) Consistency", "TENDER", "Tender-specific MAF matching bidder, product, and tender", "Inconsistent MAF (REF-OLD-2023 / Spectrophotometer)", "NON_COMPLIANT", "OEM authorization has bidder/product/tender-reference inconsistencies: MAF references unrelated tender 'REF-OLD-2023', specifies spectrophotometers instead of weighing balances, and names an unverified third party.", "OEM Verification Engine"),
        ("TECH_REQ_1", "Technical Spec: Readability", "TECHNICAL", "Readability <= 0.01 g", "0.1 g / 0.05 g (Contradictory)", "NON_COMPLIANT", "Technical specification contains contradictory readability values: Technical Bid Page 2 specifies 0.1 g readability, whereas Page 4 summary specifies 0.05 g. Both values fail the required 0.01 g precision threshold.", "Technical Specification Comparator"),
        ("TECH_REQ_2", "Technical Spec: Tare Function", "TECHNICAL", "Tare Function == Supported", "Supported", "COMPLIANT", "Single-touch Tare function meets specification.", "Technical Specification Comparator"),
        ("TECH_REQ_3", "Technical Spec: Calibration Capability", "TECHNICAL", "Calibration Capability == Supported", "Supported", "COMPLIANT", "Internal calibration mechanism meets specification.", "Technical Specification Comparator"),
        ("TECH_REQ_4", "Technical Spec: Overload Protection", "TECHNICAL", "Overload Protection == Supported", "Supported", "COMPLIANT", "Overload protection mechanism meets specification.", "Technical Specification Comparator"),
        ("TECH_REQ_5", "Technical Spec: Warranty", "TECHNICAL", "Warranty >= 2 Years", "1.0 Year", "NON_COMPLIANT", "Warranty is one year instead of the required two years: Proposal commits to only 1-year warranty, failing the mandatory 2-year requirement.", "Technical Specification Comparator"),
        ("TECH_REQ_6", "Technical Spec: Delivery Time", "TECHNICAL", "Delivery Time <= 45 Days", "75 Days", "NON_COMPLIANT", "Delivery is 75 days instead of the required 45 days: Proposal commits to 75 calendar days, exceeding the 45-day tender limit.", "Technical Specification Comparator"),
    ]

    for code, name, cat, req_t, sub_t, stat, reason, src in checks_bid2:
        cr = ComplianceResult(
            bid_id=bid2.id,
            check_code=code,
            check_name=name,
            category=cat,
            requirement_text=req_t,
            submitted_text=sub_t,
            status=stat,
            reason=reason,
            integration_source=src,
            is_reviewed=False,
        )
        db.session.add(cr)
        db.session.flush()
        db.session.add(Evidence(
            compliance_result_id=cr.id,
            bid_id=bid2.id,
            document_name="Mokshi_Technical_Bid.pdf" if cat == "TECHNICAL" else "Mokshi_GST_Certificate.pdf",
            page_number=2 if cat == "TECHNICAL" else 1,
            extracted_snippet=f"{name}: {sub_t} -> {reason}",
            field_name=name,
            expected_value=req_t,
            actual_value=sub_t,
            explanation=reason,
        ))

    # Risk result for Bid 2 (HIGH RISK)
    db.session.add(RiskResult(
        bid_id=bid2.id,
        risk_level="HIGH",
        risk_score=92.0,
        anomaly_score=76.5,
        is_anomaly_flagged=True,
        risk_factors_json=json.dumps([
            {"severity": "HIGH", "category": "TECHNICAL", "factor": "Technical specification contains contradictory readability values (0.1g vs 0.05g, failing 0.01g requirement)."},
            {"severity": "HIGH", "category": "TECHNICAL", "factor": "Warranty is one year instead of the required two years."},
            {"severity": "HIGH", "category": "TECHNICAL", "factor": "Delivery is 75 days instead of the required 45 days."},
            {"severity": "HIGH", "category": "STATUTORY", "factor": "GST identity verification has a mismatch (06AAAPM9999K1Z4 vs 27AABCM5678D1Z2)."},
            {"severity": "HIGH", "category": "STATUTORY", "factor": "PAN does not match the bidder profile (AAAPM9999K vs AABCM5678D)."},
            {"severity": "HIGH", "category": "STATUTORY", "factor": "Udyam/MSME information has a mismatch (UDYAM-HR-02-0099999 vs UDYAM-MH-01-0056789)."},
            {"severity": "HIGH", "category": "TENDER", "factor": "OEM authorization has bidder/product/tender-reference inconsistencies (REF-OLD-2023 / Spectrophotometer)."},
        ]),
        ml_explanation="Scikit-learn Isolation Forest detected high anomaly score (76.5). Critical non-compliant exceptions in delivery schedule (75 days vs 45 days limit), warranty period (1 yr vs 2 yrs), statutory identity mismatches, and contradictory technical readability specifications. Immediate officer review required.",
        requires_human_review=True,
    ))

    # -------------------------------------------------------------
    # TENDER 3 BID: Sam Tech -> MEDIUM RISK (Manual Review Required)
    # -------------------------------------------------------------
    t3 = tenders_dict["t3"]
    comp3 = bidder_companies["samtech"]
    bid3 = Bid.query.filter_by(tender_id=t3.id, company_id=comp3.id).first()
    if not bid3:
        bid3 = Bid(
            bid_number="GEM-BID-2026-SOL03",
            tender_id=t3.id,
            company_id=comp3.id,
            quoted_amount=5400000.0,
            warranty_years=3.0,
            delivery_days=60,
            local_content_declared=60.0,
            oem_status="Authorized OEM Partner with MAF",
            product_name="SamTech SolarLum 60W Street System",
            product_model="STS-60W-SL",
            technical_summary="Standalone integrated solar LED street light with 60W LED luminaire, LiFePO4 battery, dusk-to-dawn intelligent controller, and IP65 enclosure.",
            declarations_accepted=True,
            submission_status="SUBMITTED",
            verification_status="NEEDS_REVIEW",
            officer_review_status="PENDING_REVIEW",
            officer_review_comments="Flagged for manual review: Core technical specifications and statutory identity match, but delivery schedule commitment (60-90 days), warranty term ambiguity (2 vs 3 years), and missing OEM authorization validity date/signature require officer clarification.",
            overall_compliance_score=94.0,
            document_compliance_score=100.0,
            statutory_compliance_score=100.0,
            technical_compliance_score=86.7,
            tender_compliance_score=90.0,
            risk_level="MEDIUM",
        )
        db.session.add(bid3)
        db.session.flush()
    else:
        bid3.quoted_amount = 5400000.0
        bid3.warranty_years = 3.0
        bid3.delivery_days = 60
        bid3.local_content_declared = 60.0
        bid3.overall_compliance_score = 94.0
        bid3.document_compliance_score = 100.0
        bid3.statutory_compliance_score = 100.0
        bid3.technical_compliance_score = 86.7
        bid3.tender_compliance_score = 90.0
        bid3.risk_level = "MEDIUM"
        bid3.verification_status = "NEEDS_REVIEW"
        bid3.officer_review_status = "PENDING_REVIEW"
        db.session.flush()

    Evidence.query.filter_by(bid_id=bid3.id).delete()
    ComplianceResult.query.filter_by(bid_id=bid3.id).delete()
    RiskResult.query.filter_by(bid_id=bid3.id).delete()
    Document.query.filter_by(bid_id=bid3.id).delete()
    BidItem.query.filter_by(bid_id=bid3.id).delete()
    db.session.flush()

    # BidItems for Bid 3
    db.session.add_all([
        BidItem(bid_id=bid3.id, item_category="TECHNICAL", parameter_name="LED Luminaire", submitted_value="60", unit="W", source_document="SamTech_Technical_Bid.pdf", source_page=2),
        BidItem(bid_id=bid3.id, item_category="TECHNICAL", parameter_name="Battery Type", submitted_value="Lithium Battery", unit="", source_document="SamTech_Technical_Bid.pdf", source_page=2),
        BidItem(bid_id=bid3.id, item_category="TECHNICAL", parameter_name="Dusk-to-Dawn Control", submitted_value="Supported", unit="", source_document="SamTech_Technical_Bid.pdf", source_page=2),
        BidItem(bid_id=bid3.id, item_category="TECHNICAL", parameter_name="Enclosure Rating", submitted_value="IP65 Enclosure", unit="", source_document="SamTech_Technical_Bid.pdf", source_page=2),
        BidItem(bid_id=bid3.id, item_category="TECHNICAL", parameter_name="Warranty", submitted_value="3", unit="Years", source_document="SamTech_Technical_Bid.pdf", source_page=3),
        BidItem(bid_id=bid3.id, item_category="TECHNICAL", parameter_name="Delivery Time", submitted_value="60", unit="Days", source_document="SamTech_Technical_Bid.pdf", source_page=3),
    ])

    # Documents for Bid 3
    t3_docs = [
        ("Technical Bid", "SamTech_Technical_Bid.pdf", "Technical Proposal - Standalone Solar LED Street Light", {
            "Tender Reference": "TDR-03-SOLAR-2026",
            "Bidder": "Sam Tech",
            "Product": "SamTech SolarLum 60W Street System",
            "LED Luminaire": "60 W High-efficiency Bridgelux LED",
            "Battery": "Lithium Iron Phosphate (LiFePO4) 12.8V 36Ah",
            "Lighting Controller": "Intelligent Dusk-to-Dawn MPPT Controller",
            "Enclosure": "Die-cast Aluminum IP65 Ingress Protection",
            "Warranty Clause": "Standard manufacturer warranty 2 years with optional 3rd year extension subject to AMC terms",
            "Delivery Commitment": "Estimated dispatch 60 to 90 calendar days depending on batch logistics",
        }, [
            ("Technical Specifications & Clarification Items", [
                ["Parameter", "Required Threshold", "Offered Specification", "Verification Status"],
                ["LED Luminaire", ">= 60 W", "60 W LED Luminaire", "Compliant"],
                ["Battery Type", "Lithium Battery", "Lithium LiFePO4 Battery", "Compliant"],
                ["Dusk-to-Dawn Sensor", "Supported", "Automatic MPPT Dusk-to-Dawn Sensor", "Compliant"],
                ["Weatherproof Enclosure", "IP65 Enclosure", "IP65 Weatherproof Aluminum Enclosure", "Compliant"],
                ["Warranty Period", ">= 3 Years", "2-3 Years (Conditional on AMC)", "Requires Clarification (Ambiguous)"],
                ["Delivery Schedule", "<= 60 Calendar Days", "60 to 90 Calendar Days", "Requires Clarification (Ambiguous)"],
            ])
        ]),
        ("GST Certificate", "SamTech_GST_Certificate.pdf", "Goods and Services Tax Registration Certificate", {
            "Legal Name": "Sam Tech",
            "GSTIN": "36AAECS4321B1Z3",
            "Registration Status": "ACTIVE",
            "State": "Telangana",
            "Filing Status": "Regular Monthly Filings Verified",
        }, [
            ("Statutory GST Record", "Active 15-digit GSTIN 36AAECS4321B1Z3 matches bidder profile Sam Tech. Returns filed up to date.")
        ]),
        ("PAN", "SamTech_PAN_Card.pdf", "Income Tax Permanent Account Number Card", {
            "Name": "Sam Tech",
            "PAN": "AAECS4321B",
            "Category": "Firm / Enterprise",
            "Status": "ACTIVE",
        }, [
            ("PAN Record", "Permanent Account Number AAECS4321B verified matching bidder identity.")
        ]),
        ("Udyam/MSME Certificate", "SamTech_Udyam_Certificate.pdf", "Udyam Registration Certificate", {
            "Enterprise Name": "Sam Tech",
            "Udyam Number": "UDYAM-TS-09-0014321",
            "Enterprise Type": "Small Enterprise",
            "Activity": "Solar Power & Clean Energy Systems",
        }, [
            ("MSME Verification", "Udyam Registration UDYAM-TS-09-0014321 active and verified.")
        ]),
        ("OEM Authorization", "SamTech_OEM_Authorization.pdf", "Manufacturer Authorization Form (MAF)", {
            "OEM Manufacturer": "SolarLum Electronics Global Pvt Ltd",
            "Authorized Partner": "Sam Tech",
            "Product Covered": "60W Solar LED Street System Model STS-60W-SL",
            "Tender Reference": "TDR-03-SOLAR-2026",
            "Validity Date": "[Not Specified / Missing]",
            "Signature & Endorsement": "[Partially Obscured / Needs Visual Inspection]",
        }, [
            ("Authorization Finding", "OEM authorization matches the bidder and product; however, authorization validity expiration date is missing and authorized signature is unclear. Manual officer inspection recommended.")
        ]),
    ]

    for doc_type, fname, title, meta, secs in t3_docs:
        fpath, fsize, fpages = generate_pdf_doc(fname, title, f"Tender Reference: {t3.tender_code}", meta, secs)
        d = Document(
            bid_id=bid3.id,
            tender_id=t3.id,
            original_filename=fname,
            safe_filename=fname,
            file_type="pdf",
            file_size_bytes=fsize,
            file_path=fpath,
            declared_doc_type=doc_type,
            detected_doc_type=doc_type,
            classification_confidence=0.96,
            processing_status="PROCESSED",
            ocr_engine_used="Document Intelligence Engine",
            ocr_confidence=0.94,
            page_count=fpages,
        )
        db.session.add(d)
        db.session.flush()
        db.session.add(DocumentExtraction(
            document_id=d.id,
            raw_text=json.dumps(meta),
            structured_data_json=json.dumps(meta),
            entities_json=json.dumps([{"entity": k, "value": v} for k, v in meta.items()]),
            extraction_confidence=0.94,
        ))

    # Compliance Results for Bid 3 (Manual Review Required / Medium Risk)
    checks_bid3 = [
        ("DOC_REQ_1", "Mandatory Document: Technical Bid", "DOCUMENT", "Technical Bid must be uploaded", "SamTech_Technical_Bid.pdf", "COMPLIANT", "Document uploaded and readable.", "Document Intelligence Engine"),
        ("DOC_REQ_2", "Mandatory Document: GST Certificate", "DOCUMENT", "GST Certificate must be uploaded", "SamTech_GST_Certificate.pdf", "COMPLIANT", "Document uploaded and readable.", "Document Intelligence Engine"),
        ("DOC_REQ_3", "Mandatory Document: PAN", "DOCUMENT", "PAN must be uploaded", "SamTech_PAN_Card.pdf", "COMPLIANT", "Document uploaded and readable.", "Document Intelligence Engine"),
        ("DOC_REQ_4", "Mandatory Document: Udyam/MSME Certificate", "DOCUMENT", "Udyam/MSME Certificate must be uploaded", "SamTech_Udyam_Certificate.pdf", "COMPLIANT", "Document uploaded and readable.", "Document Intelligence Engine"),
        ("DOC_REQ_5", "Mandatory Document: OEM Authorization", "DOCUMENT", "OEM Authorization must be uploaded", "SamTech_OEM_Authorization.pdf", "COMPLIANT", "Document uploaded and readable.", "Document Intelligence Engine"),
        ("STAT_GST_VERIFY", "GST Registration & Filing Compliance", "STATUTORY", "Active 15-digit GSTIN with regular GSTR filing", "36AAECS4321B1Z3 (ACTIVE)", "COMPLIANT", "Identity documents match: Active GSTIN 36AAECS4321B1Z3 matches Sam Tech.", "GSTN Statutory Integration"),
        ("STAT_PAN_MCA", "Corporate PAN Identity Compliance", "STATUTORY", "Valid PAN matching bidder profile", "AAECS4321B (Sam Tech)", "COMPLIANT", "Identity documents match: PAN AAECS4321B verified in CBDT / MCA records.", "CBDT Integration"),
        ("STAT_UDYAM_MSME", "Udyam / MSME Registration Compliance", "STATUTORY", "Valid Udyam certificate matching bidder", "UDYAM-TS-09-0014321", "COMPLIANT", "Identity documents match: Udyam MSME certificate verified with active status.", "Ministry of MSME Integration"),
        ("STAT_EPFO_ESIC", "EPFO & ESIC Labour Compliance", "STATUTORY", "EPFO & ESIC statutory compliance", "ECR verified", "COMPLIANT", "Statutory employee contributions verified.", "Labour Statutory Integration"),
        ("STAT_DEBARMENT", "Debarment & Watchlist Screening", "STATUTORY", "Zero debarment on GeM / DoE watchlist", "Clear", "COMPLIANT", "Zero watchlist incidents found.", "Public Watchlist Adapter"),
        ("TENDER_MII_LOCAL_CONTENT", "Make in India Local Content Compliance", "TENDER", "Minimum 50.0% Local Content", "60.0% Declared", "COMPLIANT", "Declared 60.0% local content meets requirement.", "PPP-MII Rule Engine"),
        ("TENDER_OEM_AUTH", "OEM Authorization (MAF) / Validity & Signature", "TENDER", "Tender-specific MAF with clear validity date and signature", "MAF Verified, Validity Date Missing & Unclear Signature", "NEEDS_REVIEW", "OEM authorization matches the bidder and product, but authorization validity date is missing and authorized signature is unclear. Document names Sam Tech and 60W Solar LED model correctly; however, validity expiration date is omitted and signatory endorsement stamp is partially obscured. Manual review required.", "OEM Verification Adapter"),
        ("TECH_REQ_1", "Technical Spec: LED Luminaire", "TECHNICAL", "LED Luminaire >= 60 W", "60 W", "COMPLIANT", "Core technical specifications are satisfied: 60 W high-efficiency LED luminaire satisfies requirement.", "Technical Specification Comparator"),
        ("TECH_REQ_2", "Technical Spec: Battery Type", "TECHNICAL", "Battery Type == Lithium Battery", "Lithium Battery (LiFePO4)", "COMPLIANT", "Core technical specifications are satisfied: Lithium LiFePO4 battery satisfies requirement.", "Technical Specification Comparator"),
        ("TECH_REQ_3", "Technical Spec: Dusk-to-Dawn Control", "TECHNICAL", "Dusk-to-Dawn Control == Supported", "Supported (Automatic Sensor)", "COMPLIANT", "Core technical specifications are satisfied: Dusk-to-dawn automatic control satisfies requirement.", "Technical Specification Comparator"),
        ("TECH_REQ_4", "Technical Spec: Enclosure Rating", "TECHNICAL", "Enclosure Rating == IP65 Enclosure", "IP65 Enclosure", "COMPLIANT", "Core technical specifications are satisfied: IP65 weatherproof enclosure satisfies requirement.", "Technical Specification Comparator"),
        ("TECH_REQ_5", "Technical Spec: Warranty", "TECHNICAL", "Warranty >= 3 Years", "2-3 Years (Ambiguous)", "NEEDS_REVIEW", "Warranty information is ambiguous between two and three years: Bid submission form declares 3 years, but Technical Bid Page 3 states 'Standard manufacturer warranty 2 years with optional 3rd year extension subject to AMC terms'. Requires Procurement Officer clarification.", "Technical Specification Comparator"),
        ("TECH_REQ_6", "Technical Spec: Delivery Time", "TECHNICAL", "Delivery Time <= 60 Days", "60-90 Days (Ambiguous)", "NEEDS_REVIEW", "Delivery commitment says 60–90 days instead of clearly confirming the required 60 days: Form specifies 60 calendar days, while Technical Proposal logistics section states 'Estimated dispatch 60 to 90 calendar days depending on batch logistics'. Requires Procurement Officer confirmation.", "Technical Specification Comparator"),
    ]

    for code, name, cat, req_t, sub_t, stat, reason, src in checks_bid3:
        cr = ComplianceResult(
            bid_id=bid3.id,
            check_code=code,
            check_name=name,
            category=cat,
            requirement_text=req_t,
            submitted_text=sub_t,
            status=stat,
            reason=reason,
            integration_source=src,
            is_reviewed=False,
        )
        db.session.add(cr)
        db.session.flush()
        db.session.add(Evidence(
            compliance_result_id=cr.id,
            bid_id=bid3.id,
            document_name="SamTech_Technical_Bid.pdf" if cat == "TECHNICAL" else ("SamTech_OEM_Authorization.pdf" if code == "TENDER_OEM_AUTH" else "SamTech_GST_Certificate.pdf"),
            page_number=3 if cat == "TECHNICAL" else 1,
            extracted_snippet=f"{name}: {sub_t} -> {reason}",
            field_name=name,
            expected_value=req_t,
            actual_value=sub_t,
            explanation=reason,
        ))

    # Risk result for Bid 3 (MEDIUM RISK)
    db.session.add(RiskResult(
        bid_id=bid3.id,
        risk_level="MEDIUM",
        risk_score=38.0,
        anomaly_score=32.0,
        is_anomaly_flagged=False,
        risk_factors_json=json.dumps([
            {"severity": "MEDIUM", "category": "TECHNICAL", "factor": "Warranty information is ambiguous between two and three years (Form states 3 yrs; doc states 2 yrs + AMC)."},
            {"severity": "MEDIUM", "category": "TECHNICAL", "factor": "Delivery commitment says 60–90 days instead of clearly confirming required 60 days."},
            {"severity": "MEDIUM", "category": "TENDER", "factor": "OEM authorization validity date is missing and authorized signature is unclear."},
        ]),
        ml_explanation="Manual review recommended: Core technical specifications (60W LED, Lithium LiFePO4 battery, dusk-to-dawn, IP65) and statutory identity documents match; however, conditional warranty terms (2 vs 3 yrs), delivery ambiguity (60-90 days), and missing OEM validity date/signature require officer clarification before award.",
        requires_human_review=True,
    ))

    # Record Audit logs
    record_audit_log("Tenders & Accounts Configured", user=officer_user, result_status="SUCCESS", commit=False)
    db.session.commit()
    print("BidVerify production database successfully seeded and configured!")


if __name__ == "__main__":
    from backend.app import create_app
    app = create_app(test_config={"SQLALCHEMY_DATABASE_URI": Config.SQLITE_FALLBACK_URI})
    with app.app_context():
        seed_procurement_data()
