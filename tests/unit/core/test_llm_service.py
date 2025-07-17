from datetime import date
import json
from decimal import Decimal

import pytest
from unittest.mock import MagicMock, patch, ANY

from app.core.llm_service import LLMService
from app.exceptions.MyException import (
    LLMInitializeException, 
    LLMProcessingException, 
    LLMResponseParsingException
)
from app.models.schemas import ExtractionData, InvoiceDataExtended
from config.config import settings


@pytest.mark.unit
class TestLLMService:
    """Unit test class for Large Language Model Service

    Tests various functions of the LLMService class, including:
    1. Initialization and client creation
    2. Invoice data extraction function
    3. Result validation and cleaning function
    4. Error handling capability
    """
    
    def test_init(self):
        """Test LLMService initialization"""
        with patch('app.core.llm_service.OpenAI') as mock_openai:
            service = LLMService()
            
            # Verify text model client creation
            assert service.text_client is not None
            assert mock_openai.call_count >= 1
            
            # Verify temperature setting
            assert service.temperature == settings.LLM_TEMPERATURE
    
    def test_create_client(self):
        """Test client creation functionality"""
        with patch('app.core.llm_service.OpenAI') as mock_openai:
            service = LLMService()
            
            # Call the method to create a text model client
            client = service._create_client(multimodal=False)
            assert client is not None
            
            # Test the case where the API key is missing
            with patch('app.core.llm_service.settings.TEXT_MODEL_API_KEY', None):
                client = service._create_client(multimodal=False)
                assert client is None
    
    def test_extract_invoice_data_text_model(self):
        """Test extracting invoice data using the text model"""
        # Create a service instance
        with patch('app.core.llm_service.OpenAI') as mock_openai:
            # Configure mock return value
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = """{
  "invoice_number": "INV-1001",
  "invoice_date": "2024-06-15",
  "vendor_name": "ACME Corporation",
  "total_amount": 120.00,
  "line_items": [
    {
      "description": "Web Hosting (June)",
      "quantity": 1,
      "unit_price": 100.00,
      "line_total": 100.00
    },
    {
      "description": "SSL Certificate",
      "quantity": 1,
      "unit_price": 20.00,
      "line_total": 20.00
    }
  ]
}"""
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            service = LLMService()
            
            # Call the method to extract invoice data (digital invoice)
            result = service.extract_invoice_data(
                text="""ACME Corporation\n123 Main Street\nNew York, NY 10001\nInvoice Number: INV-1001\nBill To:\nJohn Doe\nXYZ Inc.\nItem Description Qty Unit Price Line Total\n-----------------------------------------------------------\nWeb Hosting (June) 1 $100.00 $100.00\nSSL Certificate 1 $20.00 $20.00\nTotal Amount Due: $120.00""",
                is_scanned=False,
                images=[]
            )
            
            # Verify the result
            assert isinstance(result, ExtractionData)
            assert result.data is not None
            data: InvoiceDataExtended = result.data
            assert data.vendor_name == "ACME Corporation"
            assert data.invoice_number == "INV-1001"
            assert data.invoice_date == date(2024, 6, 15)
            assert data.total_amount == 120.00
            assert isinstance(data.item_info, list)
            assert len(data.item_info) == 2
            line_item_1 = data.item_info[0]
            assert line_item_1.description == "Web Hosting (June)"
            assert line_item_1.quantity == 1
            assert line_item_1.unit_price == 100.00
            assert line_item_1.line_total == 100.00
            line_item_2 = data.item_info[1]
            assert line_item_2.description == "SSL Certificate"
            assert line_item_2.quantity == 1
            assert line_item_2.unit_price == 20.00
            assert line_item_2.line_total == 20.00
    
    def test_extract_invoice_data_multimodal(self):
        """Test extracting invoice data using the multimodal model"""
        # Create a service instance
        service = LLMService()
        
        # Mock settings and multimodal client
        with patch('app.core.llm_service.settings.USE_MULTIMODAL', True):
            # Mock client response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = """
            {
  "invoice_number": "INV-2024-001",
  "invoice_date": "2024-03-15",
  "vendor_name": "TechPro Solutions",
  "total_amount": 6835.01,
  "line_items": [
    {
      "description": "Web Development Services",
      "quantity": 40,
      "unit_price": 125.00,
      "line_total": 5000.00
    },
    {
      "description": "Database Setup and Configuration",
      "quantity": 8,
      "unit_price": 150.00,
      "line_total": 1200.00
    },
    {
      "description": "SSL Certificate (Annual)",
      "quantity": 1,
      "unit_price": 99.00,
      "line_total": 99.00
    },
    {
      "description": "Domain Registration (Annual)",
      "quantity": 1,
      "unit_price": 15.00,
      "line_total": 15.00
    }
  ]
}
"""
            
            # 模拟客户端
            service.vision_client = MagicMock()
            service.vision_client.chat.completions.create.return_value = mock_response
            
            # Call the method to extract invoice data (scanned invoice)
            result = service.extract_invoice_data(
                text="",
                is_scanned=True,
                images=[{'data': 'iVBORw0KGgoAAAANSUhEUgAABqQAAAiYCAIAAAA+NVHkAAEAAElEQVR4nOzdf3RU1b3//32/yW1uhKQ3TsQ0c72CTCVaE4OQgY+CSBoMKOHiEmSk6ioFmo+AXFCy8...AAJELYBwAAAACJEPYBAAAAQCKEfQAAAACQCGEfAAAAACRC2AcAAAAAiRD2AQAAAEAihH0AAAAAkAhhHwAAAAAkQtgHAAAAAIn4L6LY/MghZSUhAAAAAElFTkSuQmCC', 'format': 'PNG', 'page': 1}, {'data': 'iVBORw0KGgoAAAANSUhEUgAABqQAAAiYCAIAAAA+NVHkAABiH0lEQVR4nOzdX2hc953w4dkX3aiUXbQDpaiUmmQghAbjEq/qC4lQGjMuBrOlCR5KLurWXtG4GKcr0...BgQvYBAAAAwITsAwAAAIAJ2QcAAAAAE7IPAAAAACZkHwAAAABMyD4AAAAAmJB9AAAAADAh+wAAAABgQvYBAAAAwITsAwAAAICJAHH1j6fymG4hAAAAAElFTkSuQmCC', 'format': 'PNG', 'page': 2}]
            )
            
            # Verify the result
            assert isinstance(result, ExtractionData)
            assert result.data is not None
            data: InvoiceDataExtended = result.data
            assert data.vendor_name == "TechPro Solutions"
            assert data.invoice_number == "INV-2024-001"
            assert data.invoice_date == date(2024, 3, 15)
            assert data.total_amount == Decimal('6835.01')
            line_items = data.item_info
            assert isinstance(line_items, list)
            assert len(line_items) == 4

            line_item_1 = line_items[0]
            assert line_item_1.description == "Web Development Services"
            assert line_item_1.quantity == 40
            assert line_item_1.unit_price == 125.00
            assert line_item_1.line_total == 5000.00

            line_item_2 = line_items[1]
            assert line_item_2.description == "Database Setup and Configuration"
            assert line_item_2.quantity == 8
            assert line_item_2.unit_price == 150.00
            assert line_item_2.line_total == 1200.00

            line_item_3 = line_items[2]
            assert line_item_3.description == "SSL Certificate (Annual)"
            assert line_item_3.quantity == 1
            assert line_item_3.unit_price == 99.00
            assert line_item_3.line_total == 99.00

            line_item_4 = line_items[3]
            assert line_item_4.description == "Domain Registration (Annual)"
            assert line_item_4.quantity == 1
            assert line_item_4.unit_price == 15.00
            assert line_item_4.line_total == 15.00
    
    def test_validate_and_clean_result_complete_data(self, sample_extraction_result):
        """Test validation and cleaning of complete data"""
        service = LLMService()
        
        # Call the validation and cleaning method
        result = service._validate_and_clean_result(sample_extraction_result)
        
        # Verify the result
        assert result['invoice_number'] == "INV-12345"
        assert result['invoice_date'] == "2024-07-10"
        assert result['vendor_name'] == "Acme Corp"
        assert result['total_amount'] == 1025.75
        assert len(result['line_items']) == 2
    
    def test_validate_and_clean_result_missing_data(self):
        """Test validation and cleaning of missing data"""
        service = LLMService()
        
        # Create result data with some missing fields
        incomplete_result = {
            "invoice_number": "INV-12345",
            # invoice_date is missing
            "vendor_name": "Acme Corp",
            # total_amount is missing
            "line_items": []
        }
        
        # Call the validation and cleaning method
        result = service._validate_and_clean_result(incomplete_result)
        
        # Verify the result
        assert result['invoice_number'] == "INV-12345"
        assert result['invoice_date'] is None
        assert result['vendor_name'] == "Acme Corp"
        assert result['total_amount'] is None
        assert result['line_items'] == []
    
    def test_validate_and_clean_result_invalid_format(self):
        """Test validation and cleaning of invalid format data"""
        service = LLMService()
        
        # Create result data with incorrect format
        invalid_format_result = {
            "invoice_number": 12345,  # Should be a string
            "invoice_date": "Invalid date",  # Invalid date format
            "vendor_name": "",  # Empty string
            "total_amount": "1025.75",  # Should be a number
            "line_items": ["not a dict"]  # Not a dictionary object
        }
        
        # Call the validation and cleaning method
        result = service._validate_and_clean_result(invalid_format_result)
        
        # Verify the result
        assert result['invoice_number'] == "12345"  # Convert to string
        assert result['invoice_date'] is None  # Invalid date converted to Null
        assert result['vendor_name'] is None  # Empty string converted to Null
        assert result['total_amount'] == 1025.75  # Convert to float
        assert result['line_items'] == []  # Invalid array converted to an empty array
    
    def test_llm_initialization_exception(self):
        """Test LLM initialization exception"""
        # Simulate LLM client initialization failure
        with patch('app.core.llm_service.OpenAI', side_effect=Exception("API key error")):
            service = LLMService()
            
            # Expect an exception to be thrown
            with pytest.raises(LLMInitializeException):
                service.extract_invoice_data("text", False, [])

    

