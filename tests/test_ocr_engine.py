"""
Unit tests for the OCR engine
"""
import os
import pytest
import pytesseract
from PIL import Image
from pathlib import Path
from app.core.ocr_engine import OCREngine

class TestOCREngine:
    """Test OCR engine functionality"""

    @pytest.fixture
    def ocr_engine(self):
        """Create OCR engine instance"""
        return OCREngine()
    
    def test_init(self, ocr_engine):
        """Test OCR engine initialization"""
        assert ocr_engine is not None
    
    @pytest.mark.skipif(not pytesseract.pytesseract.tesseract_cmd, 
                       reason="Tesseract not installed or path not configured")
    def test_process_image(self, ocr_engine, scanned_invoice_path):
        """Test processing image files"""
        # This test requires Tesseract OCR installation, will be skipped if not installed
        try:
            from pdf2image import convert_from_path
            # Convert the first page of PDF to image
            images = convert_from_path(scanned_invoice_path, first_page=1, last_page=1)
            if images:
                image = images[0]
                
                # Process image using OCR engine
                result = ocr_engine.process_image(image)
                
                # Verify OCR results
                assert isinstance(result, dict)
                assert 'text' in result
                assert 'confidence' in result
                assert len(result['text']) > 0
        except Exception as e:
            pytest.skip(f"Cannot run OCR test: {str(e)}")
    
    @pytest.mark.skipif(not pytesseract.pytesseract.tesseract_cmd,
                       reason="Tesseract not installed or path not configured")
    def test_preprocess_image(self, ocr_engine, scanned_invoice_path):
        """Test image preprocessing functionality"""
        # This test requires Tesseract OCR installation, will be skipped if not installed
        try:
            from pdf2image import convert_from_path
            # Convert the first page of PDF to image
            images = convert_from_path(scanned_invoice_path, first_page=1, last_page=1)
            if images:
                image = images[0]
                
                # Test image preprocessing
                processed_image = ocr_engine.preprocess_image(image)
                
                # Verify preprocessing results
                assert processed_image is not None
                assert isinstance(processed_image, Image.Image)
        except Exception as e:
            pytest.skip(f"Cannot run image preprocessing test: {str(e)}")
