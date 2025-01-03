import pytest
import os
from app import PDFProcessor
import fitz
import io
from PIL import Image
import base64
import json

@pytest.fixture
def pdf_processor():
    """创建PDFProcessor实例的fixture"""
    if not os.getenv('ANTHROPIC_API_KEY'):
        pytest.skip("需要设置ANTHROPIC_API_KEY环境变量")
    return PDFProcessor()

def test_parse_page(pdf_processor):
    """测试页面解析功能"""
    # 创建一个简单的测试PDF
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((100, 100), "Test content")
    
    # 解析页面
    result = pdf_processor.parse_page(page)
    
    # 验证结果
    assert isinstance(result, str)
    assert "Test content" in result
    assert "\t" in result  # 检查坐标信息是否存在

def test_render_page(pdf_processor):
    """测试页面渲染功能"""
    # 创建测试PDF
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((100, 100), "Test content")
    
    # 渲染页面
    result = pdf_processor.render_page(page)
    
    # 验证结果
    assert isinstance(result, Image.Image)
    assert result.mode in ["RGB", "RGBA"]

@pytest.mark.asyncio
async def test_process_with_claude(pdf_processor):
    """测试Claude AI处理功能"""
    # 创建测试图像
    img = Image.new('RGB', (100, 100), color='white')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()
    
    # 创建测试文本
    text_content = "Test text\t[0.1, 0.1, 0.9, 0.9]"
    
    # 处理内容
    result = await pdf_processor.process_with_claude(img_byte_arr, text_content)
    
    # 验证结果
    assert isinstance(result, dict)
    assert "texts" in result
    assert "images" in result
    assert isinstance(result["texts"], list)
    assert isinstance(result["images"], list)

def test_crop_regions(pdf_processor):
    """测试图像裁剪功能"""
    # 创建测试图像
    img = Image.new('RGB', (100, 100), color='white')
    
    # 定义裁剪区域
    regions = [[0.1, 0.1, 0.9, 0.9]]
    
    # 裁剪图像
    result = pdf_processor.crop_regions(img, regions)
    
    # 验证结果
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], str)
    # 验证base64编码
    try:
        base64.b64decode(result[0])
    except Exception:
        pytest.fail("Invalid base64 encoding") 