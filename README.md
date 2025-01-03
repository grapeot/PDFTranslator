# PDF Translator

PDF Translator 是一个智能PDF文档翻译工具，它能够将PDF文档从英文翻译成中文，同时保持原文档的排版格式。本工具使用Claude AI进行智能翻译，不仅能够准确理解文档内容，还能识别文档的布局结构，确保翻译后的文档与原文档具有相似的视觉效果。

## 主要特点

- 保持原文档的排版格式（包括单栏、双栏等布局）
- 智能识别文档结构和图片位置
- 使用Claude AI进行高质量翻译
- Web界面操作，使用方便
- 支持实时翻译预览
- 支持批量处理多页PDF文档
- 智能保持原文档的图表和公式

## 使用方法

1. 访问工具的Web界面（默认地址：http://localhost:8000）
2. 上传需要翻译的PDF文件（支持的最大文件大小：50MB）
3. 系统会自动处理文档并生成翻译结果
   - 每页文档会被单独处理和翻译
   - 系统会智能识别文档的布局结构
   - 图片和公式会被保留在原位置
4. 在界面上实时预览翻译结果
5. 确认无误后下载翻译完成的文档

## 部署说明

### 环境要求

- Python 3.10 或更高版本
- 操作系统：支持 Linux, macOS, Windows
- 至少 4GB 可用内存（推荐 8GB 以上）
- Claude API 访问权限

### 安装步骤

1. 克隆代码库：
```bash
git clone https://github.com/grapeot/PDFTranslator.git
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
# Linux/macOS
export ANTHROPIC_API_KEY="your-api-key"

# Windows (PowerShell)
$env:ANTHROPIC_API_KEY="your-api-key"

# Windows (CMD)
set ANTHROPIC_API_KEY=your-api-key
```

5. 启动服务：
```bash
# 直接启动
python app.py

# 或使用启动脚本
./launch_pdf_translator.sh
```

服务将在 http://localhost:8000 启动。你可以通过修改`app.py`中的配置来更改端口号。

### Docker部署（可选）

如果你偏好使用Docker，可以使用以下命令：

```bash
# 构建镜像
docker build -t pdf-translator .

# 运行容器
docker run -d -p 8000:8000 -e ANTHROPIC_API_KEY="your-api-key" pdf-translator
```

## 开发指南

### 项目结构

- `app.py`: 主应用程序文件，包含FastAPI服务器和PDF处理逻辑
- `index.html`: Web界面前端
- `static/`: 静态资源目录
- `requirements.txt`: 项目依赖文件
- `tests/`: 单元测试目录

### 开发环境设置

1. 按照上述部署步骤设置基本环境
2. 安装开发依赖：
```bash
pip install pytest pytest-asyncio pytest-cov black flake8
```

3. 设置pre-commit hooks（推荐）：
```bash
pre-commit install
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=. tests/

# 运行特定测试文件
pytest tests/test_pdf_processor.py
```

### 主要组件

- `PDFProcessor`: 核心处理类，负责PDF解析和翻译
  - 使用PyMuPDF进行PDF解析
  - 通过Claude API进行智能翻译
  - 保持原文档布局和格式
- FastAPI路由：处理文件上传和页面渲染
- Claude AI集成：通过Anthropic API进行翻译

### 开发建议

- 在修改代码前先运行测试确保环境正常
- 使用 black 进行代码格式化
- 遵循 PEP 8 编码规范
- 添加新功能时确保更新相应的文档
- 提交代码前运行测试套件
- 保持代码简洁，添加必要的注释
- 新功能需要包含相应的单元测试

### 常见问题解决

1. 如果遇到内存不足：
   - 减小处理的PDF页面分辨率
   - 增加系统swap空间
   - 使用批处理模式

2. 如果遇到API限制：
   - 实现请求队列
   - 添加重试机制
   - 使用API密钥轮换

3. 如果遇到布局问题：
   - 检查PDF源文件格式
   - 调整页面解析参数
   - 优化文本块识别算法

## 注意事项

- 需要有效的 Anthropic API key
- PDF文件大小限制为 50MB
- 处理时间取决于文档大小和复杂度
- 建议在处理大型文档时使用批处理模式
- 定期备份重要的翻译结果
- 注意API使用配额和计费

## 贡献指南

欢迎提交Pull Request来改进这个项目。在提交PR之前，请确保：

1. 代码已经过格式化和测试
2. 更新了相关文档
3. 添加了必要的测试用例
4. 遵循项目的代码风格

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。 