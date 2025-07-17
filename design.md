# Invoice Data Extraction Service - Design Document

## 1. Project Overview

This project aims to build a Python-based service that extracts structured data from PDF invoices, both scanned (image-based) and digital (text-based). The service exposes a RESTful API that accepts PDF invoices and returns structured JSON data containing key invoice information. The system leverages AI technologies including OCR (Optical Character Recognition) and LLM (Large Language Models) to process documents and extract structured data.

### 1.1 Key Features

- PDF type detection (scanned vs. digital)
- Information extraction from both types of PDFs using customized processing pipelines
- OCR processing for scanned documents using Tesseract
- LLM integration for intelligent data extraction (OpenAI API)
- Support for vision-capable LLMs for direct processing of scanned invoices
- RESTful API with FastAPI framework
- Comprehensive error handling and validation
- Structured JSON output with key invoice fields including line items

## 2. System Architecture

The system follows a modular design with clear separation of concerns to ensure maintainability and extensibility.

### 2.1 High-Level Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│             │     │             │     │             │     │             │
│  API Layer  │────▶│  Processing │────▶│ Extraction  │────▶│  Response   │
│             │     │    Layer    │     │    Layer    │     │    Layer    │
│             │     │             │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

### 2.2 Component Breakdown

#### 2.2.1 API Layer
- FastAPI framework for RESTful endpoints
- Input validation and error handling with Pydantic models
- File upload handling through multipart/form-data
- CORS middleware for cross-origin requests
- Global exception handling with custom error codes
- Health check endpoints

#### 2.2.2 Processing Layer
- PDF type detection (scanned vs. digital) using content analysis
- Digital PDF text extraction with pdfplumber
- OCR processing using Tesseract for scanned documents
- PDF to image conversion with pdf2image/poppler
- Image preprocessing for improved OCR quality
- Temporary file management

#### 2.2.3 Extraction Layer
- LLM integration with OpenAI API (GPT models)
- Support for vision-capable LLMs for direct image processing
- Configurable prompt templates for different extraction scenarios
- Multi-model fallback mechanisms
- Result validation and data cleaning

#### 2.2.4 Response Layer
- Structured JSON formatting with Pydantic models
- Field-level validation and type conversion
- Metadata enrichment (confidence scores, processing metrics)
- Comprehensive error handling with detailed error codes

## 3. Information Extraction Approaches

### 3.1 PDF Type Detection

The system uses a sophisticated heuristic approach to detect whether a PDF is scanned or digital:

1. Text content analysis - evaluates text extraction quality and quantity
2. Character density evaluation - analyzes the distribution of text across pages
3. Image coverage assessment - checks if pages are predominantly images

This multi-faceted approach achieves high accuracy in differentiating between digital and scanned PDFs.

### 3.2 Digital PDF Processing

1. Extract text directly using pdfplumber
   - Table structure preservation
   - Page-by-page extraction with error handling
   - Text content analysis
2. Process extracted text with LLM for information extraction
   - Structured prompting with field specifications
   - Format normalization and validation

### 3.3 Scanned PDF Processing

#### Approach 1: Traditional OCR + LLM
- Convert PDF pages to images using pdf2image/poppler
- Preprocess images for optimal OCR results (grayscale conversion, contrast enhancement)
- Extract text using Tesseract OCR with configurable parameters
- Apply specialized OCR-aware prompting to LLM for handling recognition errors

#### Approach 2: Multi-modal Visual Language Models
- Process PDF pages as images using vision-capable LLMs
- Convert images to base64 for API transmission
- Direct extraction from visual content using specialized prompts
- Handle multi-page documents with aggregation logic


## 4. LLM Integration

### 4.1 Model Selection and Configuration

- Primary: OpenAI models (GPT-4/GPT-3.5) for text processing
- Multimodal: GPT-4 Vision for direct image processing when enabled
- Configuration through environment variables:
  ```
  TEXT_MODEL_API_KEY=your_api_key
  TEXT_MODEL_API_URL=optional_custom_endpoint
  TEXT_MODEL_NAME=model_name
  MULTIMODAL_MODEL_API_KEY=vision_api_key
  ```
- Fallback mechanisms between models when primary fails

### 4.2 Prompt Engineering

- Specialized prompt templates for different document types and extraction tasks
- OCR-aware prompting for handling recognition errors in scanned documents
- Structured output format specification with JSON examples
- System and user prompts separation for clear context setting

### 4.3 Prompt Management

The system uses a structured prompt management system implemented in `app/prompts/base_prompts.py`:

```python
class BasePromptTemplates:
    @staticmethod
    def invoice_extraction_base() -> str:
        # Base prompt for invoice data extraction
    
    @staticmethod
    def scanned_invoice_extraction() -> str:
        # Enhanced prompt for OCR-processed invoices
    
    @staticmethod
    def system_prompt(is_scanned: bool) -> str:
        # Generate appropriate system prompt based on document type
    
    @staticmethod
    def user_prompt(is_image: bool, text: str = '') -> str:
        # Generate user prompt for image or text input
    
    @staticmethod
    def line_items_extraction() -> str:
        # Specialized prompt for extracting invoice line items
```

### 4.4 Result Validation and Processing

The extracted results undergo comprehensive validation and cleaning:

- Date format normalization (conversion to YYYY-MM-DD)
- Numerical value cleaning (removing currency symbols, commas)
- Confidence scoring based on extraction completeness
- Type conversion and validation for all fields
- Handling of missing or uncertain data

