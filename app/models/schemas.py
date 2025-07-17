"""
Data model definitions, used for API request and response data structures.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date
from decimal import Decimal


class InvoiceData(BaseModel):
    """
    Invoice data model, defines key information extracted from invoices.
    """
    invoice_number: Optional[str] = Field(None, description="Invoice number")
    invoice_date: date = Field(..., description="Invoice date, format YYYY-MM-DD")
    vendor_name: str = Field(..., description="Vendor name")
    total_amount: Decimal = Field(..., description="Total invoice amount")


class InvoiceLineItem(BaseModel):
    """
    Invoice line item, used for advanced features (extension goal).
    """
    description: str = Field(..., description="Product or service description")
    quantity: Optional[Decimal] = Field(None, description="Quantity")
    unit_price: Optional[Decimal] = Field(None, description="Unit price")
    line_total: Decimal = Field(..., description="Line item total amount")


class InvoiceDataExtended(InvoiceData):
    """
    Extended invoice data model with line items (extension goal).
    """
    itemInfo: Optional[List[InvoiceLineItem]] = Field(None, description="Invoice line items")


class ExtractionData(BaseModel):
    """
    API response model, contains extraction results and status information.
    """
    code: int = Field(..., description="status, 0 Whether extraction was successful")
    data: Optional[InvoiceDataExtended] = Field(None, description="Extracted invoice data with line items")
    message: Optional[str] = Field(None, description="Prompt message, especially when errors occur")

class ExtractionResponse(BaseModel):
    """
    API response model, contains extraction results and status information.
    """
    code: int = Field(..., description="status, 0 Whether extraction was successful")
    data: List[ExtractionData] = Field(None, description="Extracted invoice data with line items")
    message: Optional[str] = Field(None, description="Prompt message, especially when errors occur")



class HealthResponse(BaseModel):
    """
    Health check response.
    """
    status: str = Field("ok", description="Service status")
