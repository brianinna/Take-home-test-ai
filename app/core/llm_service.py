# app/core/llm_service.py

"""
LLM service module, responsible for interacting with large language models for information extraction.
"""
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional

from openai import OpenAI, APIStatusError

from app.models.schemas import ExtractionResponse, InvoiceData
from app.prompts.base_prompts import BasePromptTemplates
from config.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMService:
    """
    LLM service class, provides interaction with different OpenAI compatible APIs.
    It can hold separate clients for text and multimodal models.
    """

    def __init__(self):
        """Initialize LLM service by creating clients based on configuration."""
        self.text_client = self._create_client(multimodal=False)
        self.vision_client = self._create_client(multimodal=True) if settings.USE_MULTIMODAL else None
        self.temperature = settings.LLM_TEMPERATURE

    def _create_client(self, multimodal: bool) -> Optional[OpenAI]:
        """Helper to create an OpenAI client based on type."""
        if not multimodal:
            api_key = settings.TEXT_MODEL_API_KEY
            base_url = settings.TEXT_MODEL_API_URL
            model_name = settings.TEXT_MODEL_NAME
            model_type = "Text"
        else:
            api_key = settings.MULTIMODAL_MODEL_API_KEY
            base_url = settings.MULTIMODAL_MODEL_API_URL
            model_name = settings.MULTIMODAL_MODEL_NAME
            model_type = "Multimodal"

        if not api_key:
            logger.warning(
                f"{model_type} model API key not set. This functionality will not be available.")
            return None

        try:
            logger.info(f"Initializing client for {'multimodal' if multimodal else 'model'} : {model_name}...")
            if base_url:
                return OpenAI(api_key=api_key, base_url=base_url)
            else:
                return OpenAI(api_key=api_key)
        except Exception as e:
            logger.error(f"Error initializing client: {str(e)}")
            return None

    def _handle_api_error(self, error, model_type: str) -> ExtractionResponse:
        """Common error handling for API calls."""
        if isinstance(error, APIStatusError):
            logger.error(f"{model_type} LLM API call failed with status {error.status_code}: {error.response.text}")
            return ExtractionResponse(success=False, data=None, message=f"API Error: {error.response.text}")
        else:
            logger.error(f"{model_type} LLM API call failed: {str(error)}")
            return ExtractionResponse(success=False, data=None, message=f"Extraction failed: {str(error)}")
        
    def extract_invoice_data_with_images(self, images: List[Dict[str, Any]]) -> ExtractionResponse:
        """
        Extract key information from invoice images using the configured multimodal model.
        """
        if not self.vision_client:
            logger.error("Vision client not initialized. Cannot process images.")
            return ExtractionResponse(success=False, data=None, message="Vision model is not configured.")

        try:
            user_message_content = [{"type": "text", "text":  BasePromptTemplates.user_prompt(True)}]
            for img in images:
                user_message_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{img['data']}", "detail": "high"}
                })

            messages = [
                {"role": "system",
                 "content": BasePromptTemplates.invoice_extraction_base()},
                {"role": "user", "content": user_message_content}
            ]
            start_time = time.time()
            response = self.vision_client.chat.completions.create(
                model=settings.MULTIMODAL_MODEL_NAME,
                messages=messages,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            elapsed_time = time.time() - start_time  # 计算耗时
            logger.info(f"LLM response in {elapsed_time:.2f} seconds consume {response.usage.total_tokens} tokens with content： {response.choices[0].message.content}")
            result = json.loads(response.choices[0].message.content)
            validated_result = self._validate_and_clean_result(result)
            from datetime import datetime
            from decimal import Decimal
            
            invoice_data = None
            if validated_result:
                invoice_data = InvoiceData(
                    invoice_number=validated_result.get("invoice_number", ""),
                    invoice_date=datetime.strptime(validated_result.get("invoice_date", ""), "%Y-%m-%d").date() if validated_result.get("invoice_date") else None,
                    vendor_name=validated_result.get("vendor_name", ""),
                    total_amount=Decimal(str(validated_result.get("total_amount", 0)))
                )
            
            return ExtractionResponse(success=True, data=invoice_data)

        except (APIStatusError, Exception) as e:
            return self._handle_api_error(e, "Multimodal")

    def extract_invoice_data(self, text: str, is_scanned: bool) -> ExtractionResponse:
        """
        Extract key information from invoice text using the configured text model.
        """
        if not self.text_client:
            logger.error("Text client not initialized. Cannot process text.")
            return ExtractionResponse(success=False, data=None, message="Text model is not configured.")

        prompt = BasePromptTemplates.user_prompt(False, text)

        try:
            start_time = time.time()
            response = self.text_client.chat.completions.create(
                model=settings.TEXT_MODEL_NAME,
                messages=[
                    {"role": "system",
                     "content": BasePromptTemplates.system_prompt(is_scanned)},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            elapsed_time = time.time() - start_time
            logger.info(f"LLM response in {elapsed_time:.2f} seconds consume {response.usage.total_tokens} tokens with content： {response.choices[0].message.content}")
            result = json.loads(response.choices[0].message.content)
            validated_result = self._validate_and_clean_result(result)
            from datetime import datetime
            from decimal import Decimal
            
            invoice_data = None
            if validated_result:
                invoice_data = InvoiceData(
                    invoice_number=validated_result.get("invoice_number", ""),
                    invoice_date=datetime.strptime(validated_result.get("invoice_date", ""), "%Y-%m-%d").date() if validated_result.get("invoice_date") else None,
                    vendor_name=validated_result.get("vendor_name", ""),
                    total_amount=Decimal(str(validated_result.get("total_amount", 0)))
                )
            
            return ExtractionResponse(success=True, data=invoice_data)

        except (APIStatusError, Exception) as e:
            return self._handle_api_error(e, "Text")

    def _validate_and_clean_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean the extraction result from the LLM.
        
        Performs validation and normalization on each field to ensure consistency.
        
        Args:
            result: Raw extraction result from LLM
            
        Returns:
            Dict containing validated and cleaned invoice data
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
                date_str = result["invoice_date"].strip()
                datetime.strptime(date_str, "%Y-%m-%d")
                validated_result["invoice_date"] = date_str
            except (ValueError, AttributeError):
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
                if isinstance(result["total_amount"], (int, float)):
                    amount = float(result["total_amount"])
                else:
                    amount_str = str(result["total_amount"]).replace(',', '')
                    amount = float(amount_str)
                validated_result["total_amount"] = round(amount, 2)
            except (ValueError, TypeError):
                validated_result["total_amount"] = None
        else:
            validated_result["total_amount"] = None
        return validated_result