## 5. API Specification

### 5.1 Base Configuration

The API is built with FastAPI and follows RESTful principles:

```python
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Invoice data extraction service API, supporting digital and scanned PDF processing.",
    version="0.1.0",
)
```

### 5.2 Endpoints

#### GET /
- **Description**: Welcome endpoint with API information
- **Response**: Basic API information and links to documentation

#### GET /api/v1/health
- **Description**: Health check endpoint
- **Response**: Service health status

#### POST /api/v1/extract
- **Description**: Extract data from invoice PDF
- **Request**: Multipart form with PDF file
- **Response**: Extracted invoice data in JSON format

### 5.3 API Interface

The client can interact with the API using standard HTTP libraries:

```python
# Python example with requests
import requests

url = "http://localhost:8000/api/v1/extract"
files = {"file": open("invoice.pdf", "rb")}

response = requests.post(url, files=files)
print(response.json())
```

```bash
# curl example
curl -X POST -F "file=@/path/to/invoice.pdf" http://localhost:8000/api/v1/extract
```

This implementation:
- Uses standard HTTP multipart/form-data for file uploads
- Provides detailed error information in responses
- Returns structured JSON data with validation

## 6. Project Structure

The project follows a modular structure with clear separation of concerns:

```
invoice-extraction-api/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Application entry point and FastAPI setup
│   ├── routers/
│   │   └── invoice_router.py   # API routes definition
│   ├── core/
│   │   ├── pdf_processor.py    # PDF handling and type detection
│   │   ├── ocr_engine.py       # OCR processing with Tesseract
│   │   └── llm_service.py      # LLM integration with OpenAI
│   ├── exceptions/
│   │   └── MyException.py      # Custom exception classes
│   ├── models/
│   │   └── schemas.py          # Pydantic data models
│   ├── prompts/
│   │   └── base_prompts.py     # LLM prompt templates
│   └── utils/
│       └── helpers.py          # Utility functions
├── tests/
│   ├── unit/
│   │   ├── core/
│   │   │   ├── test_pdf_processor.py
│   │   │   └── test_llm_service.py
│   │   └── api/
│   │       └── test_endpoints.py
│   └── fixtures/
│       └── sample_invoices/    # Test PDF files
├── config/
│   └── config.py               # Configuration settings
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── Dockerfile                  # Container definition
├── README.md                   # English documentation
├── README_CN.md               # Chinese documentation
└── design.md                  # Design documentation
```

## 7. API Specification

### 7.1 Endpoints

#### GET /
- **Description**: API welcome page with basic information
- **Response Format**: JSON
- **Example Response**: 
  ```json
  {
    "message": "Welcome to the Invoice Data Extraction API",
    "version": "0.1.0",
    "docs_url": "/docs"
  }
  ```

#### GET /api/v1/health
- **Description**: Service health check endpoint
- **Response Format**: JSON
- **Example Response**: 
  ```json
  { "status": "ok" }
  ```

#### POST /api/v1/extract
- **Description**: Process PDF invoice and extract structured data
- **Request Format**: multipart/form-data
- **Parameters**: 
  - `file`: Single PDF file (required)
- **Response Format**: JSON with extraction results

### 7.2 Example Responses

#### Successful Response

```json
{
  "success": true,
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
  ],
  "metadata": {
    "is_scanned": false,
    "confidence": 0.95,
    "processing_time": 1.23
  }
}
```

#### Error Response

```json
{
  "success": false,
  "error": {
    "code": 1101,
    "message": "Invalid file format, only PDF files are supported"
  }
}
```

### 7.3 Error Codes

The API uses a structured error code system for clear error reporting:

| Error Code | Exception Class | Description |
|------------|-----------------|-------------|
| **1000** | **BaseExtractionException** | Base class for all extraction errors |
| **1100-1199** | **Input Exceptions** | |
| 1100 | InputException | Base class for input data-related exceptions |
| 1101 | InvalidFileFormatException | Invalid file format, only PDF files are supported |
| 1102 | EmptyFileException | The uploaded file is empty |
| 1103 | FileTooLargeException | File is too large, please compress and retry |
| **1200-1299** | **PDF Processing Exceptions** | |
| 1200 | PDFProcessingException | Base class for PDF processing-related exceptions |
| 1201 | PDFReadException | Cannot read PDF file, it may be corrupted |
| 1202 | PDFPasswordProtectedException | The PDF file is password protected |
| 1203 | PDFPageExtractionException | Failed to extract page content from PDF |
| **1300-1399** | **OCR Processing Exceptions** | |
| 1300 | OCRProcessingException | Base class for OCR processing-related exceptions |
| 1301 | OCRFailedException | OCR text recognition failed |
| 1302 | LowQualityImageException | Image quality is too low for accurate recognition |
| **1400-1499** | **Data Extraction Exceptions** | |
| 1400 | DataExtractionException | Base class for data extraction-related exceptions |
| 1401 | MissingRequiredFieldException | Failed to extract a required field |
| 1402 | InvalidDateFormatException | The extracted date format is invalid |
| 1403 | InvalidAmountFormatException | The extracted amount format is invalid |
| **1500-1599** | **LLM Processing Exceptions** | |
| 1500 | LLMProcessingException | Base class for LLM processing-related exceptions |
| 1501 | LLMRequestFailedException | LLM API request failed |
| 1502 | LLMResponseParsingException | Failed to parse the LLM response |
| 1503 | LLMQuotaExceededException | LLM API quota has been exceeded |

