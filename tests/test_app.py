import pytest
from fastapi.testclient import TestClient
from app import app
import os
import io

@pytest.fixture
def client():
    """创建测试客户端"""
    if not os.getenv('ANTHROPIC_API_KEY'):
        pytest.skip("需要设置ANTHROPIC_API_KEY环境变量")
    return TestClient(app)

def test_read_root(client):
    """测试根路由"""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_process_pdf_no_file(client):
    """测试没有文件的情况"""
    response = client.post("/process-pdf/")
    assert response.status_code == 422  # FastAPI的验证错误

def test_process_pdf_wrong_file_type(client):
    """测试错误的文件类型"""
    # 创建测试文件
    file_content = b"This is not a PDF file"
    files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
    
    response = client.post("/process-pdf/", files=files)
    assert response.status_code == 400
    assert "File must be a PDF" in response.json()["detail"]

def test_process_pdf_empty_pdf(client):
    """测试空PDF文件"""
    # 创建空PDF文件
    import fitz
    doc = fitz.open()
    pdf_bytes = doc.write()
    files = {"file": ("test.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    
    response = client.post("/process-pdf/", files=files)
    assert response.status_code == 200 