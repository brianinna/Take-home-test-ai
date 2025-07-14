"""
PDF processing module responsible for PDF type detection and text extraction.
Uses pdfplumber to extract text and table data, especially suitable for invoice processing.
"""
import io
import os
import pytesseract
import pdfplumber
from pathlib import Path
from typing import Tuple, Dict, Any, List, Optional
import logging
from PIL import Image

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFProcessor:
    """
    PDF processor responsible for detecting PDF type (scanned/digital) and extracting text.
    """
    
    def __init__(self, tesseract_path: Optional[str] = None):
        """
        Initialize PDF processor。
        
        Args:
            tesseract_path: Tesseract OCR引擎的安装路径（可选）
        """
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
    
    def process_pdf(self, file_content: bytes) -> Dict[str, Any]:
        """
        Process PDF file, detect type and extract content.
        
        Args:
            file_content: Binary content of the PDF file
            
        Returns:
            Dictionary with the following keys:
            - is_scanned: Whether the PDF is a scanned version
            - text: Extracted text content
            - confidence: Confidence level of text extraction
            - page_count: Number of PDF pages
            - tables: Extracted table data
        """
        try:
            # Load byte content as file object
            temp_file_path = "temp_pdf_file.pdf"
            with open(temp_file_path, 'wb') as f:
                f.write(file_content)
            
            # Open PDF
            with pdfplumber.open(temp_file_path) as pdf:
                # Get total page count
                page_count = len(pdf.pages)
                
                # Otherwise extract text
                text = ""
                tables = []
                
                for page in pdf.pages:
                    # Extract page text
                    page_text = page.extract_text() or ""
                    text += page_text
                    text += "\n--- Page Break ---\n"
                    
                    # Try to extract tables
                    try:
                        page_tables = page.extract_tables()
                        if page_tables:
                            tables.extend(page_tables)
                    except Exception as e:
                        logger.warning(f"Table extraction error: {str(e)}")
                
                # Check if it's a scanned PDF
                is_scanned, confidence = self._detect_scanned_pdf(pdf, text)
                
                # Handle scanned PDF
                if is_scanned:
                    text = self._extract_text_from_scanned_pdf(temp_file_path)
            
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            
            return {
                "is_scanned": is_scanned,
                "text": text,
                "confidence": confidence,
                "page_count": page_count,
                "tables": tables
            }
        
        except Exception as e:
            logger.error(f"PDF processing error: {str(e)}")
            # Ensure cleaning up temporary file
            if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            raise
    
    def _detect_scanned_pdf(self, pdf, extracted_text: str) -> Tuple[bool, float]:
        """
        Detect if the PDF is a scanned version.
        
        Basic idea:
        1. Check the extracted text content
        2. Check the text length and quality
        3. If the text is short or of poor quality, it might be a scanned PDF
        
        Args:
            pdf: pdfplumber PDF object
            extracted_text: Extracted text
            
        Returns:
            (is_scanned, confidence) tuple:
            - is_scanned (bool): Whether the PDF is a scanned version
            - confidence (float): Confidence level of the detection
        """
        total_text_length = len(extracted_text)
        text_quality_score = 0
        
        # Simple quality check: calculate character/word ratio
        if total_text_length > 0:
            words = extracted_text.split()
            if words:
                avg_word_length = total_text_length / len(words)
                if 3 <= avg_word_length <= 10:  # Normal text word length range
                    text_quality_score = 1
        
        # Check if there are image elements
        has_images = False
        
        # Check the first 3 pages for image objects
        for i, page in enumerate(pdf.pages):
            if i >= 3:  # Only check the first three pages
                break
                
            # If there are images
            if page.images:
                has_images = True
                break
        
        # Make a judgment based on text length, quality, and image presence
        is_scanned = (total_text_length < 100) or (text_quality_score == 0 and has_images)
        
        # Calculate confidence level (simple version)
        if total_text_length < 10 and has_images:
            confidence = 0.95  # Almost no text and images, likely a scanned PDF
        elif total_text_length < 100:
            confidence = 0.8  # Short text, possibly a scanned PDF
        elif text_quality_score == 0 and has_images:
            confidence = 0.7  # Poor text quality and images, possibly a scanned PDF but some content recognized
        else:
            confidence = 0.9  # Enough high-quality text, possibly a digital PDF
            
        return is_scanned, confidence
    
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
                text += "\n--- Page Break ---\n"
        return text
    
    def _extract_text_from_scanned_pdf(self, pdf_path: str) -> str:
        """
        Extract text from a scanned PDF using OCR.
        
        Args:
            pdf_path: PDF file path
            
        Returns:
            OCR-extracted text content
        """
        from pdf2image import convert_from_path
        
        text = ""
        tables = []
        
        try:
            # First, try to extract text and tables using pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                # Try to extract tables (even if it's a scanned PDF, there might be structured tables)
                for page in pdf.pages:
                    try:
                        page_tables = page.extract_tables()
                        if page_tables:
                            tables.extend(page_tables)
                    except Exception:
                        pass
            
            # Convert PDF to images and perform OCR
            images = convert_from_path(pdf_path)
            
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
                    text += "\n--- Page Break ---\n"
                except Exception as e:
                    logger.error(f"OCR processing error on page {i+1}: {str(e)}")
                    text += f"\n[OCR Error on Page {i+1}]\n"
        except Exception as e:
            logger.error(f"Error converting PDF to image: {str(e)}")
            # If conversion fails, try to extract text using pdfplumber
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text() or ""
                        text += page_text
                        text += "\n--- Page Break ---\n"
            except Exception:
                text = "[PDF extraction error]"
            
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
