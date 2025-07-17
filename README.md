[中文说明](./README_CN.md)

# Invoice Data Extraction API - Implementation Guide

This document provides a detailed guide for installing, configuring, and using the Invoice Extraction API project. This project uses AI technology to extract key information from PDF invoices, supporting both digital and scanned versions.

## Table of Contents

- [System Requirements](#system-requirements)
- [Installation Steps](#installation-steps)
  - [1. Clone the Project](#1-clone-the-project)
  - [2. Install Python Dependencies](#2-install-python-dependencies)
  - [3. Install Tesseract OCR](#3-install-tesseract-ocr)
  - [4. Install Poppler](#4-install-poppler)
  - [5. Configure OpenAI API Key](#5-configure-openai-api-key)
- [Starting the Service](#starting-the-service)
- [API Usage Guide](#api-usage-guide)
- [Running Tests](#running-tests)
- [Project Structure](#project-structure)
- [Frequently Asked Questions (FAQ)](#frequently-asked-questions-faq)

## System Requirements

- Python 3.8+
- Windows, macOS, or Linux
- Internet connection (for OpenAI API calls)

You can start the service using Docker or by cloning the code.

## 1.1 Start with Docker

Copy `.env.example` to `.env`, then modify the corresponding configurations in the `.env` file.

```bash
docker build -t invoice-extraction-api .
docker run -p 8000:8000 --env-file .env invoice-extraction-api
```

## 1.2 Local Installation Steps

### 1. Clone the Project

```bash
git clone <PROJECT_REPOSITORY_URL>
cd invoice-extraction-api
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Tesseract OCR

Tesseract OCR is a necessary component for processing scanned invoices.

**Windows:**
1. Download the installer from [here](https://github.com/UB-Mannheim/tesseract/wiki).
2. Install to the default location (`C:\Program Files\Tesseract-OCR`) or a custom location.
3. Add the Tesseract installation directory to the system PATH environment variable.

**macOS:**
```bash
brew install tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install tesseract-ocr
```

### 4. Install Poppler

Poppler is used for PDF to image conversion, which is essential for processing scanned PDFs.

**Windows:**
1. Download Poppler from [here](https://github.com/oschwartz10612/poppler-windows/releases/).
2. Unzip it to a permanent location (e.g., `C:\Program Files\poppler`).
3. Add the `bin` directory (e.g., `C:\Program Files\poppler\bin`) to the system PATH environment variable.

**macOS:**
```bash
brew install poppler
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install poppler-utils
```

### 5. Configure OpenAI API Key

The project uses OpenAI's LLM service for invoice data extraction.

1. Register and get an API key from the [OpenAI platform](https://platform.openai.com/).
2. Create a `.env` file in the project root directory:

```
TEXT_MODEL_API_KEY=your_api_key_here
```

## Starting the Service

Run the following command to start the API server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The service will start at [http://localhost:8000](http://localhost:8000) and provide the following endpoints:

- `GET /` - API welcome page
- `GET /health` - Health check endpoint
- `POST /extract` - Invoice extraction endpoint

## API Usage Guide

### Extract Invoice Data

**Endpoint:** `POST /extract`

**Request:**
- Use `multipart/form-data` format
- Field name: `file`, value is the PDF file

**curl Example:**
```bash
curl -X POST -F "file=@/path/to/invoice.pdf" http://localhost:8000/extract
```

**Python Example:**
```python
import requests

url = "http://localhost:8000/extract"
files = {"file": open("invoice.pdf", "rb")}

response = requests.post(url, files=files)
print(response.json())
```

**Successful Response Example:**
```json
{
  "success": true,
  "invoice_number": "INV-12345",
  "invoice_date": "2024-07-10",
  "vendor_name": "Acme Corp",
  "total_amount": 1025.75,
  "metadata": {
    "is_scanned": false,
    "confidence": 0.95,
    "processing_time": 1.23
  }
}
```

## Running Tests

The project includes comprehensive unit and integration tests.

Run all tests:
```bash
pytest
```

Run a specific test module:
```bash
pytest tests/test_pdf_processor.py
```

Generate a test coverage report:
```bash
pytest --cov=app tests/
```

## Project Structure

```
invoice-extraction-api/
│
├── app/                      # Main application code
│   ├── core/                 # Core business logic
│   │   ├── pdf_processor.py  # PDF processing and type detection
│   │   ├── ocr_engine.py     # OCR text recognition
│   │   ├── llm_service.py    # LLM service interface
│   │   └── extraction.py     # Data extraction coordinator
│   │
│   ├── routers/              # API routes
│   │   └── invoice_router.py # Invoice processing route
│   │
│   ├── models/               # Data models
│   │   └── schemas.py        # Pydantic models
│   │
│   ├── prompts/              # LLM prompt templates
│   │   └── base_prompts.py   # Base prompts
│   │
│   └── main.py               # Application entry point
│
├── config/                   # Configuration
│   └── config.py             # Configuration management
│
├── tests/                    # Automated tests
│
├── Sample Invoices/          # Sample invoices
│
├── requirements.txt          # Python dependencies
├── Dockerfile                # Docker configuration
├── .env                      # Environment variables (to be created)
└── README.md                 # Project documentation
```

## Exception Error Code Reference Table

| Error Code | Exception Class             | Description                                      |
|------------|-----------------------------|--------------------------------------------------|
| **1000**   | **BaseExtractionException** | Base class for all extraction errors             |
| **1100-1199**| **Input Exceptions**      |                                                  |
| 1100       | InputException              | Base class for input data-related exceptions     |
| 1101       | InvalidFileFormatException  | Invalid file format, only PDF files are supported|
| 1102       | EmptyFileException          | The uploaded file is empty                       |
| 1103       | FileTooLargeException       | File is too large, please compress and retry     |
| **1200-1299**| **PDF Processing Exceptions**|                                                  |
| 1200       | PDFProcessingException      | Base class for PDF processing-related exceptions |
| 1201       | PDFReadException            | Cannot read PDF file, it may be corrupted        |
| 1202       | PDFPasswordProtectedException| The PDF file is password protected               |
| 1203       | PDFPageExtractionException  | Failed to extract page content from PDF          |
| **1300-1399**| **OCR Processing Exceptions**|                                                  |
| 1300       | OCRProcessingException      | Base class for OCR processing-related exceptions |
| 1301       | OCRFailedException          | OCR text recognition failed                      |
| 1302       | LowQualityImageException    | Image quality is too low for accurate recognition|
| **1400-1499**| **Data Extraction Exceptions**|                                                  |
| 1400       | DataExtractionException     | Base class for data extraction-related exceptions|
| 1401       | MissingRequiredFieldException| Failed to extract a required field               |
| 1402       | InvalidDateFormatException  | The extracted date format is invalid             |
| 1403       | InvalidAmountFormatException| The extracted amount format is invalid           |
| **1500-1599**| **LLM Processing Exceptions**|                                                  |
| 1500       | LLMProcessingException      | Base class for LLM processing-related exceptions |
| 1501       | LLMRequestFailedException   | LLM API request failed                           |
| 1502       | LLMResponseParsingException | Failed to parse the LLM response                 |
| 1503       | LLMQuotaExceededException   | LLM API quota has been exceeded                  |
| **1900-1999**| **System Exceptions**     |                                                  |
| 1900       | SystemException             | Base class for system-related exceptions         |
| 1901       | DatabaseException           | Database operation exception                     |
| 1902       | ConfigurationException      | System configuration exception                   |
| 1903       | ServiceUnavailableException | The service is temporarily unavailable, please try again later|

## Frequently Asked Questions (FAQ)

### Q: Why are my OCR results inaccurate?
A: Please ensure that Tesseract OCR and Poppler are installed correctly. For particularly blurry invoices, you may need to manually adjust OCR engine parameters or use image preprocessing to improve quality.

### Q: I don't have an OpenAI API key. Are there other options?
A: The system currently defaults to using OpenAI's API. You can modify `app/core/llm_service.py` to support other open-source LLMs, such as Llama 3.

### Q: The service fails to start, showing "ModuleNotFoundError".
A: Please ensure you are running the command from the project root directory and have correctly installed all dependencies: `pip install -r requirements.txt`

### Q: How to handle invoices in multiple languages?
A: The default configuration is optimized for English invoices. For other languages, please modify the language parameter in `app/core/ocr_engine.py` and ensure the corresponding language packs are installed in Tesseract.

---

For more questions or support, please submit an Issue or contact the project maintainers.