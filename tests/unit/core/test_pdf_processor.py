# Import necessary libraries and modules
from unittest.mock import MagicMock, patch

import pytest

from app.core.pdf_processor import PDFProcessor
from app.exceptions.MyException import (
    PDFProcessingException
)


# Mark this test class as a unit test
@pytest.mark.unit
class TestPDFProcessor:
    """Unit tests for the PDFProcessor class

    This class contains methods to test various functionalities of PDFProcessor, mainly testing:
    1. PDF type detection (scanned/digital)
    2. Text extraction functionality
    3. OCR processing functionality
    4. Error handling
    """

    def test_init(self):
        """Test PDFProcessor initialization"""
        # Case where tesseract path is not specified
        processor = PDFProcessor()
        assert not processor.use_vision_api

        # Case where tesseract path is specified
        with patch('pytesseract.pytesseract') as mock_pytesseract:
            processor = PDFProcessor(tesseract_path="/path/to/tesseract")
            assert mock_pytesseract.tesseract_cmd == "/path/to/tesseract"

        # Case where vision API is enabled
        processor = PDFProcessor(use_vision_api=True)
        assert processor.use_vision_api

    def test_process_pdf_digital(self, sample_pdf_content, mock_pdfplumber):
        """Test processing a digital PDF file"""
        processor = PDFProcessor()

        # Mock the PDF as not scanned
        with patch.object(processor, '_detect_scanned_pdf', return_value=False):
            # Call the process_pdf method to handle sample PDF content
            result = processor.process_pdf(sample_pdf_content)

            # Validate the returned result
            assert result['is_scanned'] == False
            assert "ACME Corporation" in result['text']
            assert "Total Amount Due: $120.00" in result['text']
            assert result['page_count'] == 1

    def test_process_pdf_scanned(self, sample_pdf_content, mock_pdfplumber, mock_pytesseract):
        """Test processing a scanned PDF file (using OCR)"""
        processor = PDFProcessor()

        # Mock the PDF as scanned
        with patch.object(processor, '_detect_scanned_pdf', return_value=True):
            # Mock the method for converting PDF to images
            with patch.object(processor, '_convert_pdf_to_pages') as mock_convert:
                # Create a mock list of images
                mock_images = [MagicMock(), MagicMock()]
                mock_convert.return_value = mock_images

                # Call the process_pdf method to handle sample PDF content
                result = processor.process_pdf(sample_pdf_content)

                # Validate the result
                assert result['is_scanned'] == True
                assert "Invoice: INV-12345" in result['text']
                assert result['page_count'] == 1

    def test_process_pdf_scanned_with_vision_api(self, sample_pdf_content, mock_pdfplumber):
        """Test processing a scanned PDF with the Vision API"""
        processor = PDFProcessor(use_vision_api=True)

        # Mock the PDF as scanned
        with patch.object(processor, '_detect_scanned_pdf', return_value=True):
            # Mock the method for converting PDF to images
            with patch.object(processor, '_convert_pdf_to_pages') as mock_convert:
                # Create a mock list of images
                mock_images = [MagicMock(), MagicMock()]
                mock_convert.return_value = mock_images

                # Mock the method for converting images to base64
                with patch.object(processor, '_convert_images_to_base64') as mock_convert_base64:
                    mock_base64_images = [
                        {"page": 1, "data": "base64data1", "format": "PNG"},
                        {"page": 2, "data": "base64data2", "format": "PNG"}
                    ]
                    mock_convert_base64.return_value = mock_base64_images

                    # Call the process_pdf method to handle sample PDF content
                    result = processor.process_pdf(sample_pdf_content)

                    # Validate the result
                    assert result['is_scanned'] == True
                    assert result['page_count'] == 1
                    assert result['images'] == mock_base64_images

    def test_detect_scanned_pdf(self, mock_pdfplumber):
        """Test PDF type detection (scanned/digital)"""
        processor = PDFProcessor()

        # Open the mock PDF file
        # Set extracted text to empty to simulate a scanned PDF
        is_scanned = processor._detect_scanned_pdf(mock_pdfplumber, "")
        assert is_scanned == True

        # Set extracted text to non-empty to simulate a digital PDF
        is_scanned = processor._detect_scanned_pdf(mock_pdfplumber, "This is some text content")
        assert is_scanned == False

    def test_convert_images_to_base64(self, sample_image):
        """Test converting images to base64 encoding"""
        processor = PDFProcessor()

        # Create a list of images
        images = [sample_image, sample_image]

        # Call the conversion method
        result = processor._convert_images_to_base64(images)

        # Validate the result
        assert len(result) == 2
        assert all(item.get('page') for item in result)
        assert all(item.get('data') for item in result)
        assert all(item.get('format') == 'PNG' for item in result)

    def test_process_images_with_ocr(self, sample_image, mock_pytesseract):
        """Test processing images with OCR"""
        processor = PDFProcessor()

        # Mock the image preprocessing method
        with patch.object(processor, '_preprocess_image_for_ocr', return_value=sample_image):
            # Create a list of images
            images = [sample_image, sample_image]

            # Call the OCR processing method
            result = processor._process_images_with_ocr(images)

            # Validate the result
            assert "Invoice: INV-12345" in result
            assert mock_pytesseract.call_count == 2

    def test_preprocess_image_for_ocr(self, sample_image):
        """Test image preprocessing before OCR"""
        processor = PDFProcessor()

        # Call the preprocessing method
        result = processor._preprocess_image_for_ocr(sample_image)

        # Validate the result is a grayscale image
        assert result.mode == 'L'

    def test_pdf_password_protected_exception(self):
        """Test exception when processing a password-protected PDF"""
        processor = PDFProcessor()

        # Mock pdfplumber.open to raise PDFEncryptionError
        with patch('pdfplumber.open', side_effect=Exception("file has not been decrypted")):
            with pytest.raises(PDFProcessingException):
                processor.process_pdf(b'dummy_content')
