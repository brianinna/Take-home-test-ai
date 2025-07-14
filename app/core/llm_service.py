"""
LLM service module, responsible for interacting with large language models for information extraction.
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

import openai
from openai import OpenAI

from config.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set API key and base URL
openai_api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
openai_base_url = os.getenv("OPENAI_BASE_URL")


class LLMService:
    """
    LLM service class, provides interaction with OpenAI API.
    Responsible for preparing prompts, calling API and parsing responses.
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize LLM service
        
        Args:
            api_key: OpenAI API key
            base_url: OpenAI API base URL
        """
        self.api_key = api_key or openai_api_key
        self.base_url = base_url or openai_base_url
        
        if not self.api_key:
            logger.warning("OpenAI API key not set, LLM functionality will not be available")
        
        # Configure OpenAI client, including optional base_url
        # Only use officially supported parameters
        try:
            if self.api_key:
                if self.base_url:
                    logger.info(f"Using custom OpenAI base URL: {self.base_url}")
                    self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
                else:
                    self.client = OpenAI(api_key=self.api_key)
            else:
                self.client = None
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {str(e)}")
            self.client = None
        self.model = settings.DEFAULT_LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
    
    def extract_invoice_data(self, text: str, is_scanned: bool) -> Dict[str, Any]:
        """
        Extract key information from invoice text
        
        Args:
            text: Invoice text to be processed
            is_scanned: Whether it's a scanned PDF, used to adjust prompt strategy
            
        Returns:
            Dictionary containing extraction results
        """
        if not self.client:
            raise ValueError("LLM service not properly initialized, please check API key")
        
        # Build prompt
        prompt = self._build_extraction_prompt(text, is_scanned)
        
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional invoice analysis expert. You need to extract key information from invoice text and return it in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            # Parse and validate results
            result = json.loads(response.choices[0].message.content)
            validated_result = self._validate_and_clean_result(result)
            
            return {
                "success": True,
                "data": validated_result,
                "confidence": 0.85  # Simple version uses fixed confidence
            }
            
        except Exception as e:
            logger.error(f"LLM API call failed: {str(e)}")
            return {
                "success": False,
                "data": None,
                "message": f"Information extraction failed: {str(e)}",
                "confidence": 0.0
            }
    
    def _build_extraction_prompt(self, text: str, is_scanned: bool) -> str:
        """
        Build prompt for information extraction
        
        Args:
            text: Invoice text to be processed
            is_scanned: Whether it's a scanned PDF
            
        Returns:
            Constructed prompt string
        """
        # Base prompt
        base_prompt = """
Please extract the following key information from the invoice text below:
- invoice_number (Invoice number)
- invoice_date (Invoice date, in YYYY-MM-DD format)
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

Invoice text:
"""
        
        # Additional prompts for scanned PDF
        if is_scanned:
            base_prompt += """
Note: This is text extracted from a scanned PDF via OCR, and may contain recognition errors. Please infer the correct information as much as possible, paying special attention to:
1. Invoice numbers may contain combinations of letters and numbers
2. Date formats may be diverse (such as MM/DD/YYYY, DD-MM-YYYY, etc.), please convert uniformly to YYYY-MM-DD
3. Amounts may include currency symbols, thousands separators, etc., please extract only the numeric part
"""
        
        # Add few-shot examples (not implemented in simple version)
        
        # Add text to be processed
        full_prompt = base_prompt + "\n" + text
        
        return full_prompt
    
    def _validate_and_clean_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean results returned by LLM
        
        Args:
            result: Original results returned by LLM
            
        Returns:
            Validated and cleaned results
        """
        validated_result = {}
        
        # Process invoice number
        if "invoice_number" in result and result["invoice_number"]:
            validated_result["invoice_number"] = str(result["invoice_number"]).strip()
        else:
            validated_result["invoice_number"] = None
        
        # Process date
        if "invoice_date" in result and result["invoice_date"]:
            try:
                # Try to parse date string
                date_str = result["invoice_date"].strip()
                # If date is valid ISO format (YYYY-MM-DD), use directly
                datetime.strptime(date_str, "%Y-%m-%d")
                validated_result["invoice_date"] = date_str
            except (ValueError, AttributeError):
                # If date format is invalid, set to None
                validated_result["invoice_date"] = None
        else:
            validated_result["invoice_date"] = None
        
        # Process vendor name
        if "vendor_name" in result and result["vendor_name"]:
            validated_result["vendor_name"] = str(result["vendor_name"]).strip()
        else:
            validated_result["vendor_name"] = None
        
        # Process amount
        if "total_amount" in result and result["total_amount"] is not None:
            try:
                # Convert amount to float
                if isinstance(result["total_amount"], (int, float)):
                    amount = float(result["total_amount"])
                else:
                    # Try to convert from string
                    amount_str = str(result["total_amount"]).replace(',', '')
                    amount = float(amount_str)
                validated_result["total_amount"] = round(amount, 2)
            except (ValueError, TypeError):
                validated_result["total_amount"] = None
        else:
            validated_result["total_amount"] = None
        
        return validated_result
