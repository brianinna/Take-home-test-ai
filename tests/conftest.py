"""
测试配置文件，提供测试所需的公共fixture和配置
"""
import os
import sys
import pytest
from pathlib import Path

# 将项目根目录添加到Python路径中，确保可以导入应用模块
sys.path.insert(0, str(Path(__file__).parent.parent))

# 测试数据路径
TEST_DATA_DIR = Path(__file__).parent.parent / "Sample Invoices"

@pytest.fixture
def sample_invoices_dir():
    """返回样本发票目录的路径"""
    return TEST_DATA_DIR

@pytest.fixture
def sample_invoice_files():
    """返回所有样本发票文件的路径列表"""
    return sorted([f for f in TEST_DATA_DIR.glob("*.pdf")])

@pytest.fixture
def digital_invoice_path():
    """返回一个数字版PDF发票的路径"""
    # 这里假设invoice1.pdf是数字版发票，实际使用时可能需要调整
    return TEST_DATA_DIR / "invoice1.pdf"

@pytest.fixture
def scanned_invoice_path():
    """返回一个扫描版PDF发票的路径"""
    # 这里假设invoice2.pdf是扫描版发票，实际使用时可能需要调整
    return TEST_DATA_DIR / "invoice2.pdf"
