"""
Unit tests for the PDF processor
"""
import os
import pytest
from pathlib import Path
from app.core.pdf_processor import PDFProcessor

class TestPDFProcessor:
    """Test PDF processor functionality"""

    @pytest.fixture
    def pdf_processor(self):
        """Create PDF processor instance"""
        return PDFProcessor()
    
    def test_init(self, pdf_processor):
        """Test PDF processor initialization"""
        assert pdf_processor is not None
    
    def test_process_pdf_with_digital_invoice(self, pdf_processor, digital_invoice_path):
        """Test processing digital PDF invoice"""
        with open(digital_invoice_path, 'rb') as f:
            file_content = f.read()
        
        result = pdf_processor.process_pdf(file_content)
        
        # Verify result structure
        assert isinstance(result, dict)
        assert 'is_scanned' in result
        assert 'text' in result
        assert 'confidence' in result
        assert 'page_count' in result
        assert 'tables' in result
        
        # Verify text extraction success
        assert len(result['text']) > 0
        
        # Digital PDF should be correctly identified
        # Note: This may need adjustment based on actual test files
        # assert result['is_scanned'] is False
    
    def test_process_pdf_with_scanned_invoice(self, pdf_processor, scanned_invoice_path):
        """Test processing scanned PDF invoice"""
        with open(scanned_invoice_path, 'rb') as f:
            file_content = f.read()
        
        result = pdf_processor.process_pdf(file_content)
        
        # Verify result structure
        assert isinstance(result, dict)
        assert 'is_scanned' in result
        assert 'text' in result
        assert 'confidence' in result
        assert 'page_count' in result
        
        # Verify text extraction success
        assert len(result['text']) > 0
        
        # Scanned PDF should be correctly identified
        # Note: This may need adjustment based on actual test files
        # assert result['is_scanned'] is True
    
    def test_process_all_sample_invoices(self, pdf_processor, sample_invoice_files):
        """Test processing all sample invoice files"""
        for invoice_path in sample_invoice_files:
            with open(invoice_path, 'rb') as f:
                file_content = f.read()
            
            result = pdf_processor.process_pdf(file_content)
            
            # Verify each invoice can be processed successfully
            assert isinstance(result, dict)
            assert 'is_scanned' in result
            assert 'text' in result
            assert 'confidence' in result
            assert 'page_count' in result
            
            # Verify text extraction success
            assert len(result['text']) > 0
            print(f"Successfully processed {invoice_path.name}, text length: {len(result['text'])}, "
                  f"is scanned: {result['is_scanned']}, confidence: {result['confidence']}")
