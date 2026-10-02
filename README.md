# BidVerify – AI-Powered Bid Compliance Verification Platform for GeM Procurement

**Smart India Hackathon (SIH) Problem Statement 26100**

> **IMPORTANT GOVERNANCE & DECISION-SUPPORT MANDATE:**
> This platform is strictly a **compliance verification and decision-support system**. It does **NOT** automatically select a winning bidder or make final procurement award/rejection decisions. It assists the authorized Procurement Officer by preprocessing documents, extracting structured fields via an integrated **EasyOCR** and NLP pipeline, comparing tender requirements, detecting cross-document inconsistencies, flagging statistical anomalies via Scikit-learn Isolation Forest, linking page-level evidence, and generating downloadable PDF reports. Final procurement decisions remain exclusively with the authorized Procurement Officer.

---

## 1. Project Overview & EasyOCR Integration Architecture

Public procurement on the **Government e-Marketplace (GeM)** requires evaluating complex multi-document bids containing Technical Bids, GST Certificates, PAN Cards, Udyam/MSME Registrations, Make in India (PPP-MII) Local Content Declarations, OEM Manufacturer Authorization Forms (MAF), and EPFO/ESIC statutory records.

**BidVerify** incorporates an end-to-end **EasyOCR** text extraction pipeline tailored specifically for public procurement compliance:

```text
Document Upload
      ↓
PDF / Image Processing (pypdf digital pass-through or pypdfium2 page rasterization)
      ↓
Image Preprocessing (OpenCV: auto-scaling, grayscale, CLAHE contrast, Gaussian denoising)
      ↓
EasyOCR Engine (Singleton Reader, bounding boxes, text & confidence scores)
      ↓
Extracted Text (Preserves page order with [Page X] demarcations)
      ↓
Entity Extraction (Regex, spaCy, RapidFuzz: GSTIN, PAN, Udyam, Company, Technical Specs)
      ↓
Compliance Verification Rule Engine (Evaluates tender requirements against extracted data)
      ↓
Risk Analysis (Scikit-learn Isolation Forest anomaly & statistical risk scoring)
      ↓
Human Review (Procurement Officer decision-support dashboard)
      ↓
Audit Trail & PDF Report Generation
```

### Key Technical Pillars of the EasyOCR Pipeline:
1. **Exclusive OCR Engine**: Powered exclusively by **EasyOCR** (`easyocr>=1.7.1`). No secondary or competing engines (PaddleOCR, Tesseract, Google Vision, Textract, Azure OCR) are used.
2. **Singleton Reader Pattern**: `easyocr.Reader(['en'], gpu=Config.OCR_USE_GPU)` is initialized once as a lazy-loaded thread-safe singleton, preventing redundant model instantiation and memory overhead across concurrent document uploads.
3. **Configurable GPU & Confidence Thresholds**:
   - `OCR_USE_GPU=false` (runs smoothly on CPU; enables GPU acceleration when CUDA is available)
   - `OCR_CONFIDENCE_THRESHOLD=0.60` (configurable threshold for flagging low-confidence extractions for Human Review)
4. **Hybrid PDF Support**:
   - **Digital PDFs**: Evaluates native text streams via `pypdf`. If selectable text exists, extracts directly with maximum speed and 100% fidelity.
   - **Scanned / Image-based PDFs**: Converts each page into a high-resolution PIL image using `pypdfium2`, runs image preprocessing, extracts text page-by-page with EasyOCR, and preserves page ordering with `[Page X]` headers.
5. **Lightweight Image Preprocessing**: Uses OpenCV to upscale low-resolution scans (width < 800px), apply grayscale conversion, contrast-limited adaptive histogram equalization (CLAHE), and gentle Gaussian noise reduction before feeding into EasyOCR.
6. **Confidence-Aware Human-in-the-Loop**: If EasyOCR confidence is below `0.60`, the system automatically marks the document and relevant statutory checks as `NEEDS_REVIEW` with an explicit reason for the Procurement Officer to inspect.
7. **Transparent Frontend Inspection**: Both Procurement Officers and Bidders can inspect OCR status, pages processed, extracted entities with confidence scores, and raw OCR text via the "DOCUMENT ANALYSIS" preview modal.

---

