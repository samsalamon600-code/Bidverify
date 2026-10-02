import json
from backend.config import Config
from backend.extensions import db
from backend.models.models import Document, DocumentExtraction, BidItem
from backend.ocr.ocr_engine import extract_text_with_details
from backend.document_processing.classifier import classify_document
from backend.document_processing.extractor import extract_structured_information


def process_document_pipeline(document: Document, commit: bool = True):
    """
    Executes the end-to-end document processing pipeline:
    1. OCR / Text Extraction (OpenCV + EasyOCR / Direct PDF Stream)
    2. Document Identification (Regex + RapidFuzz + Keyword Classification)
    3. Structured Information & Entity Extraction with Field Confidence (Regex + spaCy + RapidFuzz)
    4. Persist DocumentExtraction (with raw text, structured data, entities & OCR bounding boxes)
    5. Sync BidItems if Technical Bid
    """
    try:
        raw_text, engine_used, page_count, ocr_conf, ocr_details, status = extract_text_with_details(
            document.file_path,
            original_filename=document.original_filename,
            declared_doc_type=document.declared_doc_type or "",
        )

        detected_type, class_conf = classify_document(
            raw_text,
            filename=document.original_filename,
            declared_type=document.declared_doc_type or "",
        )

        structured_data, entities, ext_conf = extract_structured_information(
            raw_text, detected_type, ocr_details=ocr_details
        )

        # Confidence Handling: Flag for Human Review if OCR confidence is below threshold
        threshold = getattr(Config, "OCR_CONFIDENCE_THRESHOLD", 0.60)
        is_low_conf = (ocr_conf < threshold) and (engine_used == "EasyOCR")
        if is_low_conf:
            structured_data["low_ocr_confidence"] = True
            structured_data["review_reason"] = (
                f"LOW OCR CONFIDENCE ({ocr_conf * 100:.1f}% < {threshold * 100:.1f}%) "
                "-> Flagged for Human Review by Procurement Officer."
            )

        document.detected_doc_type = detected_type
        document.classification_confidence = class_conf
        document.ocr_engine_used = engine_used
        document.ocr_confidence = ocr_conf
        document.page_count = page_count
        document.processing_status = status

        # Remove old extractions for idempotency
        DocumentExtraction.query.filter_by(document_id=document.id).delete()

        extraction = DocumentExtraction(
            document_id=document.id,
            raw_text=raw_text,
            structured_data_json=json.dumps(structured_data),
            entities_json=json.dumps(entities),
            extraction_confidence=ext_conf,
            ocr_details_json=json.dumps(ocr_details) if ocr_details else None,
        )
        db.session.add(extraction)

        # If document belongs to a bid and contains technical_specifications, sync BidItems
        if document.bid_id and "technical_specifications" in structured_data:
            for param_name, spec_info in structured_data["technical_specifications"].items():
                existing_item = BidItem.query.filter_by(
                    bid_id=document.bid_id, parameter_name=param_name
                ).first()
                if not existing_item:
                    item = BidItem(
                        bid_id=document.bid_id,
                        item_category="TECHNICAL",
                        parameter_name=param_name,
                        submitted_value=str(spec_info.get("value", "")),
                        unit=spec_info.get("unit", ""),
                        source_document=document.original_filename,
                        source_page=int(spec_info.get("page", 1)),
                    )
                    db.session.add(item)

        if commit:
            db.session.commit()

        return {
            "success": True,
            "document": document.to_dict(include_extraction=True),
        }

    except Exception as exc:
        document.processing_status = "FAILED"
        if commit:
            db.session.commit()
        return {
            "success": False,
            "error": str(exc),
            "error_code": "OCR_PROCESSING_FAILURE",
        }
