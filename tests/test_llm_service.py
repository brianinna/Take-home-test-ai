"""
Unit tests for the LLM service
"""
import os
import pytest
import unittest.mock as mock
from app.core.llm_service import LLMService

class TestLLMService:
    """Test LLM service functionality"""

    @pytest.fixture
    def llm_service(self):
        """Create LLM service instance, using mock instead of real API calls"""
        service = LLMService()
        # Mock environment variables
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "mock-api-key"}):
            yield service
    
    def test_init(self, llm_service):
        """Test LLM service initialization"""
        assert llm_service is not None
    
    def test_build_prompt(self, llm_service):
        """Test prompt building functionality"""
        # Prepare test data
        invoice_text = "Invoice #12345\nDate: 2023-01-01\nVendor: ABC Company\nAmount: $100.00"
        
        # Build prompt
        prompt = llm_service.build_prompt(invoice_text)
        
        # Verify prompt contains necessary information
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "Invoice #12345" in prompt
        assert "extracting data" in prompt.lower() or "extraction" in prompt.lower()
    
    @mock.patch("app.core.llm_service.openai.chat.completions.create")
    def test_extract_invoice_data_with_mock(self, mock_openai_create, llm_service):
        """Test invoice data extraction functionality using mock"""
        # Prepare test data
        invoice_text = "Invoice #12345\nDate: 2023-01-01\nVendor: ABC Company\nAmount: $100.00"
        
        # Set up mock response
        mock_response = mock.MagicMock()
        mock_response.choices[0].message.content = """
        {
            "invoice_number": "12345",
            "invoice_date": "2023-01-01",
            "vendor_name": "ABC Company",
            "total_amount": 100.00
        }
        """
        mock_openai_create.return_value = mock_response
        
        # Call extraction method
        result = llm_service.extract_invoice_data(invoice_text)
        
        # Verify results
        assert isinstance(result, dict)
        assert result.get("invoice_number") == "12345"
        assert result.get("invoice_date") == "2023-01-01"
        assert result.get("vendor_name") == "ABC Company"
        assert result.get("total_amount") == 100.00
        
        # Verify mock was called correctly
        mock_openai_create.assert_called_once()
    
    @mock.patch("app.core.llm_service.openai.chat.completions.create")
    def test_validate_response(self, mock_openai_create, llm_service):
        """Test LLM response validation functionality"""
        # Prepare test data - valid response
        valid_response = """
        {
            "invoice_number": "12345",
            "invoice_date": "2023-01-01",
            "vendor_name": "ABC Company",
            "total_amount": 100.00
        }
        """
        
        # Invalid response - missing required fields
        invalid_response = """
        {
            "invoice_number": "12345",
            "vendor_name": "ABC Company"
        }
        """
        
        # Test valid response
        valid_result = llm_service.validate_llm_response(valid_response)
        assert valid_result is not None
        assert valid_result.get("invoice_number") == "12345"
        
        # Test invalid response
        with pytest.raises(ValueError):
            llm_service.validate_llm_response(invalid_response)
