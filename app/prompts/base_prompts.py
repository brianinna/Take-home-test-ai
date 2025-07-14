"""
Base prompt templates, used for various scenarios of interaction with LLM.
"""
from typing import Dict, Any


class BasePromptTemplates:
    """Collection of base prompt templates"""
    
    @staticmethod
    def invoice_extraction_base() -> str:
        """
        Base prompt template for invoice information extraction
        """
        return """
You are a professional invoice analysis expert. Please extract the following key information from the invoice text below:
- invoice_number (Invoice number)
- invoice_date (Invoice date, format YYYY-MM-DD)
- vendor_name (Vendor name)
- total_amount (Total invoice amount, numeric value only)

Return only the result in JSON format, do not include other explanations. Example output format:
{
  "invoice_number": "INV-12345",
  "invoice_date": "2024-07-10",
  "vendor_name": "Acme Corp",
  "total_amount": 1025.75
}

If a field cannot be determined, please use null value.
"""

    @staticmethod
    def scanned_invoice_extraction() -> str:
        """
        Prompt template specifically for scanned invoices
        """
        base = BasePromptTemplates.invoice_extraction_base()
        additional = """
Note: This is text extracted from a scanned PDF via OCR, and may contain recognition errors. Please infer the correct information as much as possible, paying special attention to:
1. Invoice numbers may contain combinations of letters and numbers
2. Date formats may be diverse (such as MM/DD/YYYY, DD-MM-YYYY, etc.), please convert uniformly to YYYY-MM-DD
3. Amounts may include currency symbols, thousands separators, etc., please extract only the numeric part
"""
        return base + additional

    @staticmethod
    def line_items_extraction() -> str:
        """
        Prompt template for extracting invoice line items (extended feature)
        """
        return """
Please extract all line items (product or service details) from the following invoice text. For each line item, please extract:
- description (Description)
- quantity (Quantity, if available)
- unit_price (Unit price, if available)
- line_total (Line item total amount)

Return the results in JSON array format:
[
  {
    "description": "Item 1 description",
    "quantity": 2,
    "unit_price": 100.00,
    "line_total": 200.00
  },
  {
    "description": "Item 2 description",
    "quantity": 1,
    "unit_price": 50.00,
    "line_total": 50.00
  }
]

If you cannot determine the value of a field, please use null.
"""

    @staticmethod
    def document_classification() -> str:
        """
        Prompt template for document type classification
        """
        return """
Please analyze the following document text and determine if it is an invoice. If it is an invoice, please further classify what type of invoice it is (e.g., sales invoice, purchase invoice, service invoice, etc.).

Please return the result in JSON format:
{
  "is_invoice": true/false,
  "invoice_type": "Invoice type",
  "confidence": 0.95
}

If it is not an invoice, please specify the possible type of document in invoice_type.
"""


class PromptBuilder:
    """
    Prompt builder, used for assembling and customizing prompts
    """
    
    @staticmethod
    def build_extraction_prompt(text: str, is_scanned: bool = False) -> str:
        """
        Build invoice extraction prompt
        
        Args:
            text: Invoice text
            is_scanned: Whether it is a scanned invoice
            
        Returns:
            Complete prompt string
        """
        if is_scanned:
            prompt = BasePromptTemplates.scanned_invoice_extraction()
        else:
            prompt = BasePromptTemplates.invoice_extraction_base()
        
        # Add text to be processed
        full_prompt = prompt + "\n\nInvoice text:\n" + text
        
        return full_prompt
