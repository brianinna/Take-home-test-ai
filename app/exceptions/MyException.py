"""
Custom exception handling module, for throwing exceptions with error codes in different scenarios.
These exceptions can be converted to standard ExtractionResponse response format.
"""
from app.models.schemas import ExtractionResponse, ExtractionData


class BaseExtractionException(Exception):
    """
    Base class for extraction exceptions.
    All custom exceptions should inherit from this class and provide error codes and error messages.
    """
    # Base error code, subclasses should override this value
    error_code = 1000
    error_message = "An exception occurred during extraction"

    def __init__(self, message=None, *args, **kwargs):
        """
        Initialize exception

        Args:
            message: Optional error message to override default message
            *args: Additional arguments passed to parent class
            **kwargs: Additional keyword arguments passed to parent class
        """
        self.message = message or self.error_message
        super().__init__(self.message, *args, **kwargs)

    def to_result(self) -> ExtractionResponse:
        """
        Convert exception to standardized ExtractionResponse response

        Returns:
            ExtractionResponse: Response object containing error information
        """
        return ExtractionResponse(
            code= self.error_code,
            data=None,
            message=f"[Error Code:{self.error_code}] {self.message}"
        )

    def to_data_result(self) -> ExtractionData:
        """
        Convert exception to file extract result

        Returns:
            ExtractionResponse: Response object containing error information
        """
        return ExtractionData(
            code= self.error_code,
            data=None,
            message=f"[Error Code:{self.error_code}] {self.message}"
        )

# Input related exceptions (1100-1199)
class InputException(BaseExtractionException):
    """Base class for input data related exceptions"""
    error_code = 1100
    error_message = "Input data exception"


class InvalidFileFormatException(InputException):
    """Invalid file format exception"""
    error_code = 1101
    error_message = "Invalid file format, only PDF files are supported"


class EmptyFileException(InputException):
    """Empty file exception"""
    error_code = 1102
    error_message = "Uploaded file is empty"


class FileTooLargeException(InputException):
    """File too large exception"""
    error_code = 1103
    error_message = "File is too large, please compress and try again"


# PDF processing exceptions (1200-1299)
class PDFProcessingException(BaseExtractionException):
    """Base class for PDF processing related exceptions"""
    error_code = 1200

    def __init__(self, message = "LLM processing exception"):
        """

        Args:
            message: error message

        """
        super().__init__(message)

class PDFReadException(PDFProcessingException):
    """PDF reading exception"""
    error_code = 1201
    error_message = "Unable to read PDF file, the file may be corrupted"


class PDFPasswordProtectedException(PDFProcessingException):
    """PDF password protected exception"""
    error_code = 1202
    error_message = "PDF file is password protected, cannot process"


class PDFPageExtractionException(PDFProcessingException):
    """PDF page extraction exception"""
    error_code = 1203
    error_message = "Unable to extract page content from PDF"


# OCR processing exceptions (1300-1399)
class OCRProcessingException(BaseExtractionException):
    """Base class for OCR processing related exceptions"""
    error_code = 1300
    error_message = "OCR processing exception"


class OCRFailedException(OCRProcessingException):
    """OCR recognition failed exception"""
    error_code = 1301
    error_message = "OCR text recognition failed"


class LowQualityImageException(OCRProcessingException):
    """Low image quality exception"""
    error_code = 1302
    error_message = "Image quality is too low for accurate recognition"


# Data extraction exceptions (1400-1499)
class DataExtractionException(BaseExtractionException):
    """Base class for data extraction related exceptions"""
    error_code = 1400
    error_message = "Data extraction exception"


class MissingRequiredFieldException(DataExtractionException):
    """Missing required field exception"""
    error_code = 1401
    error_message = "Unable to extract required field"

    def __init__(self, field_name=None, *args, **kwargs):
        """
        Initialize missing field exception

        Args:
            field_name: Name of the missing field
            *args: Additional arguments passed to parent class
            **kwargs: Additional keyword arguments passed to parent class
        """
        message = f"Unable to extract required field: {field_name}" if field_name else self.error_message
        super().__init__(message, *args, **kwargs)


class InvalidDateFormatException(DataExtractionException):
    """Invalid date format exception"""
    error_code = 1402
    error_message = "Extracted date format is invalid"


class InvalidAmountFormatException(DataExtractionException):
    """Invalid amount format exception"""
    error_code = 1403
    error_message = "Extracted amount format is invalid"


# LLM processing exceptions (1500-1599)
class LLMProcessingException(BaseExtractionException):
    """Base class for LLM processing related exceptions"""
    error_code = 1500


    def __init__(self, message = "LLM processing exception"):
        """

        Args:
            message: error message

        """
        super().__init__(message)


class LLMRequestFailedException(LLMProcessingException):
    """LLM request failed exception"""
    error_code = 1501
    error_message = "LLM API request failed"


class LLMResponseParsingException(LLMProcessingException):
    """LLM response parsing failed exception"""
    error_code = 1502
    error_message = "Unable to parse LLM response"


class LLMQuotaExceededException(LLMProcessingException):
    """LLM quota exceeded exception"""
    error_code = 1503
    error_message = "LLM API quota has been exhausted"

class LLMInitializeException(LLMProcessingException):
    """LLM client initialization failed exception"""
    error_code = 1504
    error_message = "Failed to initialize LLM client"

# System exceptions (1900-1999)
class SystemException(BaseExtractionException):
    """Base class for system related exceptions"""
    error_code = 1900
    error_message = "System exception"


class DatabaseException(SystemException):
    """Database exception"""
    error_code = 1901
    error_message = "Database operation exception"


class ConfigurationException(SystemException):
    """Configuration exception"""
    error_code = 1902
    error_message = "System configuration exception"


class ServiceUnavailableException(SystemException):
    """Service unavailable exception"""
    error_code = 1903
    error_message = "Service temporarily unavailable, please try again later"