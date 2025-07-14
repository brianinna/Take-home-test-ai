# Invoice Data Extraction Service - Design Document

## 1. Project Overview

This project aims to build a Python-based service that extracts structured data from PDF invoices, both scanned (image-based) and digital (text-based). The service will expose a RESTful API that accepts PDF invoices and returns structured JSON data containing key invoice information.

### 1.1 Key Features

- PDF type detection (scanned vs. digital)
- Information extraction from both types of PDFs
- RESTful API for invoice processing
- Structured JSON output with key invoice fields
- Error handling and validation

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
- Input validation and error handling
- File upload handling

#### 2.2.2 Processing Layer
- PDF type detection (scanned vs. digital)
- PDF text extraction / OCR processing
- Document preprocessing

#### 2.2.3 Extraction Layer
- LLM integration for information extraction
- Prompt management
- Information validation

#### 2.2.4 Response Layer
- JSON formatting
- Response validation
- Error handling

## 3. Information Extraction Approaches

### 3.1 Digital PDF Processing

1. Extract text directly using PyPDF2 or pdfplumber
2. Process extracted text with LLM for information extraction

### 3.2 Scanned PDF Processing

#### Approach 1: Traditional OCR + LLM
- Use Tesseract or other OCR tools to extract text
- Pass extracted text to LLM for information extraction

#### Approach 2: Multi-modal Visual Language Models
- Process PDF pages as images using vision-capable LLMs
- Direct extraction from visual content

#### Approach 3: Document AI Services
- Use specialized document processing APIs

#### Approach 4: Hybrid Approach (Recommended)
- High-quality OCR with position information
- Reconstruct document layout
- Enhanced prompts with spatial information

## 4. LLM Integration

### 4.1 Model Selection

- Primary: OpenAI GPT-4/GPT-4o for main extraction tasks
- Alternative: Claude 3 for specialized extraction
- Local Option: Llama 3 or Mistral for fallback/simpler tasks

### 4.2 Prompt Engineering

- Structured prompt templates for different extraction tasks
- Few-shot learning with examples
- Chain-of-thought prompting for complex extractions

### 4.3 Prompt Management

```
/prompts
├── templates/         # Base templates
├── examples/          # Few-shot examples
└── engine.py          # Prompt assembly and management
```

## 5. Test Client Design

### 5.1 API Test Client

- Python-based test client for API validation
- Supports both single and batch file processing
- Uses real PDF files for testing rather than empty placeholders
- Performs file existence validation before attempting upload

### 5.1 Client Architecture

The test client provides a simple way to interact with the Invoice Extraction API. It supports both single file and batch processing capabilities.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│             │     │             │     │             │
│  File Input │────▶│  API Client │────▶│  Results    │
│  Handler    │     │  Interface  │     │  Display    │
│             │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
```

### 5.2 Multi-File Support

The client supports multiple input methods:

1. **Single File Path**: Process a single invoice PDF
2. **Directory Path**: Process all PDF files in a directory
3. **File List**: Process multiple specific PDF files provided as a list

This flexible approach allows for both targeted testing and batch processing scenarios.

### 5.3 API Interface

The client uses simple HTTP requests with the Python `requests` library:

```python
# Simple API request implementation
response = requests.post(api_url, files={"files": (file_name, file_data, "application/pdf")})
```

This implementation:
- Uses standard library components
- Minimizes dependencies
- Provides clear error handling
- Supports both single and batch file processing

## 6. Project Structure

```
project/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Application entry point
│   ├── routers/
│   │   └── invoice_router.py   # API routes
│   ├── core/
│   │   ├── pdf_processor.py    # PDF handling
│   │   ├── ocr_engine.py       # OCR processing
│   │   ├── llm_service.py      # LLM integration
│   │   └── extraction.py       # Information extraction
│   ├── models/
│   │   └── schemas.py          # Data models/schemas
│   ├── prompts/
│   │   ├── base_prompts.py     # Base prompt templates
│   │   ├── extraction.py       # Extraction prompts
│   │   └── validation.py       # Validation prompts
│   └── utils/
│       ├── validators.py       # Data validators
│       └── helpers.py          # Helper functions
├── tests/
│   ├── test_pdf_processor.py
│   ├── test_extraction.py
│   └── test_api.py
├── config/
│   └── config.py               # Configuration
├── requirements.txt
├── Dockerfile
└── README.md
```

## 6. API Specification

### 6.1 Endpoints

#### POST /extract
- **Description**: Process one or more PDF invoices
- **Request Format**: multipart/form-data
- **Parameters**: 
  - `files`: One or more PDF files
- **Response**: JSON array of extraction results

#### GET /health
- **Description**: Service health check
- **Response**: `{ "status": "ok" }`

### 6.2 Example Response

```json
{
  "invoice_number": "INV-12345",
  "invoice_date": "2024-07-10",
  "vendor_name": "Acme Corp",
  "total_amount": 1025.75
}
```

## 7. Quality Assurance

### 7.1 Testing Strategy

- Unit tests for individual components
- Integration tests for end-to-end workflows
- Performance testing for response time and throughput

### 7.2 Accuracy Measurement

- Field-level accuracy metrics
- Document-level accuracy metrics
- Continuous monitoring and improvement

## 8. Extensibility

The architecture is designed to be extensible in the following ways:

### 8.1 Short-term Extensions

- Line item extraction
- Additional invoice fields
- Support for more document types

### 8.2 Long-term Extensions

- Multi-language support
- Custom extraction models for specific vendors
- Automated data validation and correction
- Integration with accounting systems

## 9. Implementation Plan

### 9.1 Phase 1: Core Functionality

- Basic project setup and API endpoints
- PDF type detection
- Basic extraction for digital PDFs
- Simple OCR for scanned PDFs
- Minimal LLM integration

### 9.2 Phase 2: Enhanced Features

- Advanced OCR processing
- Sophisticated LLM prompting
- Improved accuracy and validation
- Support for more complex invoice formats

### 9.3 Phase 3: Optimization & Extensions

- Performance optimization
- Additional data fields extraction
- Line item extraction
- Containerization

## 10. Challenges and Mitigations

### 10.1 OCR Quality

**Challenge**: Poor OCR quality from low-resolution scans
**Mitigation**: Pre-processing images, using high-quality OCR engines, applying LLM for error correction

### 10.2 Invoice Format Variability

**Challenge**: Wide variation in invoice layouts and formats
**Mitigation**: Template-based approaches, adaptive prompting, few-shot examples

### 10.3 LLM Reliability

**Challenge**: Inconsistent extraction by LLMs
**Mitigation**: Prompt engineering, result validation, fallback mechanisms

## 11. Conclusion

This design provides a flexible and extensible framework for invoice data extraction. By leveraging modern AI/ML techniques, particularly LLMs, the system can handle a wide variety of invoice formats and layouts while maintaining high accuracy. The modular architecture allows for future enhancements and optimizations.
