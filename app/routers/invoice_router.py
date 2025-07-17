"""
API routing module, defines API endpoints related to invoice processing.
"""
import logging
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends

from app.core.extraction import ExtractionService
from app.exceptions.MyException import BaseExtractionException, EmptyFileException, InvalidFileFormatException
from app.models.schemas import HealthResponse, ExtractionResponse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Dependency injection
def get_extraction_service():
    return ExtractionService()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    
    Returns:
        HealthResponse: Status information
    """
    return {"status": "ok"}


@router.post("/extract", response_model=ExtractionResponse)
async def extract_invoice_data(
    files: List[UploadFile] = File(...),
    extraction_service: ExtractionService = Depends(get_extraction_service)
):
    """
    Invoice data extraction endpoint
    
    Args:
        files: PDF invoice files to process (can be multiple)
        extraction_service: Extraction service instance (via dependency injection)
        
    Returns:
        ExtractionResponse: List of extraction results
    """
    try:
        # Check files
        if not files:
            raise EmptyFileException()

        # Validate file type
        for file in files:
            if not file.filename.lower().endswith('.pdf'):
                raise InvalidFileFormatException()
        # Process files
        results = await extraction_service.process_multiple_invoices(files)
        return results
    except BaseExtractionException as e:
        logger.error(f"Error occurred while processing invoices: {e.error_message}")
        return e.to_result()
    except Exception as e:
        logger.error(f"Error occurred while processing invoices: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
