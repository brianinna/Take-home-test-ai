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

from app.exceptions.MyException import LLMInitializeException, BaseExtractionException, LLMProcessingException
from app.models.schemas import ExtractionResponse, InvoiceDataExtended, ExtractionData
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


    def extract_invoice_data(self, text: str, is_scanned: bool,images: List[Dict[str, Any]]) -> ExtractionData:
        """
        use LLM to generate the structured data from the file
        Args:
            text: the text from the file if it is digital
            is_scanned: whether the file is scanned
            images: the list of images if the file is scanned

        Returns:

        """
        # init different LLM parameter base on the config
        if settings.USE_MULTIMODAL and images and is_scanned:
            client = self.vision_client
            model_name = settings.MULTIMODAL_MODEL_NAME
            system_prompt = BasePromptTemplates.invoice_extraction_base()
            user_message_content = [{"type": "text", "text": BasePromptTemplates.user_prompt(True)}]
            for img in images:
                user_message_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{img['data']}", "detail": "high"}
                })
        else:
            client = self.text_client
            model_name = settings.TEXT_MODEL_NAME
            system_prompt = BasePromptTemplates.system_prompt(is_scanned)
            user_message_content = BasePromptTemplates.user_prompt(False, text)

        if not client:
            raise LLMInitializeException()

        try:
            start_time = time.time()
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system",
                     "content": system_prompt},
                    {"role": "user", "content": user_message_content}
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
                invoice_data = InvoiceDataExtended(
                    invoice_number=validated_result.get("invoice_number", ""),
                    invoice_date=datetime.strptime(validated_result.get("invoice_date", ""), "%Y-%m-%d").date() if validated_result.get("invoice_date") else None,
                    vendor_name=validated_result.get("vendor_name", ""),
                    total_amount=Decimal(str(validated_result.get("total_amount", 0))),
                    itemInfo=validated_result.get("line_items")

                )
            return ExtractionData(code=0, data=invoice_data, message= "success")
        except Exception as e:
            error = f"Error occurred while invoke LLM api: {str(e)}"
            logger.error(error)
            if isinstance(e, BaseExtractionException):
                return e.to_data_result()
            return LLMProcessingException(error).to_data_result()


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
            
        # Process line items
        validated_result["line_items"] = []
        if "line_items" in result and isinstance(result["line_items"], list) and result["line_items"]:
            for item in result["line_items"]:
                if not isinstance(item, dict):
                    continue
                    
                validated_item = {}
                
                # Process description
                if "description" in item and item["description"]:
                    validated_item["description"] = str(item["description"]).strip()
                else:
                    validated_item["description"] = "Unknown item"
                    
                # Process quantity
                if "quantity" in item and item["quantity"] is not None:
                    try:
                        if isinstance(item["quantity"], (int, float)):
                            validated_item["quantity"] = float(item["quantity"])
                        else:
                            qty_str = str(item["quantity"]).replace(',', '')
                            validated_item["quantity"] = float(qty_str)
                    except (ValueError, TypeError):
                        validated_item["quantity"] = None
                else:
                    validated_item["quantity"] = None
                    
                # Process unit price
                if "unit_price" in item and item["unit_price"] is not None:
                    try:
                        if isinstance(item["unit_price"], (int, float)):
                            validated_item["unit_price"] = round(float(item["unit_price"]), 2)
                        else:
                            price_str = str(item["unit_price"]).replace(',', '')
                            validated_item["unit_price"] = round(float(price_str), 2)
                    except (ValueError, TypeError):
                        validated_item["unit_price"] = None
                else:
                    validated_item["unit_price"] = None
                    
                # Process line total
                if "line_total" in item and item["line_total"] is not None:
                    try:
                        if isinstance(item["line_total"], (int, float)):
                            validated_item["line_total"] = round(float(item["line_total"]), 2)
                        else:
                            total_str = str(item["line_total"]).replace(',', '')
                            validated_item["line_total"] = round(float(total_str), 2)
                    except (ValueError, TypeError):
                        validated_item["line_total"] = None
                else:
                    validated_item["line_total"] = None
                    
                validated_result["line_items"].append(validated_item)
                
        return validated_result
