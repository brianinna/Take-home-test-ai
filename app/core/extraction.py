"""
Information extraction module, coordinates PDF processing and LLM services to complete the entire invoice information extraction process.
"""
import logging
from typing import List

from fastapi import UploadFile

from app.core.llm_service import LLMService
from app.core.pdf_processor import PDFProcessor
from app.models.schemas import ExtractionResponse
from config.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExtractionService:
    """
    Invoice information extraction service, coordinates the entire information extraction process.
    """

    def __init__(self):
        """Initialize extraction service"""
        # 从配置中读取是否使用多模态视觉API
        use_vision_api = settings.USE_VISION_API
        self.pdf_processor = PDFProcessor(use_vision_api=use_vision_api)
        self.llm_service = LLMService()

    async def process_invoice(self, file: UploadFile) -> ExtractionResponse:
        """
        Process a single invoice file, extract key information
        
        Args:
            file: Uploaded invoice file
            
        Returns:
            Dictionary containing extraction results
        """
        try:
            # Read file content
            file_content = await file.read()

            # Process PDF
            logger.info(f"Starting to process file: {file.filename}")
            pdf_result = self.pdf_processor.process_pdf(file_content)

            # Extract information
            is_scanned = pdf_result["is_scanned"]
            text = pdf_result["text"]

            images = pdf_result.get("images", [])
            # Use LLM to extract key information
            logger.info(
                f"Using LLM to extract information, document type: {'scanned' if is_scanned else 'digital'}, using vision API: {settings.USE_VISION_API}")

            if settings.USE_VISION_API and images and is_scanned:
                logger.info(f"Processing with vision API, found {len(images)} images")
                extraction_result = self.llm_service.extract_invoice_data_with_images(images)
            else:
                extraction_result = self.llm_service.extract_invoice_data(text, is_scanned)

            return extraction_result

        except Exception as e:
            logger.error(f"Error occurred while processing file {file.filename}: {str(e)}")
            return ExtractionResponse(success=False, data=None, message=f"Extraction failed: {str(e)}")

    async def process_multiple_invoices(self, files: List[UploadFile]) -> List[ExtractionResponse]:
        """
        Batch process multiple invoice files
        
        Args:
            files: List of uploaded invoice files
            
        Returns:
            List containing extraction results for each invoice
        """
        results = []

        for file in files:
            result = await self.process_invoice(file)
            results.append(result)

        return results