## 2. Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript (ES6+), Bootstrap 5.3, Chart.js (25 Responsive Pages) |
| **Backend** | Python 3, Flask, Flask-SQLAlchemy, REST API Architecture, PyJWT Authentication, Werkzeug Security |
| **Database** | PostgreSQL (`backend/schema.sql` with 16 relational tables; automatic fallback to SQLite `gem_compliance.db` in local demo mode) |
| **OCR Layer** | **EasyOCR** (`easyocr`), OpenCV (`cv2`), `pypdfium2`, `pypdf` |
| **NLP & Entity Extraction** | Regular Expressions, spaCy (`en_core_web_sm`), RapidFuzz |
| **Machine Learning** | Scikit-learn (`IsolationForest`), NumPy |
| **Reporting & Export** | ReportLab (Downloadable enterprise PDF compliance reports) |
| **Testing** | Pytest (10 automated end-to-end integration tests) |

---

## 3. Project Directory Structure

```text
gem-compliance-platform/
├── backend/
│   ├── app.py                      # Flask app factory, CORS, static serving & health check
│   ├── config.py                   # Config & OCR settings (OCR_USE_GPU, OCR_CONFIDENCE_THRESHOLD)
│   ├── extensions.py               # SQLAlchemy db instance
│   ├── schema.sql                  # Complete 16-table PostgreSQL DDL schema
│   ├── seed_demo.py                # Seeds 3 tenders, 5 companies, 10 bids, sample docs & checks
│   ├── auth/
│   │   └── decorators.py           # JWT generation, validation & RBAC decorators
│   ├── models/
│   │   └── models.py               # 16 SQLAlchemy ORM models (includes ocr_confidence, ocr_details_json)
│   ├── routes/
│   │   ├── auth_routes.py          # /api/auth/*
│   │   ├── tender_routes.py        # /api/tenders/*
│   │   ├── bid_routes.py           # /api/tenders/{id}/bids, /api/bids/*, /api/dashboard/stats
│   │   ├── document_routes.py      # /api/bids/{id}/documents, /api/documents/{id}/process
│   │   ├── compliance_routes.py    # /api/bids/{id}/verify, /compliance, /risk, /review
│   │   ├── report_routes.py        # /api/bids/{id}/report, /api/reports/{id}
│   │   └── audit_routes.py         # /api/audit-logs
│   ├── ocr/
│   │   ├── __init__.py
│   │   ├── easyocr_engine.py       # Core EasyOCR Singleton, OpenCV Preprocessing, Hybrid PDF & Confidence
│   │   └── ocr_engine.py           # Clean abstraction routing all extraction to easyocr_engine
│   ├── document_processing/
│   │   ├── classifier.py           # Content + Regex + RapidFuzz document classifier
│   │   ├── extractor.py            # Regex + spaCy + RapidFuzz structured field & entity extractor
│   │   └── pipeline.py             # End-to-end document processing pipeline
│   ├── compliance/
│   │   └── engine.py               # 17-point modular compliance verification & scoring engine
│   ├── ml/
│   │   └── risk_analyzer.py        # Scikit-learn Isolation Forest anomaly & risk analyzer
│   ├── integrations/               # DEMO / MOCK External Government Adapters
│   │   ├── gst_service.py
│   │   ├── udyam_service.py
│   │   ├── mca_service.py
│   │   ├── digilocker_service.py
│   │   ├── epfo_service.py
│   │   ├── esic_service.py
│   │   └── blacklist_service.py
│   ├── reports/
│   │   └── pdf_generator.py        # ReportLab PDF compliance report builder with EasyOCR metadata
│   ├── services/
│   │   └── audit_service.py        # Immutable audit log recording service
│   └── utils/
│       ├── responses.py            # Standardized JSON API success/error builders
│       └── validators.py           # File type, size, empty file & duplicate filename validators
├── frontend/
│   ├── index.html                  # Landing Page
│   ├── about.html                  # About the Platform
│   ├── how-it-works.html           # System Workflow & OCR Details
│   ├── login.html                  # Secure Login (with 1-click SIH demo credentials)
│   ├── register.html               # Registration Page with password policy enforcement
│   ├── officer/                    # Procurement Officer Portal (bid-details.html, document-analysis.html, etc.)
│   ├── company/                    # Offering Company / Bidder Portal (upload-documents.html, submission-status.html, etc.)
│   ├── css/styles.css
│   └── js/api.js
├── uploads/                        # Uploaded bid documents
├── reports_output/                 # Generated ReportLab PDF reports
├── tests/
│   └── test_platform.py            # 10 comprehensive Pytest verification suites
├── .env.example
├── requirements.txt
└── README.md
```

---

