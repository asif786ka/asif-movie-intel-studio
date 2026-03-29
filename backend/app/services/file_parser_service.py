import io
from typing import Optional
from app.core.logging import get_logger

logger = get_logger(__name__)


def extract_text_from_pdf(content: bytes) -> str:
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(io.BytesIO(content))
        pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                pages.append(f"[Page {i + 1}]\n{text.strip()}")
        if not pages:
            return ""
        return "\n\n".join(pages)
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return ""


def extract_text_from_image(content: bytes, filename: str) -> str:
    try:
        import pytesseract
        from PIL import Image
        image = Image.open(io.BytesIO(content))
        text = pytesseract.image_to_string(image)
        if text and text.strip():
            return text.strip()
    except Exception as e:
        logger.warning(f"Tesseract OCR not available: {e}")

    try:
        from PIL import Image
        image = Image.open(io.BytesIO(content))
        width, height = image.size
        mode = image.mode
        format_name = image.format or filename.rsplit(".", 1)[-1].upper()
        description = f"Image file: {filename}\nFormat: {format_name}\nDimensions: {width}x{height}\nMode: {mode}"

        if hasattr(image, "text") and image.text:
            for key, value in image.text.items():
                description += f"\n{key}: {value}"

        info = image.info or {}
        if "exif" in info or "comment" in info:
            if "comment" in info:
                comment = info["comment"]
                if isinstance(comment, bytes):
                    comment = comment.decode("utf-8", errors="replace")
                description += f"\nComment: {comment}"

        return description
    except Exception as e:
        logger.error(f"Image processing failed: {e}")
        return f"Image file: {filename} (could not extract text content)"


def extract_text_from_file(content: bytes, filename: str) -> Optional[str]:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext in ("txt", "md"):
        return content.decode("utf-8", errors="replace")

    if ext == "pdf":
        text = extract_text_from_pdf(content)
        if not text:
            return None
        return text

    if ext in ("png", "jpg", "jpeg"):
        text = extract_text_from_image(content, filename)
        if not text:
            return None
        return text

    return None
