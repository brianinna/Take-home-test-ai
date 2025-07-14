"""
Information extraction module, coordinates PDF processing and LLM services to complete the entire invoice information extraction process.
"""
import logging
from typing import Dict, Any, BinaryIO, List
from fastapi import UploadFile

from app.core.pdf_processor import PDFProcessor
from app.core.llm_service import LLMService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExtractionService:
    """
    Invoice information extraction service, coordinates the entire information extraction process.
    """
    
    def __init__(self):
        """Initialize extraction service"""
        self.pdf_processor = PDFProcessor()
        self.llm_service = LLMService()
    
    async def process_invoice(self, file: UploadFile) -> Dict[str, Any]:
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
            
            # Use LLM to extract key information
            logger.info(f"Using LLM to extract information, document type: {'scanned' if is_scanned else 'digital'}")
            extraction_result = self.llm_service.extract_invoice_data(text, is_scanned)
            
            # Combine results
            result = {
                "filename": file.filename,
                "is_scanned": is_scanned,
                "success": extraction_result["success"],
                "data": extraction_result["data"],
                "confidence": extraction_result.get("confidence", 0.0),
            }
            
            if not extraction_result["success"]:
                result["message"] = extraction_result.get("message", "Extraction failed")
            
            return result
            
        except Exception as e:
            logger.error(f"Error occurred while processing file {file.filename}: {str(e)}")
            return {
                "filename": file.filename,
                "success": False,
                "message": f"Processing error: {str(e)}",
                "data": None
            }
    
    async def process_multiple_invoices(self, files: List[UploadFile]) -> List[Dict[str, Any]]:
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
