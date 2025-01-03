# PDF Translator

PDF Translator 是一个智能PDF文档翻译工具，它能够将PDF文档从英文翻译成中文，同时保持原文档的排版格式。本工具使用Claude AI进行智能翻译，不仅能够准确理解文档内容，还能识别文档的布局结构，确保翻译后的文档与原文档具有相似的视觉效果。

## 主要特点

- 保持原文档的排版格式（包括单栏、双栏等布局）
- 智能识别文档结构和图片位置
- 使用Claude AI进行高质量翻译
- Web界面操作，使用方便
- 支持实时翻译预览

## 使用方法

1. 访问工具的Web界面
2. 上传需要翻译的PDF文件
3. 系统会自动处理文档并生成翻译结果
4. 可以在界面上预览和下载翻译后的文档

## 部署说明

### 环境要求

- Python 3.10 或更高版本
- 操作系统：支持 Linux, macOS, Windows

### 安装步骤

1. 克隆代码库：
```bash
git clone [repository-url]
cd PDFTranslator
```

2. 创建并激活虚拟环境（推荐）：
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
.\venv\Scripts\activate  # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 设置环境变量：
```bash
export ANTHROPIC_API_KEY="your-api-key"
```

5. 启动服务：
```bash
python app.py
```

服务将在 http://localhost:8000 启动

## 开发指南

### 项目结构

- `app.py`: 主应用程序文件，包含FastAPI服务器和PDF处理逻辑
- `index.html`: Web界面前端
- `static/`: 静态资源目录
- `requirements.txt`: 项目依赖文件

### 开发环境设置

1. 按照上述部署步骤设置基本环境
2. 安装开发依赖：
```bash
pip install pytest black flake8
```

### 主要组件

- `PDFProcessor`: 核心处理类，负责PDF解析和翻译
- FastAPI路由：处理文件上传和页面渲染
- Claude AI集成：通过Anthropic API进行翻译

### 开发建议

- 在修改代码前先运行测试确保环境正常
- 使用 black 进行代码格式化
- 遵循 PEP 8 编码规范
- 添加新功能时确保更新相应的文档

## 注意事项

- 需要有效的 Anthropic API key
- PDF文件大小限制为 50MB
- 处理时间取决于文档大小和复杂度 