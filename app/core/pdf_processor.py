"""
PDF processing module responsible for PDF type detection and text extraction.
Uses pdfplumber to extract text and table data, especially suitable for invoice processing.
"""
import io
import logging
import os
import uuid
from typing import Dict, Any, Optional

import pdfplumber
import pytesseract
from pdfminer.pdfdocument import PDFEncryptionError

from app.exceptions.MyException import PDFProcessingException, BaseExtractionException, PDFPasswordProtectedException, \
    PDFPageExtractionException

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFProcessor:
    """
    PDF processor responsible for detecting PDF type (scanned/digital) and extracting text.
    """

    def __init__(self, tesseract_path: Optional[str] = None, use_vision_api: bool = False):
        """
        Initialize PDF processor。
        
        Args:
            tesseract_path: Tesseract OCR
            use_vision_api: use llm to handle the data
        """
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        self.use_vision_api = use_vision_api

    def process_pdf(self, file_content: bytes) -> Dict[str, Any]:
        """
        Process PDF file, detect type and extract content.
        
        Args:
            file_content: Binary content of the PDF file
            
        Returns:
            Dictionary with the following keys:
            - is_scanned: Whether the PDF is a scanned version
            - text: Extracted text content
            - images: List of image data (base64 encoded) if using vision API
            - page_count: Number of PDF pages
            - tables: Extracted table data
            
        Raises:
            PDFReadException: If the PDF file cannot be read or is corrupted
            PDFPasswordProtectedException: If the PDF file is password protected
            PDFPageExtractionException: If page content cannot be extracted
            PDFProcessingException: For other PDF processing errors
        """
        temp_file_path = None
        try:
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                # Check if PDF is password protected

                # Get total page count
                page_count = len(pdf.pages)

                # Extract text
                text = ""

                for page in pdf.pages:
                    try:
                        # Extract page text
                        page_text = page.extract_text() or ""
                        text += page_text
                    except Exception as page_error:
                        logger.error(f"Error extracting page content: {str(page_error)}")
                        raise PDFPageExtractionException(f"Error on page {page.page_number}: {str(page_error)}")

                # Check if it's a scanned PDF
                is_scanned = self._detect_scanned_pdf(pdf, text)

                # Handle scanned PDF
                images = []
                if is_scanned:
                    temp_file_path = f"{uuid.uuid4()}.pdf"
                    with open(temp_file_path, 'wb') as f:
                        f.write(file_content)
                    # convert to images
                    pdf_images = self._convert_pdf_to_pages(temp_file_path)

                    if self.use_vision_api:
                        # base64
                        images = self._convert_images_to_base64(pdf_images)
                    else:
                        # ocr
                        text = self._process_images_with_ocr(pdf_images)

            result = {
                "is_scanned": is_scanned,
                "text": text,
                "page_count": page_count,
            }

            if self.use_vision_api and images:
                result["images"] = images

            return result
        except Exception as e:
            logger.error(f"PDF processing error: {str(e)}")
            if isinstance(e,PDFEncryptionError):
                raise PDFPasswordProtectedException()
            if isinstance(e, BaseExtractionException):
                raise e
            # Default to general PDFProcessingException for unhandled errors
            raise PDFProcessingException(f"PDF processing error: {str(e)}")
        finally:
            # Clean up temporary file if it exists
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    def _detect_scanned_pdf(self, pdf, extracted_text: str) -> bool:
        """
        Detect if the PDF is a scanned version.

        Enhanced detection logic:
            1. Check text content quality and quantity
            2. Check image coverage ratio

        Args:
            pdf: pdfplumber PDF object
            extracted_text: Extracted text
            
        Returns:
            (is_scanned, confidence) tuple:
            - is_scanned (bool): Whether the PDF is a scanned version
        """
        # Check if there are text
        has_text = len(extracted_text) > 10

        # Check if there are image elements
        for i, page in enumerate(pdf.pages):
            page_area = page.width * page.height
            # If there are images
            total_image_area = 0
            for img in page.images:
                has_images = True
                img_area = img.get('width', 0) * img.get('height', 0)
                total_image_area += img_area
            coverage_ratio = total_image_area / page_area
            if coverage_ratio > 0.5:
                return True

        if not has_text:
            return True

        return False

    def _extract_text_from_digital_pdf(self, pdf_path: str) -> str:
        """
        Extract text from a digital PDF.
        
        Args:
            pdf_path: PDF file path
            
        Returns:
            Extracted text content
        """
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += page_text
        return text

    def _convert_pdf_to_pages(self, pdf_path: str) -> list:
        """
        Convert PDF to a list of PIL Image objects.
        
        Args:
            pdf_path: PDF file path
            
        Returns:
            List of PIL Image objects
        """
        from pdf2image import convert_from_path

        try:
            # Convert PDF pages to PIL images
            pdf_images = convert_from_path(pdf_path)
            return pdf_images
        except Exception as e:
            logger.error(f"Error converting PDF to images: {str(e)}")
            return []

    def _convert_images_to_base64(self, images: list) -> list:
        """
        Convert PIL images to base64 encoded strings for API transmission.
        
        Args:
            images: List of PIL Image objects
            
        Returns:
            List of dictionaries with page number, base64 data and format
        """
        import base64
        from io import BytesIO

        result = []
        try:
            # Convert each image to base64 for API transmission
            for i, img in enumerate(images):
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                result.append({
                    "page": i + 1,
                    "data": img_base64,
                    "format": "PNG"
                })

            return result
        except Exception as e:
            logger.error(f"Error converting images to base64: {str(e)}")
            return []

    def _process_images_with_ocr(self, images: list) -> str:
        """
        Extract text from images using OCR.
        
        Args:
            images: List of PIL Image objects
            
        Returns:
            OCR-extracted text content
        """
        text = ""

        try:
            # Process each page
            for i, image in enumerate(images):
                # Preprocess image for OCR
                img_array = self._preprocess_image_for_ocr(image)

                # Perform OCR to extract text
                try:
                    page_text = pytesseract.image_to_string(
                        img_array,
                        lang='eng',  # Can be changed according to needs
                        config='--psm 6'  # Assume block text
                    )
                    text += page_text
                except Exception as e:
                    logger.error(f"OCR processing error on page {i + 1}: {str(e)}")
                    text += f"\n[OCR Error on Page {i + 1}]\n"
        except Exception as e:
            logger.error(f"OCR processing error: {str(e)}")
            text = "[OCR extraction error]"

        return text

    def _preprocess_image_for_ocr(self, image):
        """
        Preprocess image to improve OCR quality.
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed image
        """
        # Convert to grayscale
        gray = image.convert('L')

        # Can add more preprocessing steps, like binarization, noise reduction, etc.
        # from PIL import ImageOps
        # binary = ImageOps.invert(gray)
        # thresh = 200
        # fn = lambda x : 255 if x > thresh else 0
        # binary = gray.point(fn, mode='1')

        # Return preprocessed image
        return gray
