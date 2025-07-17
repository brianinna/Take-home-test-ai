"""
Base prompt templates, used for various scenarios of interaction with LLM.

This module provides a collection of prompt templates for different use cases
when interacting with language models, particularly for invoice processing tasks.
"""


class BasePromptTemplates:
    """
    Collection of base prompt templates for various invoice processing tasks.
    """

    @staticmethod
    def invoice_extraction_base() -> str:
        """
        Base prompt template for invoice information extraction.
        
        Returns:
            str: Base prompt template for extracting information from invoices.
        """
        return """
            You are a professional invoice analysis expert. Please extract the following key information from the invoice text below:
            - invoice_number (Invoice number)
            - invoice_date (Invoice date, format YYYY-MM-DD)
            - vendor_name (Vendor name)
            - total_amount (Total invoice amount, numeric value only)
            - line_items (List of all products/services with details)
            
            Return only the result in JSON format, do not include other explanations. Example output format:
            {
              "invoice_number": "INV-12345",
              "invoice_date": "2024-07-10",
              "vendor_name": "Acme Corp",
              "total_amount": 1025.75,
              "line_items": [
                {
                  "description": "Product A",
                  "quantity": 2,
                  "unit_price": 100.00,
                  "line_total": 200.00
                },
                {
                  "description": "Service B",
                  "quantity": 1,
                  "unit_price": 50.00,
                  "line_total": 50.00
                }
              ]
            }
            
            For line_items, extract all products/services listed in the invoice. If quantity, unit_price cannot be determined, use null. If a field cannot be determined, please use null value.
        """

    @staticmethod
    def scanned_invoice_extraction() -> str:
        """
        Prompt template specifically for scanned invoices.
        
        Returns:
            str: Enhanced prompt template for OCR-processed invoice extraction.
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
    def system_prompt(is_scanned: bool) -> str:
        """
        Generate the system prompt based on whether the invoice is scanned or digital.
        
        Args:
            is_scanned: Whether the invoice is scanned (True) or digital (False)
            
        Returns:
            str: Appropriate system prompt for the invoice type
        """
        if is_scanned:
            prompt = BasePromptTemplates.scanned_invoice_extraction()
        else:
            prompt = BasePromptTemplates.invoice_extraction_base()
        return prompt

    @staticmethod
    def user_prompt(is_image: bool, text: str = '') -> str:
        """
        Generate the user prompt for invoice information extraction.
        
        Args:
            is_image: Whether the input is an image (True) or text (False)
            text: The invoice text to process (only used when is_image is False)
            
        Returns:
            str: Formatted user prompt for the LLM
        """
        base_prompt = "Extract the JSON format data from "
        if is_image:
            return base_prompt + "the provided invoice images."
        else:
            return base_prompt + "the following text:\n" + text


    @staticmethod
    def line_items_extraction() -> str:
        """
        Prompt template for extracting invoice line items (extended feature).
        
        This template is designed to extract detailed information about each
        line item in an invoice, including descriptions, quantities, prices, and totals.
        
        Returns:
            str: Prompt template for extracting detailed line items from invoices.
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
        Prompt template for document type classification.
        
        Returns:
            str: Prompt template for classifying document types, particularly invoices.
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
