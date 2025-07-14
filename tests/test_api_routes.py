"""
Tests for API routes
"""
import os
import pytest
import unittest.mock as mock
from fastapi.testclient import TestClient
from pathlib import Path
from app.main import app
from app.core.extraction import ExtractionService

# Create test client
client = TestClient(app)

class TestAPIRoutes:
    """Test API route functionality"""

    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_root_endpoint(self):
        """Test root path endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        assert "Invoice Extraction API" in response.json()["message"]
    
    @mock.patch("app.routers.invoice_router.ExtractionService")
    def test_extract_endpoint_single_file(self, mock_extraction_service):
        """Test invoice extraction endpoint with single file"""
        # Configure mock
        mock_service_instance = mock.MagicMock()
        mock_extraction_service.return_value = mock_service_instance
        
        # Set up processing result
        mock_service_instance.process_multiple_invoices.return_value = [{
            "filename": "invoice1.pdf",
            "success": True,
            "is_scanned": False,
            "data": {
                "invoice_number": "12345",
                "invoice_date": "2023-01-01",
                "vendor_name": "ABC Company",
                "total_amount": 100.00
            },
            "confidence": 0.9
        }]
        
        # Prepare test file
        test_file_path = Path(__file__).parent.parent / "Sample Invoices" / "invoice1.pdf"
        if not test_file_path.exists():
            pytest.skip(f"Test file does not exist: {test_file_path}")
            
        # Send test request
        with open(test_file_path, "rb") as f:
            response = client.post(
                "/extract",
                files=[("files", ("invoice1.pdf", f, "application/pdf"))]
            )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["data"]["invoice_number"] == "12345"
        assert data[0]["data"]["vendor_name"] == "ABC Company"
        assert data[0]["success"] is True
        
        # Verify mock was called correctly
        mock_service_instance.process_multiple_invoices.assert_called_once()
    
    def test_extract_endpoint_validation(self):
        """Test input validation for extraction endpoint"""
        # Test case with no file
        response = client.post("/extract")
        assert response.status_code == 422  # 验证错误
        
        # Test case with incorrect file type
        with open(__file__, "rb") as f:  # 使用当前Python文件作为非PDF文件
            response = client.post(
                "/extract",
                files=[("files", ("test.py", f, "text/plain"))]
            )
        
        # Should return an error
        assert response.status_code == 400
        assert "not a valid PDF" in response.json()["detail"].lower()
    
    @mock.patch("app.routers.invoice_router.ExtractionService")
    def test_extract_endpoint_multiple_files(self, mock_extraction_service):
        """Test invoice extraction endpoint with multiple files"""
        # Configure mock
        mock_service_instance = mock.MagicMock()
        mock_extraction_service.return_value = mock_service_instance
        
        # Set up processing result
        mock_service_instance.process_multiple_invoices.return_value = [
            {
                "filename": "invoice1.pdf",
                "success": True,
                "is_scanned": False,
                "data": {
                    "invoice_number": "12345",
                    "invoice_date": "2023-01-01",
                    "vendor_name": "ABC Company",
                    "total_amount": 100.00
                },
                "confidence": 0.9
            },
            {
                "filename": "invoice2.pdf",
                "success": True,
                "is_scanned": True,
                "data": {
                    "invoice_number": "67890",
                    "invoice_date": "2023-02-01",
                    "vendor_name": "XYZ Corp",
                    "total_amount": 250.00
                },
                "confidence": 0.85
            }
        ]
        
        # Prepare test files
        sample_dir = Path(__file__).parent.parent / "Sample Invoices"
        test_files = list(sample_dir.glob("*.pdf"))[:2]  # 获取前两个PDF文件
        if len(test_files) < 2:
            pytest.skip("Need at least 2 sample invoice files for testing")
            
        # Send test request with multiple files
        with open(test_files[0], "rb") as f1, open(test_files[1], "rb") as f2:
            response = client.post(
                "/extract",
                files=[
                    ("files", (test_files[0].name, f1, "application/pdf")),
                    ("files", (test_files[1].name, f2, "application/pdf"))
                ]
            )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["data"]["invoice_number"] == "12345"
        assert data[1]["data"]["invoice_number"] == "67890"
        
        # Verify mock was called correctly
        mock_service_instance.process_multiple_invoices.assert_called_once()
