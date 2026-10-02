import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models.models import MockGovRecord

# Fallback in-memory registry if database record is not pre-populated
FALLBACK_GOV_REGISTRY = {
    "36ABCDE1234F1Z5": {
        "portal": "GSTN (Goods and Services Tax Network)",
        "gstin": "36ABCDE1234F1Z5",
        "legal_name": "Alpha Logix Solutions Private Limited",
        "trade_name": "Alpha Logix Tech",
        "status": "Active",
        "pan": "ABCDE1234F",
        "state": "Telangana",
        "pincode": "500081",
        "address": "Plot 42, Hitech City, Madhapur, Hyderabad, Telangana - 500081",
        "registration_date": "2020-04-15",
        "taxpayer_type": "Regular",
        "is_mock": True
    },
    "27AABCA5678B1Z2": {
        "portal": "GSTN (Goods and Services Tax Network)",
        "gstin": "27AABCA5678B1Z2",
        "legal_name": "Apex Infra Projects Limited",
        "trade_name": "Apex Infrastructure",
        "status": "Active",
        "pan": "AABCA5678B",
        "state": "Maharashtra",
        "pincode": "400051",
        "address": "Tower B, Level 14, Bandra Kurla Complex, Bandra East, Mumbai, Maharashtra - 400051",
        "registration_date": "2018-09-12",
        "taxpayer_type": "Regular",
        "is_mock": True
    },
    "29AAACZ9999C1Z3": {
        "portal": "GSTN (Goods and Services Tax Network)",
        "gstin": "29AAACZ9999C1Z3",
        "legal_name": "Zenith Global Supplies LLP",
        "trade_name": "Zenith Supplies",
        "status": "Active",
        "pan": "AAACZ9999C",
        "state": "Karnataka",
        "pincode": "560001",
        "address": "Brigade Towers, MG Road, Bengaluru, Karnataka - 560001",
        "registration_date": "2021-01-20",
        "taxpayer_type": "Regular",
        "is_mock": True
    },
    "07AABCN1111D1Z4": {
        "portal": "GSTN (Goods and Services Tax Network)",
        "gstin": "07AABCN1111D1Z4",
        "legal_name": "NovaTech Electronics Solutions Private Limited",
        "trade_name": "NovaTech Electronics",
        "status": "Active",
        "pan": "AABCN1111D",
        "state": "Delhi",
        "pincode": "110020",
        "address": "Okhla Industrial Area Phase III, New Delhi - 110020",
        "registration_date": "2022-06-10",
        "taxpayer_type": "Regular",
        "is_mock": True
    },
    "33AABCV2222E1Z8": {
        "portal": "GSTN (Goods and Services Tax Network)",
        "gstin": "33AABCV2222E1Z8",
        "legal_name": "Vanguard Trading Hub Private Limited",
        "trade_name": "Vanguard Enterprises",
        "status": "Active",
        "pan": "AABCV2222E",
        "state": "Tamil Nadu",
        "pincode": "600002",
        "address": "Mount Road, Anna Salai, Chennai, Tamil Nadu - 600002",
        "registration_date": "2023-11-05",
        "taxpayer_type": "Regular",
        "is_mock": True
    },
    "06AABCM3333F1Z1": {
        "portal": "GSTN (Goods and Services Tax Network)",
        "gstin": "06AABCM3333F1Z1",
        "legal_name": "Metro Logistics Corporation",
        "trade_name": "Metro Freight",
        "status": "Suspended",  # Suspended GST scenario
        "pan": "AABCM3333F",
        "state": "Haryana",
        "pincode": "122002",
        "address": "DLF Cyber City, Sector 24, Gurugram, Haryana - 122002",
        "registration_date": "2019-02-14",
        "taxpayer_type": "Regular",
        "is_mock": True
    }
}

