# app/core/llm_service.py

"""
LLM service module, responsible for interacting with large language models for information extraction.
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from openai import OpenAI, APIStatusError

from app.models.schemas import ExtractionResponse, InvoiceData
from app.prompts.base_prompts import PromptBuilder
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
        self.text_client = self._create_client("text")
        self.vision_client = self._create_client("vision") if settings.USE_VISION_API else None
        self.temperature = settings.LLM_TEMPERATURE

    def _create_client(self, multimodal: bool) -> Optional[OpenAI]:
        """Helper to create an OpenAI client based on type."""
        if not multimodal:
            api_key = settings.TEXT_MODEL_API_KEY
            base_url = settings.TEXT_MODEL_API_URL
            model_name = settings.TEXT_MODEL_NAME
        else:
            api_key = settings.MULTIMODAL_MODEL_API_KEY
            base_url = settings.MULTIMODAL_MODEL_API_URL
            model_name = settings.MULTIMODAL_MODEL_NAME

        if not api_key:
            logger.warning(
                f"model API key not set. This functionality will not be available.")
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

    def extract_invoice_data_with_images(self, images: List[Dict[str, Any]]) -> ExtractionResponse:
        """
        Extract key information from invoice images using the configured multimodal model.
        """
        if not self.vision_client:
            logger.error("Vision client not initialized. Cannot process images.")
            return ExtractionResponse(success=False, data=None, message="Vision model is not configured.")

        try:
            user_message_content = [{"type": "text", "text": PromptBuilder.build_image_extraction_prompt()}]
            for img in images:
                user_message_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{img['data']}", "detail": "high"}
                })

            messages = [
                {"role": "system",
                 "content": "You are a professional invoice analysis expert. Extract key information from the provided invoice images and return it in JSON format."},
                {"role": "user", "content": user_message_content}
            ]

            response = self.vision_client.chat.completions.create(
                model=settings.MULTIMODAL_MODEL_NAME,
                messages=messages,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            validated_result = self._validate_and_clean_result(result)
            # 创建 InvoiceData 对象，然后将其包装在 ExtractionResponse 中
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
            
            return ExtractionResponse(success=True, data=invoice_data, confidence=0.90)

        except APIStatusError as e:
            logger.error(f"Multimodal LLM API call failed with status {e.status_code}: {e.response.text}")
            return ExtractionResponse(success=False, data=None, message=f"API Error: {e.response.text}")
        except Exception as e:
            logger.error(f"Multimodal LLM API call failed: {str(e)}")
            return ExtractionResponse(success=False, data=None, message=f"Extraction failed: {str(e)}")

    def extract_invoice_data(self, text: str, is_scanned: bool) -> ExtractionResponse:
        """
        Extract key information from invoice text using the configured text model.
        """
        if not self.text_client:
            logger.error("Text client not initialized. Cannot process text.")
            return ExtractionResponse(success=False, data=None, message="Text model is not configured.")

        prompt = PromptBuilder.build_extraction_prompt(text, is_scanned)

        try:
            response = self.text_client.chat.completions.create(
                model=settings.TEXT_MODEL_NAME,
                messages=[
                    {"role": "system",
                     "content": "You are a professional invoice analysis expert. Extract key information from invoice text and return it in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            validated_result = self._validate_and_clean_result(result)
            # 创建 InvoiceData 对象，然后将其包装在 ExtractionResponse 中
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
            
            return ExtractionResponse(success=True, data=invoice_data, confidence=0.85)

        except APIStatusError as e:
            logger.error(f"Text LLM API call failed with status {e.status_code}: {e.response.text}")
            return ExtractionResponse(success=False, data=None, message=f"API Error: {e.response.text}")
        except Exception as e:
            logger.error(f"Text LLM API call failed: {str(e)}")
            return ExtractionResponse(success=False, data=None, message=f"Extraction failed: {str(e)}")

    def _validate_and_clean_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
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
