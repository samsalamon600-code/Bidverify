import json
import os
import sys

# Ensure project root is in sys.path when script is executed directly
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

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
    ComplianceCheck,
)
from backend.document_processing.pipeline import process_document_pipeline
from backend.compliance.engine import run_bid_compliance_verification
from backend.services.audit_service import record_audit_log


def _create_sample_document_file(filename: str, content: str) -> tuple[str, int]:
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    path = os.path.join(Config.UPLOAD_FOLDER, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    size = os.path.getsize(path)
    return path, size


def seed_demo_data():
    """
    Populates the database with SIH 26100 demonstration data if not already seeded:
    - 2 Roles (PROCUREMENT_OFFICER, COMPANY)
    - 2 Procurement Officers + 5 Bidder Companies
    - 3 GeM Tenders with structured technical/statutory requirements
    - 10 Submitted Bids with real sample documents, OCR extractions, Compliance Results,
      Scikit-learn Isolation Forest Risk Analysis, Supporting Evidence, and Audit Logs.
    """
    if User.query.first():
        return

    # 1. Roles
    role_officer = Role(name="PROCUREMENT_OFFICER", description="Authorized GeM Procurement Officer")
    role_company = Role(name="COMPANY", description="Offering Company / GeM Registered Bidder")
    db.session.add_all([role_officer, role_company])
    db.session.flush()

    # 2. Standard Compliance Check Catalog
    checks_catalog = [
        ("DOC_REQ", "Mandatory Tender Documents Completeness", "DOCUMENT", "Verifies all mandatory tender documents are uploaded and readable."),
        ("STAT_GST_VERIFY", "GSTIN Registration & Filing Compliance", "STATUTORY", "Validates 15-digit GSTIN and GSTR filing status via GSTN adapter."),
        ("STAT_PAN_MCA", "PAN & MCA21 Corporate Verification", "STATUTORY", "Validates PAN and Corporate Identity Number (CIN)."),
        ("STAT_UDYAM_MSME", "Udyam / MSME Statutory Registration", "STATUTORY", "Verifies Udyam Registration certificate and enterprise category."),
        ("STAT_EPFO_ESIC", "EPFO & ESIC Labour Statutory Compliance", "STATUTORY", "Checks establishment ECR and ESIC employer contribution status."),
        ("STAT_DEBARMENT", "Public Debarment & Watchlist Screening", "STATUTORY", "Checks GeM / DoE public debarment & incident watchlists."),
        ("STAT_DIGILOCKER", "DigiLocker Issuer Metadata Verification", "STATUTORY", "Checks document reference metadata against DigiLocker adapter."),
        ("TENDER_MII_LOCAL_CONTENT", "Make in India (PPP-MII) Local Content", "TENDER", "Verifies Class-I / Class-II Local Content percentage requirement."),
        ("TENDER_OEM_AUTH", "OEM Authorization (MAF) / Startup / NSIC", "TENDER", "Verifies Manufacturer Authorization Form or direct OEM status."),
        ("TECH_SPECS", "Technical Specification Comparison", "TECHNICAL", "Compares extracted technical parameters against tender requirements."),
    ]
    for code, name, cat, desc in checks_catalog:
        db.session.add(ComplianceCheck(check_code=code, check_name=name, category=cat, description=desc))

    # 3. Users: 2 Procurement Officers
    officer_user1 = User(
        email="officer@gem.gov.in",
        password_hash=generate_password_hash("Officer@123"),
        full_name="Rajeshwar Sharma, IAS",
        role_id=role_officer.id,
        role_name="PROCUREMENT_OFFICER",
    )
    officer_user2 = User(
        email="director.proc@meity.gov.in",
        password_hash=generate_password_hash("Officer@123"),
        full_name="Dr. Ananya Deshmukh",
        role_id=role_officer.id,
        role_name="PROCUREMENT_OFFICER",
    )
    db.session.add_all([officer_user1, officer_user2])
    db.session.flush()

    db.session.add_all([
        Officer(
            user_id=officer_user1.id,
            employee_id="GEM-OFF-1001",
            department="Central Digital Infrastructure Procurement Division",
            designation="Joint Secretary & Chief Procurement Officer",
            ministry="Ministry of Commerce & Industry (GeM)",
            phone="+91-11-23062410",
        ),
        Officer(
            user_id=officer_user2.id,
            employee_id="GEM-OFF-1002",
            department="National e-Governance Hardware Cell",
            designation="Director (Procurement Compliance)",
            ministry="Ministry of Electronics & IT (MeitY)",
            phone="+91-11-24301855",
        ),
    ])

    # 4. Users: 5 Offering Companies / Bidders
    companies_spec = [
        {
            "email": "company@apexbharat.in",
            "full_name": "Vikramaditya Nair",
            "company_name": "Apex Bharat Technologies Pvt. Ltd.",
            "reg_no": "U72200DL2018PTC331201",
            "gstin": "07AABCA1234C1Z5",
            "pan": "AABCA1234C",
            "udyam": "UDYAM-DL-01-0012345",
            "etype": "Small Enterprise",
            "year": 2018,
            "lc": 68.0,
            "addr": "Plot 14, Okhla Industrial Estate Phase-III, New Delhi - 110020",
            "phone": "+91-9810112233",
            "msme": True,
            "startup": False,
        },
        {
            "email": "bids@novagrid.co.in",
            "full_name": "Sandeep Kulkarni",
            "company_name": "NovaGrid InfoSystems Ltd.",
            "reg_no": "U72900MH2016PLC284510",
            "gstin": "27AAFCN5678D1Z2",
            "pan": "AAFCN5678D",
            "udyam": "UDYAM-MH-04-0056789",
            "etype": "Medium Enterprise",
            "year": 2016,
            "lc": 54.0,
            "addr": "MIDC SEEPZ, Andheri East, Mumbai, Maharashtra - 400096",
            "phone": "+91-9820445566",
            "msme": True,
            "startup": False,
        },
        {
            "email": "tenders@shaktihardware.in",
            "full_name": "Karthikeya Rao",
            "company_name": "Shakti Sovereign Hardware Solutions Pvt. Ltd.",
            "reg_no": "U30007KA2020PTC139812",
            "gstin": "29AADCS9012E1Z8",
            "pan": "AADCS9012E",
            "udyam": "UDYAM-KA-02-0090123",
            "etype": "Small Enterprise",
            "year": 2020,
            "lc": 74.0,
            "addr": "Electronic City Phase II, Hosur Road, Bengaluru - 560100",
            "phone": "+91-9845098765",
            "msme": True,
            "startup": True,
        },
        {
            "email": "procurement@vanguardinfra.in",
            "full_name": "M. Chidambaram",
            "company_name": "Vanguard Infra & MedTech Corp",
            "reg_no": "U33110TN2015PTC101442",
            "gstin": "33AABCV4321F1Z9",
            "pan": "AABCV4321F",
            "udyam": "UDYAM-TN-08-0043210",
            "etype": "Medium Enterprise",
            "year": 2015,
            "lc": 35.0,
            "addr": "Guindy Industrial Estate, Chennai, Tamil Nadu - 600032",
            "phone": "+91-9444011223",
            "msme": False,
            "startup": False,
        },
        {
            "email": "gem@pragatidigital.in",
            "full_name": "Harshvardhan Patel",
            "company_name": "Pragati Digital Peripherals LLP",
            "reg_no": "AAJ-4590",
            "gstin": "24AAECP7890G1Z1",
            "pan": "AAECP7890G",
            "udyam": "UDYAM-GJ-06-0078901",
            "etype": "Micro Enterprise",
            "year": 2021,
            "lc": 62.0,
            "addr": "GIFT City Road, Gandhinagar, Gujarat - 382355",
            "phone": "+91-9898077665",
            "msme": True,
            "startup": True,
        },
    ]

    companies = []
    for c_spec in companies_spec:
        u = User(
            email=c_spec["email"],
            password_hash=generate_password_hash("Company@123"),
            full_name=c_spec["full_name"],
            role_id=role_company.id,
            role_name="COMPANY",
        )
        db.session.add(u)
        db.session.flush()
        comp = Company(
            user_id=u.id,
            company_name=c_spec["company_name"],
            registration_number=c_spec["reg_no"],
            gstin=c_spec["gstin"],
            pan=c_spec["pan"],
            udyam_number=c_spec["udyam"],
            enterprise_type=c_spec["etype"],
            incorporation_year=c_spec["year"],
            local_content_percent=c_spec["lc"],
            address=c_spec["addr"],
            contact_phone=c_spec["phone"],
            is_msme=c_spec["msme"],
            is_startup=c_spec["startup"],
        )
        db.session.add(comp)
        db.session.flush()
        companies.append(comp)

    # 5. Create 3 Sample Tenders
    req_docs_std = json.dumps([
        "Technical Bid",
        "GST Certificate",
        "PAN",
        "Udyam/MSME Certificate",
        "OEM Authorization",
    ])

    tender1 = Tender(
        tender_code="GEM/2026/B/5011201",
        title="Procurement of 250 Units AI-Ready Enterprise Workstations & Compute Systems",
        department="Ministry of Electronics & Information Technology (MeitY)",
        description=(
            "Supply, installation, and 3-year comprehensive on-site warranty of high-performance enterprise "
            "workstations for Digital India State Data Centres under PPP-MII Class-I/II norms."
        ),
        publication_date="2026-09-10",
        closing_date="2026-10-30",
        category="IT Hardware & Enterprise Workstations",
        estimated_value=32500000.0,
        eligibility_requirements="Minimum 3 years experience in central/state government IT supply; Valid ISO 9001 & BIS registration.",
        technical_requirements="RAM >= 16 GB DDR5, NVMe SSD >= 512 GB, On-site Comprehensive Warranty >= 3 Years.",
        statutory_requirements="Active GSTIN with regular GSTR-3B filings, Valid Corporate PAN, Udyam MSME Certificate, EPFO & ESIC compliance.",
        required_documents=req_docs_std,
        local_content_requirements=50.0,
        oem_requirements="Direct OEM or Authorized Reseller with tender-specific Manufacturer Authorization Form (MAF).",
        other_requirements="Zero debarment record on GeM / DoE watchlist; RoHS & UL certifications.",
        status="PUBLISHED",
        created_by=officer_user1.id,
    )

    tender2 = Tender(
        tender_code="GEM/2026/B/5011202",
        title="Supply & Commissioning of Managed Layer-3 Core Network Switches & Next-Gen Firewalls",
        department="National Informatics Centre (NIC) - Central Network Division",
        description=(
            "Enterprise datacenter switching and perimeter firewall appliances with 24x7 support "
            "and Indigenous Cyber Security compliance."
        ),
        publication_date="2026-09-14",
        closing_date="2026-11-05",
        category="Networking & Cybersecurity Appliances",
        estimated_value=18000000.0,
        eligibility_requirements="OEM or Tier-1 Partner with valid TEC/MTCTE certification and 3 years Government supply track record.",
        technical_requirements="ThroughputRAM >= 32 GB, FlashSSD >= 512 GB, Comprehensive Warranty >= 3 Years.",
        statutory_requirements="Active GSTIN, Valid PAN, Udyam/MSME or Startup India certificate, EPFO & ESIC compliance.",
        required_documents=req_docs_std,
        local_content_requirements=50.0,
        oem_requirements="Valid OEM Authorization Form (MAF) mandatory.",
        other_requirements="Must comply with MeitY Trusted Telecom Portal norms.",
        status="PUBLISHED",
        created_by=officer_user1.id,
    )

    tender3 = Tender(
        tender_code="GEM/2026/B/5011203",
        title="Procurement of Multi-Parameter ICU Patient Monitors & Central Telemetry Stations",
        department="Ministry of Health & Family Welfare (AIIMS Central Procurement)",
        description=(
            "High-acuity bedside multipara patient monitoring units with embedded compute modules "
            "for regional AIIMS trauma & critical care centres."
        ),
        publication_date="2026-09-18",
        closing_date="2026-11-12",
        category="Medical Electronics & Hospital Telemetry",
        estimated_value=24000000.0,
        eligibility_requirements="CDSCO Medical Device License & ISO 13485 quality certification.",
        technical_requirements="System RAM >= 16 GB, Internal Storage SSD >= 512 GB, Comprehensive Warranty >= 3 Years.",
        statutory_requirements="Active GSTIN, Valid PAN, Udyam Registration, EPFO/ESIC compliance.",
        required_documents=req_docs_std,
        local_content_requirements=50.0,
        oem_requirements="Direct Medical Device OEM or Authorized Distributor with MAF.",
        other_requirements="BIS & CDSCO safety compliance.",
        status="PUBLISHED",
        created_by=officer_user2.id,
    )

    db.session.add_all([tender1, tender2, tender3])
    db.session.flush()

    # Add structured TenderRequirements for each tender
    for t in (tender1, tender2, tender3):
        req_ram = "32" if t.id == tender2.id else "16"
        db.session.add_all([
            TenderRequirement(
                tender_id=t.id,
                category="TECHNICAL",
                parameter_name="RAM",
                operator=">=",
                required_value=req_ram,
                unit="GB",
                is_mandatory=True,
                description=f"Minimum system memory RAM >= {req_ram} GB",
            ),
            TenderRequirement(
                tender_id=t.id,
                category="TECHNICAL",
                parameter_name="SSD",
                operator=">=",
                required_value="512",
                unit="GB",
                is_mandatory=True,
                description="Minimum solid state storage SSD >= 512 GB",
            ),
            TenderRequirement(
                tender_id=t.id,
                category="TECHNICAL",
                parameter_name="Warranty",
                operator=">=",
                required_value="3",
                unit="Years",
                is_mandatory=True,
                description="Minimum comprehensive on-site warranty >= 3 Years",
            ),
        ])
    db.session.flush()

    record_audit_log("Tender Created", user=officer_user1, tender_id=tender1.id, result_status="PUBLISHED", commit=False)
    record_audit_log("Tender Created", user=officer_user1, tender_id=tender2.id, result_status="PUBLISHED", commit=False)
    record_audit_log("Tender Created", user=officer_user2, tender_id=tender3.id, result_status="PUBLISHED", commit=False)

    # 6. Create 10 Sample Bids across the 3 Tenders covering Compliant, Non-Compliant, Anomaly, Inconsistent, and Missing Document cases
    bids_seed_specs = [
        # Bid 1: Fully Compliant Bid (Apex Bharat -> Tender 1)
        {
            "bid_number": "GEM-BID-2026-1001",
            "tender": tender1,
            "company": companies[0],
            "quoted": 30850000.0,
            "warranty": 3.0,
            "delivery": 28,
            "lc": 68.0,
            "oem_status": "Direct OEM Manufacturer",
            "product_name": "ApexPro Sovereign Workstation W790",
            "product_model": "APX-W790-16G",
            "ram": 32,
            "ssd": 1024,
            "doc_lc": 68.0,
            "include_docs": ["Technical Bid", "GST Certificate", "PAN", "Udyam/MSME Certificate", "OEM Authorization"],
            "review_status": "VERIFIED",
            "review_comments": "All statutory certificates, technical specs (32GB RAM, 1TB SSD), and MII local content (68%) verified against evidence.",
        },
        # Bid 2: Non-Compliant Technical Spec SSD=256GB < 512GB & Missing OEM Doc (NovaGrid -> Tender 1)
        {
            "bid_number": "GEM-BID-2026-1002",
            "tender": tender1,
            "company": companies[1],
            "quoted": 29500000.0,
            "warranty": 3.0,
            "delivery": 35,
            "lc": 54.0,
            "oem_status": "Authorized Reseller",
            "product_name": "NovaDesk Enterprise Node D4",
            "product_model": "ND-D4-256",
            "ram": 16,
            "ssd": 256,  # Below required 512 GB!
            "doc_lc": 54.0,
            "include_docs": ["Technical Bid", "GST Certificate", "PAN", "Udyam/MSME Certificate"],  # Missing OEM Authorization!
            "review_status": "REQUIRES_CLARIFICATION",
            "review_comments": "Submitted SSD capacity (256 GB) on Technical Bid Page 4 is below the 512 GB minimum requirement, and OEM MAF certificate is missing.",
        },
        # Bid 3: ML Anomaly Detected: Warranty = 30 Years! Needs Human Review (Shakti Hardware -> Tender 1)
        {
            "bid_number": "GEM-BID-2026-1003",
            "tender": tender1,
            "company": companies[2],
            "quoted": 31200000.0,
            "warranty": 30.0,  # Isolation Forest Anomaly (30 years vs normal 3 years!)
            "delivery": 25,
            "lc": 74.0,
            "oem_status": "Direct OEM Manufacturer",
            "product_name": "Shakti Vikrant Compute Station",
            "product_model": "SV-CS-2026",
            "ram": 16,
            "ssd": 512,
            "doc_lc": 74.0,
            "include_docs": ["Technical Bid", "GST Certificate", "PAN", "Udyam/MSME Certificate", "OEM Authorization"],
            "review_status": "PENDING_REVIEW",
            "review_comments": None,
        },
        # Bid 4: High Risk / Suspended GSTIN + Watchlist Alert + Low Local Content (Vanguard Infra -> Tender 1)
        {
            "bid_number": "GEM-BID-2026-1004",
            "tender": tender1,
            "company": companies[3],
            "quoted": 28900000.0,
            "warranty": 2.0,  # Below 3 years
            "delivery": 45,
            "lc": 35.0,  # Below 50% MII requirement
            "oem_status": "Unauthorized Trader",
            "product_name": "Vanguard Generic Desktop PC",
            "product_model": "VG-PC-100",
            "ram": 8,  # Below 16 GB
            "ssd": 256,  # Below 512 GB
            "doc_lc": 35.0,
            "include_docs": ["Technical Bid", "GST Certificate", "PAN"],
            "review_status": "REVIEWED",
            "review_comments": "Multiple high-risk compliance failures: Suspended GSTIN, low local content (35%), RAM 8GB, SSD 256GB.",
        },
        # Bid 5: Cross-Document Inconsistency (Pragati Digital -> Tender 1: Form says 62% LC, Technical Bid says 42% LC, and GSTIN mismatch)
        {
            "bid_number": "GEM-BID-2026-1005",
            "tender": tender1,
            "company": companies[4],
            "quoted": 31500000.0,
            "warranty": 3.0,
            "delivery": 30,
            "lc": 62.0,
            "oem_status": "Authorized OEM Partner",
            "product_name": "Pragati SmartStation S1",
            "product_model": "PSS-S1-16",
            "ram": 16,
            "ssd": 512,
            "doc_lc": 42.0,  # Conflicts with 62.0% declared in bid form!
            "override_doc_gstin": "24AABCP0000Z1Z9",  # Conflicts with profile GSTIN!
            "include_docs": ["Technical Bid", "GST Certificate", "PAN", "Udyam/MSME Certificate", "OEM Authorization"],
            "review_status": "REQUIRES_CLARIFICATION",
            "review_comments": "Inconsistency detected between portal declaration (62% Local Content) and Technical Bid Page 2 (42% Local Content), plus GSTIN mismatch.",
        },
        # Bid 6: Fully Compliant Bid on Tender 2 (Shakti Hardware -> Tender 2)
        {
            "bid_number": "GEM-BID-2026-2001",
            "tender": tender2,
            "company": companies[2],
            "quoted": 17100000.0,
            "warranty": 5.0,
            "delivery": 21,
            "lc": 74.0,
            "oem_status": "Direct Indigenous OEM",
            "product_name": "Shakti NetCore L3-9600 Switch & Firewall",
            "product_model": "SNC-9600-32G",
            "ram": 64,
            "ssd": 1024,
            "doc_lc": 74.0,
            "include_docs": ["Technical Bid", "GST Certificate", "PAN", "Udyam/MSME Certificate", "OEM Authorization"],
            "review_status": "VERIFIED",
            "review_comments": "Compliant with all NIC Layer-3 switching and memory specifications.",
        },
        # Bid 7: Compliant Bid on Tender 2 (Apex Bharat -> Tender 2)
        {
            "bid_number": "GEM-BID-2026-2002",
            "tender": tender2,
            "company": companies[0],
            "quoted": 17450000.0,
            "warranty": 3.0,
            "delivery": 30,
            "lc": 68.0,
            "oem_status": "Authorized OEM Partner",
            "product_name": "ApexShield CoreSwitch CS-48",
            "product_model": "ACS-48-32G",
            "ram": 32,
            "ssd": 512,
            "doc_lc": 68.0,
            "include_docs": ["Technical Bid", "GST Certificate", "PAN", "Udyam/MSME Certificate", "OEM Authorization"],
            "review_status": "REVIEWED",
            "review_comments": "All technical and statutory parameters verified.",
        },
        # Bid 8: Non-Compliant RAM on Tender 2 (NovaGrid -> Tender 2: RAM=16GB < 32GB required)
        {
            "bid_number": "GEM-BID-2026-2003",
            "tender": tender2,
            "company": companies[1],
            "quoted": 16800000.0,
            "warranty": 3.0,
            "delivery": 30,
            "lc": 54.0,
            "oem_status": "Authorized Reseller",
            "product_name": "NovaSwitch L3 Lite",
            "product_model": "NS-L3-16G",
            "ram": 16,  # Tender 2 requires 32 GB
            "ssd": 512,
            "doc_lc": 54.0,
            "include_docs": ["Technical Bid", "GST Certificate", "PAN", "Udyam/MSME Certificate", "OEM Authorization"],
            "review_status": "PENDING_REVIEW",
            "review_comments": None,
        },
        # Bid 9: Compliant Bid on Tender 3 (Pragati Digital -> Tender 3)
        {
            "bid_number": "GEM-BID-2026-3001",
            "tender": tender3,
            "company": companies[4],
            "quoted": 22800000.0,
            "warranty": 3.0,
            "delivery": 28,
            "lc": 62.0,
            "oem_status": "Authorized Medical OEM Partner",
            "product_name": "Pragati CareView ICU-16 Monitor",
            "product_model": "PCV-ICU16",
            "ram": 16,
            "ssd": 512,
            "doc_lc": 62.0,
            "include_docs": ["Technical Bid", "GST Certificate", "PAN", "Udyam/MSME Certificate", "OEM Authorization"],
            "review_status": "VERIFIED",
            "review_comments": "Meets AIIMS ICU telemetry specifications and statutory requirements.",
        },
        # Bid 10: High Risk Bid on Tender 3 (Vanguard Infra -> Tender 3: Unusually low price anomaly + missing Udyam & OEM)
        {
            "bid_number": "GEM-BID-2026-3002",
            "tender": tender3,
            "company": companies[3],
            "quoted": 8500000.0,  # 35% of estimated value -> Isolation Forest anomaly!
            "warranty": 1.0,
            "delivery": 240,  # 240 days -> Anomaly!
            "lc": 35.0,
            "oem_status": "Distributor",
            "product_name": "Vanguard Basic Monitor",
            "product_model": "VBM-8",
            "ram": 8,
            "ssd": 256,
            "doc_lc": 35.0,
            "include_docs": ["Technical Bid", "GST Certificate", "PAN"],
            "review_status": "PENDING_REVIEW",
            "review_comments": None,
        },
    ]

    for b_spec in bids_seed_specs:
        comp = b_spec["company"]
        tender = b_spec["tender"]
        bid = Bid(
            bid_number=b_spec["bid_number"],
            tender_id=tender.id,
            company_id=comp.id,
            quoted_amount=b_spec["quoted"],
            warranty_years=b_spec["warranty"],
            delivery_days=b_spec["delivery"],
            local_content_declared=b_spec["lc"],
            oem_status=b_spec["oem_status"],
            product_name=b_spec["product_name"],
            product_model=b_spec["product_model"],
            technical_summary=(
                f"Offered Model: {b_spec['product_name']} ({b_spec['product_model']}) | "
                f"RAM: {b_spec['ram']} GB | SSD: {b_spec['ssd']} GB | Warranty: {b_spec['warranty']:g} Years"
            ),
            declarations_accepted=True,
            submission_status="SUBMITTED",
            officer_review_status=b_spec["review_status"],
            officer_review_comments=b_spec["review_comments"],
            reviewed_by=officer_user1.id if b_spec["review_status"] != "PENDING_REVIEW" else None,
        )
        db.session.add(bid)
        db.session.flush()

        # Add BidItems
        db.session.add_all([
            BidItem(
                bid_id=bid.id,
                item_category="TECHNICAL",
                parameter_name="RAM",
                submitted_value=str(b_spec["ram"]),
                unit="GB",
                source_document="Technical_Bid.pdf",
                source_page=4,
            ),
            BidItem(
                bid_id=bid.id,
                item_category="TECHNICAL",
                parameter_name="SSD",
                submitted_value=str(b_spec["ssd"]),
                unit="GB",
                source_document="Technical_Bid.pdf",
                source_page=4,
            ),
            BidItem(
                bid_id=bid.id,
                item_category="TECHNICAL",
                parameter_name="Warranty",
                submitted_value=str(b_spec["warranty"]),
                unit="Years",
                source_document="Technical_Bid.pdf",
                source_page=5,
            ),
        ])

        # Create realistic sample document files & run OCR/NLP pipeline on each
        doc_templates = {
            "Technical Bid": (
                f"Technical_Bid_{b_spec['bid_number']}.pdf",
                f"[Page 1]\nTECHNICAL BID SUBMISSION - GeM Tender {tender.tender_code}\n"
                f"Bidder Name: {comp.company_name}\n"
                f"Offered Product: {b_spec['product_name']} ({b_spec['product_model']})\n\n"
                f"[Page 2]\nMAKE IN INDIA (PPP-MII) DECLARATION\n"
                f"Local Content Percentage: {b_spec['doc_lc']}%\n\n"
                f"[Page 4]\nBILL OF MATERIALS & TECHNICAL SPECIFICATIONS\n"
                f"Processor: Intel Xeon / Core Ultra Enterprise Series\n"
                f"RAM Capacity: {b_spec['ram']} GB\n"
                f"SSD Capacity: {b_spec['ssd']} GB\n\n"
                f"[Page 5]\nWARRANTY & SLA TERMS\n"
                f"Warranty Period: {b_spec['warranty']:g} Years On-Site Comprehensive Warranty\n",
            ),
            "GST Certificate": (
                f"GST_Certificate_{b_spec['bid_number']}.pdf",
                f"[Page 1]\nGOVERNMENT OF INDIA - FORM GST REG-06\n"
                f"Goods and Services Tax Registration Certificate\n"
                f"Registration Number (GSTIN): {b_spec.get('override_doc_gstin', comp.gstin)}\n"
                f"Legal Name: {comp.company_name}\n"
                f"Trade Name: {comp.company_name}\n"
                f"Registration Status: {'SUSPENDED' if '33AABCV4321F1Z9' in comp.gstin else 'ACTIVE'}\n",
            ),
            "PAN": (
                f"PAN_Card_{b_spec['bid_number']}.pdf",
                f"[Page 1]\nINCOME TAX DEPARTMENT - GOVT. OF INDIA\n"
                f"Permanent Account Number (PAN): {comp.pan}\n"
                f"Name: {comp.company_name}\n",
            ),
            "Udyam/MSME Certificate": (
                "Udyam Registration Certificate.pdf",
                f"[Page 1]\nMINISTRY OF MICRO, SMALL AND MEDIUM ENTERPRISES\n"
                f"UDYAM REGISTRATION CERTIFICATE\n"
                f"Udyam Registration Number: {comp.udyam_number}\n"
                f"Name of Enterprise: {comp.company_name}\n"
                f"Type of Enterprise: {comp.enterprise_type}\n"
                f"Status: ACTIVE\n",
            ),
            "OEM Authorization": (
                f"OEM_MAF_Certificate_{b_spec['bid_number']}.pdf",
                f"[Page 1]\nMANUFACTURER'S AUTHORIZATION FORM (MAF)\n"
                f"OEM Authorization Status: {b_spec['oem_status']}\n"
                f"We hereby authorize {comp.company_name} to submit a bid for GeM Tender {tender.tender_code}.\n",
            ),
        }

        for doc_cat in b_spec["include_docs"]:
            orig_fname, content_text = doc_templates[doc_cat]
            disk_fname = f"demo_{bid.id}_{orig_fname.replace(' ', '_')}"
            fpath, fsize = _create_sample_document_file(disk_fname, content_text)
            doc_obj = Document(
                bid_id=bid.id,
                tender_id=tender.id,
                original_filename=orig_fname,
                safe_filename=disk_fname,
                file_type="pdf",
                file_size_bytes=fsize,
                file_path=fpath,
                declared_doc_type=doc_cat,
            )
            db.session.add(doc_obj)
            db.session.flush()
            process_document_pipeline(doc_obj, commit=False)

        record_audit_log(
            "Bid Submitted",
            user=comp.user,
            tender_id=tender.id,
            bid_id=bid.id,
            result_status="SUBMITTED",
            commit=False,
        )

        # Run Automated Compliance & ML Risk Verification on all seeded bids
        summary = run_bid_compliance_verification(bid, commit=False)
        if b_spec["review_status"] == "VERIFIED":
            bid.verification_status = "VERIFIED"

        record_audit_log(
            "Compliance Result Generated",
            user=officer_user1,
            tender_id=tender.id,
            bid_id=bid.id,
            result_status=f"Score: {summary['overall_compliance_score']}% | Risk: {summary['risk_level']}",
            review_comments=b_spec["review_comments"] or "Automated Verification Complete",
            commit=False,
        )

    db.session.commit()
    print("Seed data completed successfully!")


if __name__ == "__main__":
    from backend.app import create_app

    app = create_app()
    with app.app_context():
        seed_demo_data()
        print("Demo database re-seeded successfully.")