class GovernmentVerificationService:
    """
    Standard interface for Government Portal Inquiries (GSTN, Udyam, MCA21).
    All mock endpoints clearly indicate 'Demo / Mock Verification Data'.
    Designed with a clean plug-in architecture so authorized live APIs can be seamlessly linked.
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def verify_gst(self, gstin: str) -> Dict[str, Any]:
        normalized = gstin.upper().strip()
        
        # Check DB first if session available
        if self.db:
            record = self.db.query(MockGovRecord).filter(MockGovRecord.gstin == normalized).first()
            if record:
                return {
                    "source": "Mock GSTN Portal (Demo / Simulated)",
                    "portal_code": "GSTN",
                    "is_live_api": False,
                    "disclaimer": "This is simulated demo data for procurement verification testing.",
                    "gstin": record.gstin,
                    "legal_name": record.legal_name,
                    "trade_name": record.trade_name or record.legal_name,
                    "status": record.status,
                    "pan": record.pan or (record.gstin[2:12] if len(record.gstin) >= 12 else ""),
                    "state": record.state,
                    "pincode": record.pincode,
                    "address": record.address,
                    "registration_date": record.registration_date,
                    "taxpayer_type": "Regular",
                    "retrieved_at": datetime.datetime.utcnow().isoformat()
                }

        # Check in-memory fallback
        if normalized in FALLBACK_GOV_REGISTRY:
            data = dict(FALLBACK_GOV_REGISTRY[normalized])
            data["source"] = "Mock GSTN Portal (Demo / Simulated)"
            data["is_live_api"] = False
            data["disclaimer"] = "This is simulated demo data for procurement verification testing."
            data["retrieved_at"] = datetime.datetime.utcnow().isoformat()
            return data

        # Dynamic mock synthesis for newly entered GSTINs so tests never get stuck
        pan_extracted = normalized[2:12] if len(normalized) >= 12 else "PAN000000X"
        return {
            "source": "Mock GSTN Portal (Demo / Simulated)",
            "portal_code": "GSTN",
            "is_live_api": False,
            "disclaimer": "This is simulated demo data for procurement verification testing.",
            "gstin": normalized,
            "legal_name": f"Registered Entity {normalized[-4:]} Pvt Ltd",
            "trade_name": f"Entity {normalized[-4:]}",
            "status": "Active",
            "pan": pan_extracted,
            "state": "Telangana",
            "pincode": "500081",
            "address": f"Survey No. {normalized[-2:]}, Industrial Tech Park, Sector 5, Telangana",
            "registration_date": "2021-05-10",
            "taxpayer_type": "Regular",
            "retrieved_at": datetime.datetime.utcnow().isoformat()
        }

    def verify_udyam(self, udyam_number: str) -> Dict[str, Any]:
        normalized = udyam_number.upper().strip()

        # Check DB
        if self.db:
            record = self.db.query(MockGovRecord).filter(MockGovRecord.udyam_number == normalized).first()
            if record:
                return {
                    "source": "Mock Udyam Registration Portal (Demo / Simulated)",
                    "portal_code": "UDYAM",
                    "is_live_api": False,
                    "disclaimer": "This is simulated demo data for procurement verification testing.",
                    "udyam_number": record.udyam_number,
                    "enterprise_name": record.legal_name,
                    "classification": "Medium Enterprise",
                    "major_activity": "Services",
                    "status": "Active",
                    "state": record.state,
                    "pincode": record.pincode,
                    "retrieved_at": datetime.datetime.utcnow().isoformat()
                }

        return {
            "source": "Mock Udyam Registration Portal (Demo / Simulated)",
            "portal_code": "UDYAM",
            "is_live_api": False,
            "disclaimer": "This is simulated demo data for procurement verification testing.",
            "udyam_number": normalized,
            "enterprise_name": "Verified Micro/Small Enterprise",
            "classification": "Small Enterprise",
            "major_activity": "Trading & Manufacturing",
            "status": "Active",
            "state": "Maharashtra",
            "pincode": "400001",
            "retrieved_at": datetime.datetime.utcnow().isoformat()
        }

    def verify_mca(self, cin: str) -> Dict[str, Any]:
        normalized = cin.upper().strip()

        # Check DB
        if self.db:
            record = self.db.query(MockGovRecord).filter(MockGovRecord.cin == normalized).first()
            if record:
                return {
                    "source": "Mock Ministry of Corporate Affairs MCA21 (Demo / Simulated)",
                    "portal_code": "MCA21",
                    "is_live_api": False,
                    "disclaimer": "This is simulated demo data for procurement verification testing.",
                    "cin": record.cin,
                    "company_name": record.legal_name,
                    "company_status": "Active",
                    "company_class": "Private",
                    "authorized_capital_inr": "50,00,000",
                    "paid_up_capital_inr": "25,00,000",
                    "incorporation_date": record.registration_date or "2020-01-10",
                    "state": record.state,
                    "pincode": record.pincode,
                    "retrieved_at": datetime.datetime.utcnow().isoformat()
                }

        return {
            "source": "Mock Ministry of Corporate Affairs MCA21 (Demo / Simulated)",
            "portal_code": "MCA21",
            "is_live_api": False,
            "disclaimer": "This is simulated demo data for procurement verification testing.",
            "cin": normalized,
            "company_name": "Incorporated Private Limited",
            "company_status": "Active",
            "company_class": "Private",
            "authorized_capital_inr": "1,00,00,000",
            "paid_up_capital_inr": "50,00,000",
            "incorporation_date": "2019-08-20",
            "state": "Delhi",
            "pincode": "110001",
            "retrieved_at": datetime.datetime.utcnow().isoformat()
        }
