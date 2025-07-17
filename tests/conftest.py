import os
import io
from unittest.mock import MagicMock, patch

import pytest
import pdfplumber
from PIL import Image


# 项目根目录路径
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture
def digital_invoice_path():
    """提供数字版PDF发票的路径"""
    return os.path.join(PROJECT_ROOT, 'Sample Invoices', 'invoice1.pdf')

@pytest.fixture
def scanned_invoice_paths():
    """提供所有扫描版PDF发票的路径列表"""
    sample_dir = os.path.join(PROJECT_ROOT, 'Sample Invoices')
    # invoice1.pdf是数字版，其余都是扫描版
    return [os.path.join(sample_dir, f'invoice{i}.pdf') for i in range(2, 7)]

@pytest.fixture
def sample_pdf_content():
    """提供样本数字版PDF内容用于测试"""
    with open(os.path.join(PROJECT_ROOT, 'Sample Invoices', 'invoice1.pdf'), 'rb') as f:
        return f.read()

@pytest.fixture
def sample_scanned_pdf_content():
    """提供样本扫描版PDF内容（真实的扫描版PDF数据）"""
    with open(os.path.join(PROJECT_ROOT, 'Sample Invoices', 'invoice2.pdf'), 'rb') as f:
        return f.read()

@pytest.fixture
def sample_image():
    """创建一个简单的PIL图像对象用于测试OCR功能"""
    # 创建一个100x100的白色图像
    image = Image.new('RGB', (100, 100), color='white')
    return image

@pytest.fixture
def mock_pdfplumber(sample_pdf_content):
    """模拟pdfplumber对象，使用数字版PDF"""
    with pdfplumber.open(io.BytesIO(sample_pdf_content)) as pdf:  # 创建一个数字版PDF对象
        return pdf

@pytest.fixture
def mock_scanned_pdfplumber(sample_scanned_pdf_content):
    """模拟pdfplumber对象，使用扫描版PDF"""
    with pdfplumber.open(io.BytesIO(sample_scanned_pdf_content)) as pdf:  # 创建一个扫描版PDF对象
        return pdf



@pytest.fixture
def mock_pytesseract():
    """模拟pytesseract OCR功能"""
    with patch('pytesseract.image_to_string') as mock_ocr:
        mock_ocr.return_value = "Invoice: INV-12345\nDate: 2024-07-10\nVendor: Acme Corp\nTotal: 1025.75"
        yield mock_ocr

@pytest.fixture
def mock_openai_client():
    """模拟OpenAI客户端"""
    with patch('openai.OpenAI') as mock_client_class:
        # 创建一个模拟的OpenAI客户端
        mock_client = MagicMock()
        
        # 模拟聊天完成响应
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"invoice_number": "INV-12345", "invoice_date": "2024-07-10", "vendor_name": "Acme Corp", "total_amount": 1025.75}'
        
        # 设置chat.completions.create返回值
        mock_client.chat.completions.create.return_value = mock_response
        
        # 设置OpenAI类初始化返回模拟客户端
        mock_client_class.return_value = mock_client
        
        yield mock_client_class
        
@pytest.fixture
def sample_extraction_result():
    """样本提取结果数据"""
    return {
        "invoice_number": "INV-12345",
        "invoice_date": "2024-07-10",
        "vendor_name": "Acme Corp",
        "total_amount": 1025.75,
        "line_items": [
            {
                "description": "Product A",
                "quantity": 2,
                "unit_price": 250.00,
                "line_total": 500.00
            },
            {
                "description": "Service B",
                "quantity": 5,
                "unit_price": 105.15,
                "line_total": 525.75
            }
        ]
    }