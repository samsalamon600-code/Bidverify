import os
import io
import logging
import cv2
import numpy as np
from PIL import Image

# Ensure Intel OpenMP multiple runtime conflict does not crash on Windows
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from backend.config import Config

logger = logging.getLogger("bidverify.ocr")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Global singleton EasyOCR Reader instance
_EASYOCR_READER = None


def get_easyocr_reader():
    """
    Returns the singleton EasyOCR Reader instance.
    Initialized once upon first access and reused across all document uploads.
    """
    global _EASYOCR_READER
    if _EASYOCR_READER is None:
        import easyocr

        gpu_enabled = getattr(Config, "OCR_USE_GPU", False)
        languages = getattr(Config, "OCR_LANGUAGES", ["en"])
        logger.info(f"[OCR] Initializing EasyOCR Reader (languages={languages}, gpu={gpu_enabled})...")
        _EASYOCR_READER = easyocr.Reader(languages, gpu=gpu_enabled, verbose=False)
        logger.info("[OCR] EasyOCR Reader successfully initialized and cached.")
    return _EASYOCR_READER


def preprocess_image_for_ocr(img_or_path):
    """
    Lightweight, modular OpenCV preprocessing pipeline for procurement documents:
    1. Read / convert to numpy array
    2. Upscale if low-resolution (width < 800px)
    3. Grayscale conversion
    4. Contrast enhancement using CLAHE (Contrast Limited Adaptive Histogram Equalization)
    5. Light Gaussian noise reduction
    Returns (preprocessed_numpy_img, metadata_dict)
    """
    if isinstance(img_or_path, str):
        if not os.path.exists(img_or_path):
            raise FileNotFoundError(f"Image file not found: {img_or_path}")
        img = cv2.imread(img_or_path)
        if img is None:
            # Fallback attempt via PIL
            pil_img = Image.open(img_or_path).convert("RGB")
            img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    elif isinstance(img_or_path, Image.Image):
        img = cv2.cvtColor(np.array(img_or_path.convert("RGB")), cv2.COLOR_RGB2BGR)
    elif isinstance(img_or_path, np.ndarray):
        img = img_or_path.copy()
    else:
        raise TypeError(f"Unsupported image input type: {type(img_or_path)}")

    orig_h, orig_w = img.shape[:2]

    # 1. Resize low-resolution images
    scale = 1.0
    if orig_w < 800:
        scale = max(1.5, 1200.0 / orig_w)
        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

    # 2. Grayscale conversion
    if len(img.shape) == 3 and img.shape[2] == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img

    # 3. CLAHE for contrast enhancement without washing out text
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # 4. Light Gaussian noise reduction
    denoised = cv2.GaussianBlur(enhanced, (3, 3), 0)

    meta = {
        "original_width": orig_w,
        "original_height": orig_h,
        "processed_width": denoised.shape[1],
        "processed_height": denoised.shape[0],
        "preprocessing_steps": "Resize (if small) + Grayscale + CLAHE Contrast + Gaussian Denoise",
    }
    return denoised, meta


def run_easyocr_on_image(img_or_path) -> tuple[str, list[dict], float]:
    """
    Executes EasyOCR on an image input.
    Returns:
    - combined_text: str (clean multi-line text)
    - items: list[dict] with 'text', 'confidence', 'bbox'
    - avg_confidence: float (0.0 to 1.0)
    """
    reader = get_easyocr_reader()
    processed_img, _ = preprocess_image_for_ocr(img_or_path)

    # EasyOCR readtext returns [(bbox, text, prob), ...]
    raw_results = reader.readtext(processed_img)

    items = []
    text_lines = []
    conf_scores = []

    for item in raw_results:
        try:
            bbox, text, conf = item
            clean_text = str(text).strip()
            if not clean_text:
                continue
            conf_val = round(float(conf), 4)
            # Ensure bbox points are standard serializable python ints
            serializable_bbox = []
            if isinstance(bbox, (list, tuple, np.ndarray)):
                for pt in bbox:
                    serializable_bbox.append([int(pt[0]), int(pt[1])])

            items.append({
                "text": clean_text,
                "confidence": conf_val,
                "bbox": serializable_bbox,
            })
            text_lines.append(clean_text)
            conf_scores.append(conf_val)
        except Exception:
            continue

    combined_text = "\n".join(text_lines)
    avg_conf = round(float(np.mean(conf_scores)), 4) if conf_scores else 0.0
    return combined_text, items, avg_conf


