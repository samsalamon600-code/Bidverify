import os
import logging
from backend.ocr.easyocr_engine import (
    extract_text_from_file_easyocr,
    run_easyocr_on_image,
    run_easyocr_on_pdf,
    preprocess_image_for_ocr,
    get_easyocr_reader,
)

logger = logging.getLogger("bidverify.ocr")


def extract_text_from_file(file_path: str, original_filename: str = "", declared_doc_type: str = ""):
    """
    Primary OCR & text extraction function using EasyOCR.
    Maintains backward compatibility with (raw_text, engine_used, page_count, status) signature.
    """
    raw_text, engine, page_count, conf, details, status = extract_text_from_file_easyocr(
        file_path=file_path,
        original_filename=original_filename,
        declared_doc_type=declared_doc_type,
    )
    return raw_text, engine, page_count, status


def extract_text_with_details(file_path: str, original_filename: str = "", declared_doc_type: str = ""):
    """
    Extended OCR text extraction returning full details:
    (raw_text, engine_used, page_count, ocr_confidence, ocr_details, status)
    """
    return extract_text_from_file_easyocr(
        file_path=file_path,
        original_filename=original_filename,
        declared_doc_type=declared_doc_type,
    )
