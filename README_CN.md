# 发票数据提取API - 实现指南

本文档提供了发票提取API项目的详细安装、配置和使用指南。该项目使用AI技术从PDF发票中提取关键信息，支持数字版和扫描版发票。

## 目录

- [系统要求](#系统要求)
- [安装步骤](#安装步骤)
  - [1. 克隆项目](#1-克隆项目)
  - [2. 安装Python依赖](#2-安装Python依赖)
  - [3. 安装Tesseract OCR](#3-安装Tesseract-OCR)
  - [4. 安装Poppler](#4-安装Poppler)
  - [5. 配置OpenAI API密钥](#5-配置OpenAI-API密钥)
- [启动服务](#启动服务)
- [API使用指南](#API使用指南)
- [运行测试](#运行测试)
- [项目结构](#项目结构)
- [常见问题解答](#常见问题解答)

## 系统要求

- Python 3.8+ 
- Windows, macOS 或 Linux
- 网络连接(用于OpenAI API调用)

## 安装步骤

### 1. 克隆项目

```bash
git clone <项目仓库URL>
cd invoice-extraction-api
```

### 2. 安装Python依赖

```bash
pip install -r requirements.txt
```

### 3. 安装Tesseract OCR

Tesseract OCR是处理扫描版发票的必要组件。

**Windows:**
1. 从[这里](https://github.com/UB-Mannheim/tesseract/wiki)下载安装程序
2. 安装到默认位置(`C:\Program Files\Tesseract-OCR`)或自定义位置
3. 将Tesseract安装目录添加到系统PATH环境变量

**macOS:**
```bash
brew install tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install tesseract-ocr
```

### 4. 安装Poppler

Poppler用于PDF转图像处理，对扫描版PDF的处理必不可少。

**Windows:**
1. 从[这里](https://github.com/oschwartz10612/poppler-windows/releases/)下载Poppler
2. 解压到一个永久位置(例如: `C:\Program Files\poppler`)
3. 将bin目录(例如: `C:\Program Files\poppler\bin`)添加到系统PATH环境变量

**macOS:**
```bash
brew install poppler
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install poppler-utils
```

### 5. 配置OpenAI API密钥

项目使用OpenAI的LLM服务进行发票数据提取。

1. 在[OpenAI平台](https://platform.openai.com/)注册并获取API密钥
2. 在项目根目录创建`.env`文件：

```
TEXT_MODEL_API_KEY=your_api_key_here
```

## 启动服务

运行以下命令启动API服务器：

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

服务将在[http://localhost:8000](http://localhost:8000)启动，并提供以下端点：

- `GET /` - API欢迎页面
- `GET /health` - 健康检查端点
- `POST /extract` - 发票提取端点

## API使用指南

### 提取发票数据

**端点:** `POST /extract`

**请求:**
- 使用`multipart/form-data`格式
- 字段名: `file`，值为PDF文件

**curl示例:**
```bash
curl -X POST -F "file=@/path/to/invoice.pdf" http://localhost:8000/extract
```

**Python示例:**
```python
import requests

url = "http://localhost:8000/extract"
files = {"file": open("invoice.pdf", "rb")}

response = requests.post(url, files=files)
print(response.json())
```

**成功响应示例:**
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

## 运行测试

项目包含全面的单元测试和集成测试。

运行所有测试:
```bash
pytest
```

运行特定测试模块:
```bash
pytest tests/test_pdf_processor.py
```

生成测试覆盖率报告:
```bash
pytest --cov=app tests/
```

## 项目结构

```
invoice-extraction-api/
│
├── app/                      # 主应用代码
│   ├── core/                 # 核心业务逻辑
│   │   ├── pdf_processor.py  # PDF处理和类型检测
│   │   ├── ocr_engine.py     # OCR文本识别
│   │   ├── llm_service.py    # LLM服务接口
│   │   └── extraction.py     # 数据提取协调器
│   │
│   ├── routers/              # API路由
│   │   └── invoice_router.py # 发票处理路由
│   │
│   ├── models/               # 数据模型
│   │   └── schemas.py        # Pydantic模型
│   │
│   ├── prompts/              # LLM提示词模板
│   │   └── base_prompts.py   # 基础提示词
│   │
│   └── main.py               # 应用入口点
│
├── config/                   # 配置
│   └── config.py             # 配置管理
│
├── tests/                    # 自动化测试
│
├── Sample Invoices/          # 示例发票
│
├── requirements.txt          # Python依赖
├── Dockerfile                # Docker配置
├── .env                      # 环境变量(需自行创建)
└── README.md                 # 项目文档
```

## 异常错误码参考表

| 错误码 | 异常类 | 描述 |
|------------|-----------------|-------------|
| **1000** | **BaseExtractionException** | 所有提取错误的基类异常 |
| **1100-1199** | **输入异常** | |
| 1100 | InputException | 输入数据相关异常的基类 |
| 1101 | InvalidFileFormatException | 无效的文件格式，仅支持PDF文件 |
| 1102 | EmptyFileException | 上传的文件为空 |
| 1103 | FileTooLargeException | 文件过大，请压缩后重试 |
| **1200-1299** | **PDF处理异常** | |
| 1200 | PDFProcessingException | PDF处理相关异常的基类 |
| 1201 | PDFReadException | 无法读取PDF文件，文件可能已损坏 |
| 1202 | PDFPasswordProtectedException | PDF文件受密码保护，无法处理 |
| 1203 | PDFPageExtractionException | 无法从PDF中提取页面内容 |
| **1300-1399** | **OCR处理异常** | |
| 1300 | OCRProcessingException | OCR处理相关异常的基类 |
| 1301 | OCRFailedException | OCR文字识别失败 |
| 1302 | LowQualityImageException | 图像质量过低，无法准确识别 |
| **1400-1499** | **数据提取异常** | |
| 1400 | DataExtractionException | 数据提取相关异常的基类 |
| 1401 | MissingRequiredFieldException | 无法提取必填字段 |
| 1402 | InvalidDateFormatException | 提取的日期格式无效 |
| 1403 | InvalidAmountFormatException | 提取的金额格式无效 |
| **1500-1599** | **LLM处理异常** | |
| 1500 | LLMProcessingException | LLM处理相关异常的基类 |
| 1501 | LLMRequestFailedException | LLM API请求失败 |
| 1502 | LLMResponseParsingException | 无法解析LLM响应 |
| 1503 | LLMQuotaExceededException | LLM API配额已用尽 |
| **1900-1999** | **系统异常** | |
| 1900 | SystemException | 系统相关异常的基类 |
| 1901 | DatabaseException | 数据库操作异常 |
| 1902 | ConfigurationException | 系统配置异常 |
| 1903 | ServiceUnavailableException | 服务暂时不可用，请稍后再试 |

## 常见问题解答

### Q: 为什么我的OCR识别结果不准确?
A: 请确保正确安装了Tesseract OCR和Poppler。对于特别模糊的发票，可能需要手动调整OCR引擎参数或使用图像预处理提高质量。

### Q: 我没有OpenAI API密钥，有其他选择吗?
A: 目前系统默认使用OpenAI的API。您可以修改`app/core/llm_service.py`以支持其他开源LLM，如Llama 3。

### Q: 服务启动失败，显示"ModuleNotFoundError"
A: 请确保您在项目根目录运行命令，并且已正确安装所有依赖: `pip install -r requirements.txt`

### Q: 如何处理多种语言的发票?
A: 默认配置针对英语发票优化。对于其他语言，请修改`app/core/ocr_engine.py`中的语言参数，并确保在Tesseract中安装了相应的语言包。

### Q: 项目支持Docker部署吗?
A: 是的，项目包含Dockerfile。使用以下命令构建和运行Docker容器:
```bash
docker build -t invoice-extraction-api .
docker run -p 8000:8000 -e TEXT_MODEL_API_KEY=your_api_key invoice-extraction-api
```

---

如有更多问题或需要支持，请提交Issue或联系项目维护人员。