def run_easyocr_on_pdf(pdf_path: str) -> tuple[str, int, float, list[dict], str]:
    """
    Processes a PDF document:
    1. Checks if the PDF contains selectable digital text via pypdf.
       If clear selectable text is found across pages, uses it directly.
    2. If the PDF is scanned or image-based, renders each page to an image via pypdfium2
       (or pypdf image extraction) and runs EasyOCR on each page in sequential order.
    Returns:
    - combined_text: str
    - page_count: int
    - avg_confidence: float
    - ocr_details: list[dict]
    - engine_used: str
    """
    from pypdf import PdfReader

    doc_name = os.path.basename(pdf_path)
    logger.info(f"[OCR] Processing document: {doc_name}")

    # Check for direct digital text first
    selectable_pages = []
    total_pages = 1
    try:
        reader = PdfReader(pdf_path)
        total_pages = max(1, len(reader.pages))
        logger.info(f"[OCR] Pages detected: {total_pages}")

        for idx, page in enumerate(reader.pages, start=1):
            txt = (page.extract_text() or "").strip()
            if txt:
                selectable_pages.append((idx, txt))
    except Exception as e:
        logger.warning(f"[OCR] PdfReader direct text check warning for {doc_name}: {e}")

    # If digital text exists across the PDF (average >= 30 chars per page), use direct text
    if selectable_pages and (sum(len(t[1]) for t in selectable_pages) / total_pages >= 30):
        formatted = [f"[Page {idx}]\n{txt}" for idx, txt in selectable_pages]
        combined = "\n\n".join(formatted)
        logger.info(f"[OCR] Direct digital text detected for {doc_name} ({total_pages} pages).")
        return combined, total_pages, 0.98, [], "PyPDF Direct Text Stream"

    # Otherwise: Scanned / image-based PDF -> Render pages to images and run EasyOCR
    logger.info(f"[OCR] Scanned/Image PDF detected for {doc_name}. Executing EasyOCR on {total_pages} page(s)...")

    rendered_images = []
    # Primary renderer: pypdfium2
    try:
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(pdf_path)
        for i in range(len(pdf)):
            page = pdf[i]
            # Render at 2x scale (approx 144 DPI) for sharp OCR accuracy
            pil_img = page.render(scale=2.0).to_pil()
            rendered_images.append(pil_img)
    except Exception as err:
        logger.warning(f"[OCR] pypdfium2 render fallback due to: {err}")

    # Fallback renderer: PyPDF embedded page image extraction
    if not rendered_images:
        try:
            reader = PdfReader(pdf_path)
            for page in reader.pages:
                for img_obj in page.images:
                    pil_img = Image.open(io.BytesIO(img_obj.data))
                    rendered_images.append(pil_img)
                    break  # take primary page image
        except Exception:
            pass

    if not rendered_images:
        # Check if file is raw text saved with .pdf extension
        try:
            with open(pdf_path, "r", encoding="utf-8", errors="ignore") as f:
                raw_c = f.read()
            if len(raw_c.strip()) > 10 and not raw_c.startswith("%PDF"):
                return raw_c, 1, 0.95, [], "Document Stream (Direct Text)"
        except Exception:
            pass
        raise ValueError(f"Unable to render or extract pages from PDF: {doc_name}")

    page_texts = []
    all_items = []
    all_confs = []

    for idx, page_img in enumerate(rendered_images, start=1):
        logger.info(f"[OCR] Processing page: {idx}")
        p_text, p_items, p_conf = run_easyocr_on_image(page_img)

        for item in p_items:
            item["page"] = idx
            all_items.append(item)
            all_confs.append(item["confidence"])

        page_texts.append(f"[Page {idx}]\n{p_text}")

    combined_text = "\n\n".join(page_texts)
    overall_conf = round(float(np.mean(all_confs)), 4) if all_confs else 0.0
    logger.info(f"[OCR] OCR completed with EasyOCR (Confidence: {overall_conf:.1%})")
    logger.info("[OCR] Text extraction completed")

    return combined_text, len(rendered_images), overall_conf, all_items, "EasyOCR"


def extract_text_from_file_easyocr(
    file_path: str,
    original_filename: str = "",
    declared_doc_type: str = ""
) -> tuple[str, str, int, float, list[dict], str]:
    """
    Unified entry point for document OCR text extraction using EasyOCR.
    Supports:
    - PDF (.pdf)
    - Images (.png, .jpg, .jpeg, .bmp, .tiff, .webp)
    - Text files (.txt, .md, .csv)
    Returns:
    (raw_text, engine_used, page_count, ocr_confidence, ocr_details, status)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Document file not found: {file_path}")

    filename = original_filename or os.path.basename(file_path)
    ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""

    # 1. Plain text / CSV files
    if ext in ("txt", "md", "csv", "json"):
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        if not text.strip():
            raise ValueError("OCR_EMPTY_DOCUMENT: Document contains no readable text.")
        logger.info(f"[OCR] Processing document: {filename} (Direct Text Stream)")
        logger.info("[OCR] Text extraction completed")
        return text, "Direct Text Stream", 1, 0.99, [], "PROCESSED"

    # 2. PDF Documents
    if ext == "pdf":
        raw_text, page_count, conf, details, engine = run_easyocr_on_pdf(file_path)
        if not raw_text.strip():
            raise ValueError(f"Unable to extract readable text from PDF '{filename}'. Please verify document quality.")
        return raw_text, engine, page_count, conf, details, "PROCESSED"

    # 3. Image Files (PNG, JPG, JPEG, BMP, etc.)
    if ext in ("png", "jpg", "jpeg", "bmp", "tiff", "webp"):
        logger.info(f"[OCR] Processing document: {filename} (Image File)")
        logger.info("[OCR] Pages detected: 1")
        logger.info("[OCR] Processing page: 1")
        raw_text, items, conf = run_easyocr_on_image(file_path)
        if not raw_text.strip():
            raise ValueError(f"No readable text detected in image '{filename}' by EasyOCR.")
        logger.info(f"[OCR] OCR completed with EasyOCR (Confidence: {conf:.1%})")
        logger.info("[OCR] Text extraction completed")
        return raw_text, "EasyOCR", 1, conf, items, "PROCESSED"

    # 4. Office documents or fallback
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            raw_text = f.read()
        if raw_text.strip():
            return raw_text, "Document Text Stream", 1, 0.95, [], "PROCESSED"
    except Exception:
        pass

    raise ValueError(f"Unsupported file format '.{ext}' for EasyOCR extraction: {filename}")
