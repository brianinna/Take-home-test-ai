"""
Integration testing - testing the complete invoice extraction process
"""
import os
import pytest
import unittest.mock as mock
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.core.extraction import ExtractionService
from app.core.pdf_processor import PDFProcessor
from app.core.llm_service import LLMService

class TestIntegration:
    """End-to-end integration testing"""

    @pytest.fixture
    def test_client(self):
        """Create test client"""
        return TestClient(app)
    
    @mock.patch.dict(os.environ, {"OPENAI_API_KEY": "mock-api-key"})
    @mock.patch("app.core.llm_service.openai.chat.completions.create")
    def test_end_to_end_extraction(self, mock_openai_create, test_client, sample_invoice_files):
        """Test end-to-end invoice extraction process"""
        if not sample_invoice_files:
            pytest.skip("No sample invoice files found")
        
        # Set up mock response for OpenAI call
        mock_response = mock.MagicMock()
        mock_response.choices[0].message.content = """
        {
            "invoice_number": "test-12345",
            "invoice_date": "2023-01-01",
            "vendor_name": "Test Vendor Inc.",
            "total_amount": 123.45
        }
        """
        mock_openai_create.return_value = mock_response
        
        # Test each sample invoice
        for invoice_path in sample_invoice_files[:1]:  # Limit to one file to speed up testing
            if not invoice_path.exists():
                continue
                
            # Send request to API
            with open(invoice_path, "rb") as f:
                response = test_client.post(
                    "/extract",
                    files={"file": (invoice_path.name, f, "application/pdf")}
                )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            
            # Verify basic structure
            assert "success" in data
            assert data["success"] is True
            assert "invoice_number" in data
            assert "invoice_date" in data
            assert "vendor_name" in data
            assert "total_amount" in data
            assert "metadata" in data
            
            # Verify metadata
            metadata = data["metadata"]
            assert "confidence" in metadata
            assert "processing_time" in metadata
            
            # Verify OpenAI was called
            mock_openai_create.assert_called()

    def test_pdf_processor_with_real_files(self, sample_invoice_files):
        """Test PDF processor with real files"""
        if not sample_invoice_files:
            pytest.skip("No sample invoice files found")
            
        pdf_processor = PDFProcessor()
        
        # Test each invoice file
        for invoice_path in sample_invoice_files:
            if not invoice_path.exists():
                continue
                
            # Read file content
            with open(invoice_path, "rb") as f:
                file_content = f.read()
                
            # Process PDF
            try:
                result = pdf_processor.process_pdf(file_content)
                
                # Verify results
                assert isinstance(result, dict)
                assert "is_scanned" in result
                assert "text" in result
                assert "confidence" in result
                assert "page_count" in result
                assert "tables" in result
                
                # Ensure text was extracted
                assert len(result["text"]) > 0
                
                # Output brief result information
                print(f"Processing {invoice_path.name}: "
                       f"Pages={result['page_count']}, "
                       f"Is Scanned={result['is_scanned']}, "
                       f"Confidence={result['confidence']:.2f}, "
                       f"Text Length={len(result['text'])}")
                      
            except Exception as e:
                pytest.fail(f"Failed to process {invoice_path.name}: {str(e)}")
