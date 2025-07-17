from decimal import Decimal

import requests
import os
import pytest
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api/v1/extract")

# List of PDF files to be tested
# You can add or remove file paths from this list
# The test will be parameterized to run for each file in this list
FILES_TO_TEST = [
    "../../Sample Invoices/invoice2.pdf",
    # "./Sample Invoices/invoice1.pdf",
    # "./Sample Invoices/invoice3.pdf",
    # "./Sample Invoices/invoice5.pdf",
    # "./Sample Invoices/invoice6.pdf",
]

@pytest.mark.parametrize("file_path", FILES_TO_TEST)
def test_extract_api_with_pdf(file_path):
    """
    Tests the /api/v1/extract endpoint with a single PDF file.

    This test checks:
    1. If the PDF file exists before sending.
    2. If the API returns a 200 OK status code.
    3. If the response is a valid JSON.
    4. If the returned JSON contains the expected keys ('filename' and 'extracted_data').
    """
    # --- 1. Check if the file exists ---
    assert os.path.exists(file_path), True

    # --- 2. Prepare and send the request ---
    try:
        with open(file_path, 'rb') as f:
            files = {'files': (os.path.basename(file_path), f, 'application/pdf')}
            response = requests.post(API_URL, files=files)

    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request to {API_URL} failed: {e}. Is the FastAPI server running?")

    # --- 3. Validate the response ---
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response: {response.text}"

    try:
        response_json = response.json()
    except requests.exceptions.JSONDecodeError:
        pytest.fail("Response is not a valid JSON.")

    # As we are sending one file, we expect a list with one item in response.
    assert response_json['code']== 0
    data = response_json['data'][0]['data']
    assert data['invoice_number'] =='INV-2024-001'
    assert data['invoice_date'] =='2024-03-15'
    assert data['vendor_name'] =='TechPro Solutions'
    assert data['total_amount'] =='6835.01'
    item_info = data['item_info']
    assert len(item_info) == 4
    assert item_info[0]['description'] == 'Web Development Services'
    assert float(item_info[0]['quantity']) == 40.0
    assert float(item_info[0]['unit_price']) == 125.00
    assert float(item_info[0]['line_total']) == 5000.00
