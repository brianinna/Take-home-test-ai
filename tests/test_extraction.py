"""
Unit tests for the extraction service
"""
import os
import pytest
import unittest.mock as mock
from pathlib import Path
from app.core.extraction import ExtractionService
from app.core.pdf_processor import PDFProcessor
from app.core.llm_service import LLMService

class TestExtractionService:
    """Test extraction service functionality"""

    @pytest.fixture
    def extraction_service(self):
        """Create extraction service instance, using mocks instead of real dependent services"""
        # Create mocks for PDF processor and LLM service
        mock_pdf_processor = mock.MagicMock(spec=PDFProcessor)
        mock_llm_service = mock.MagicMock(spec=LLMService)
        
        # Configure mock return values
        mock_pdf_processor.process_pdf.return_value = {
            "is_scanned": False,
            "text": "Invoice #12345\nDate: 2023-01-01\nVendor: ABC Company\nAmount: $100.00",
            "confidence": 0.9,
            "page_count": 1,
            "tables": []
        }
        
        mock_llm_service.extract_invoice_data.return_value = {
            "invoice_number": "12345",
            "invoice_date": "2023-01-01",
            "vendor_name": "ABC Company",
            "total_amount": 100.00
        }
        
        # Create extraction service instance
        return ExtractionService(pdf_processor=mock_pdf_processor, llm_service=mock_llm_service)
    
    def test_init(self, extraction_service):
        """Test extraction service initialization"""
        assert extraction_service is not None
        assert extraction_service.pdf_processor is not None
        assert extraction_service.llm_service is not None
    
    def test_process_invoice_file(self, extraction_service, digital_invoice_path):
        """Test processing single invoice file"""
        result = extraction_service.process_invoice_file(digital_invoice_path)
        
        # Verify results
        assert isinstance(result, dict)
        assert result.get("invoice_number") == "12345"
        assert result.get("invoice_date") == "2023-01-01"
        assert result.get("vendor_name") == "ABC Company"
        assert result.get("total_amount") == 100.00
        assert result.get("metadata", {}).get("is_scanned") is False
        assert result.get("metadata", {}).get("confidence") == 0.9
    
    def test_process_invoice_content(self, extraction_service):
        """Test processing invoice file content"""
        with open(Path(__file__).parent.parent / "Sample Invoices" / "invoice1.pdf", "rb") as f:
            file_content = f.read()
            
        result = extraction_service.process_invoice_content(file_content)
        
        # Verify results
        assert isinstance(result, dict)
        assert result.get("invoice_number") == "12345"
        assert result.get("invoice_date") == "2023-01-01"
        assert result.get("vendor_name") == "ABC Company"
        assert result.get("total_amount") == 100.00
        assert result.get("metadata", {}).get("is_scanned") is False
        assert result.get("metadata", {}).get("confidence") == 0.9

    @pytest.mark.parametrize("file_name", [
        "invoice1.pdf", "invoice2.pdf", "invoice3.pdf", "invoice4.pdf", "invoice5.pdf"
    ])
    def test_extraction_service_with_real_files(self, file_name):
        """Test extraction service integration with real files"""
        # This test uses actual service instances, not mocks
        # Create real service instances
        pdf_processor = PDFProcessor()
        llm_service = mock.MagicMock(spec=LLMService)
        
        # Configure mock LLM service
        llm_service.extract_invoice_data.return_value = {
            "invoice_number": f"test-{file_name}",
            "invoice_date": "2023-01-01",
            "vendor_name": "Test Company",
            "total_amount": 100.00
        }
        
        extraction_service = ExtractionService(pdf_processor=pdf_processor, llm_service=llm_service)
        
        # Get file path
        file_path = Path(__file__).parent.parent / "Sample Invoices" / file_name
        
        # Test if file exists
        if not file_path.exists():
            pytest.skip(f"Test file does not exist: {file_path}")
            
        try:
            result = extraction_service.process_invoice_file(file_path)
            
            # Verify PDF processing was successful
            assert result is not None
            assert "metadata" in result
            assert "text" in result["metadata"]
            assert len(result["metadata"]["text"]) > 0
            
        except Exception as e:
            pytest.fail(f"Error processing file {file_path}: {str(e)}")