## 4. Installation & Setup

### Step 1: Install Python Dependencies
```bash
pip install -r requirements.txt
```
*Note: Key dependencies include `easyocr>=1.7.1`, `torch`, `opencv-python-headless>=4.9.0`, `pypdfium2>=4.30.0`, `pypdf>=4.0.0`, `spacy>=3.7.0`, `scikit-learn>=1.4.0`, and `reportlab>=4.1.0`.*

### Step 2: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Key configurable parameters:
- `OCR_USE_GPU=false` (Set to `true` if an NVIDIA CUDA GPU is available)
- `OCR_CONFIDENCE_THRESHOLD=0.60` (Extractions below this threshold trigger Human Review)
- `OCR_LANGUAGES=en` (Configurable list of languages for EasyOCR, e.g. `en`)
- `DATABASE_URL=postgresql://postgres:postgres@localhost:5432/gem_compliance_db`
- `ALLOW_SQLITE_FALLBACK=true` (Falls back to `gem_compliance.db` if PostgreSQL is not active)
- `JWT_SECRET_KEY=dev-jwt-secret-key-change-in-prod`
- `WEIGHT_DOCUMENT_COMPLIANCE=0.25`
- `WEIGHT_STATUTORY_COMPLIANCE=0.25`
- `WEIGHT_TECHNICAL_COMPLIANCE=0.30`
- `WEIGHT_TENDER_COMPLIANCE=0.20`
- `INTEGRATION_MODE=MOCK`

---

## 5. Running the Application

Start the full-stack server:
```bash
python backend/app.py
```
Open **`http://localhost:5000`** in your browser.

---

## 6. How Document Upload & EasyOCR Work Together

1. **Document Upload**:
   The bidder submits files via `POST /api/bids/<id>/documents`. The endpoint validates MIME types (`pdf, png, jpg, jpeg, txt, doc, docx`), enforces the 25 MB limit, checks against 0-byte corrupted uploads, and generates a collision-free filename.
2. **Text Extraction**:
   `backend/ocr/easyocr_engine.py` inspects the document:
   - For images (`.png`, `.jpg`, `.jpeg`): applies OpenCV grayscale and CLAHE contrast enhancement, then runs `easyocr.Reader.readtext()`, returning extracted text, confidence scores, and bounding boxes.
   - For PDFs: checks for digital selectable text. If present, extracts directly. If scanned, renders each page into an image via `pypdfium2`, runs EasyOCR, and joins pages with `[Page X]` headers.
3. **Entity Extraction**:
   `backend/document_processing/extractor.py` scans the extracted text for procurement entities (GSTIN, PAN, Udyam ID, dates, company names, and technical specifications) and correlates field-level confidence scores.
4. **Compliance Verification**:
   `backend/compliance/engine.py` evaluates mandatory document presence, statutory credentials, Make in India local content, OEM authorization, and technical specification minimums. If any document has low OCR confidence (< 0.60), the check status is automatically set to `NEEDS_REVIEW`.
5. **Human Review**:
   The Procurement Officer inspects the document in `frontend/officer/bid-details.html`, opens the **DOCUMENT ANALYSIS** modal to inspect extracted fields, confidence scores, and raw OCR text, and renders the final procurement qualification decision.

---

## 7. Running Automated Tests

Run the full automated test suite covering all 10 evaluation scenarios:
```bash
pytest -v tests/test_platform.py
```
Test suite coverage:
- `test_1_fully_compliant_bid_report_and_audit`: Compliant bid + document classification + report + audit trail
- `test_2_missing_document_detection`: Detection of missing mandatory tender documents
- `test_3_wrong_technical_specification`: Detection of substandard technical parameter (`SSD = 256 GB` vs `>= 512 GB`)
- `test_4_conflicting_information_detection`: Cross-document discrepancy detection (GSTIN and Local Content %)
- `test_5_ocr_failure_handling`: Graceful error handling (422) on corrupted scan upload
- `test_6_anomalous_value_isolation_forest`: Scikit-learn Isolation Forest anomaly detection (`Warranty = 30 years`)
- `test_7_unauthorized_company_cross_bid_access`: RBAC verification protecting company data
- `test_8_invalid_file_upload_rejection`: Validation of disallowed file extensions and corrupted files
- `test_9_officer_human_review_workflow`: Formal officer review and qualification lifecycle
- `test_10_pdf_report_download_content`: End-to-end verification of ReportLab PDF generation with EasyOCR metadata
