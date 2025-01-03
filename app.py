from fastapi import FastAPI, UploadFile, HTTPException, File
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import fitz
import io
import os
import base64
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
from anthropic import AsyncAnthropic
from pathlib import Path
from jinja2 import Template
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Create static directory if it doesn't exist
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    return FileResponse("index.html")

class PDFProcessor:
    def __init__(self):
        # Read API key from environment
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("Please set ANTHROPIC_API_KEY environment variable")
        self.client = AsyncAnthropic(api_key=api_key)
    
    def parse_page(self, page):
        """Extract text and coordinates from a page"""
        page_width = page.rect.width
        page_height = page.rect.height
        blocks = page.get_text("dict")["blocks"]
        
        text_items = []
        for block in blocks:
            if block.get("type") == 0:  # Text block
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if text:
                            bbox = span.get("bbox")
                            normalized_bbox = [
                                bbox[0] / page_width,
                                bbox[1] / page_height,
                                bbox[2] / page_width,
                                bbox[3] / page_height
                            ]
                            text_items.append(f"{text}\t{json.dumps(normalized_bbox)}")
        
        return "\n".join(text_items)

    def render_page(self, page, zoom=2):
        """Render a page to image"""
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix)
        img_data = pix.tobytes("jpeg")
        return Image.open(io.BytesIO(img_data))

    async def process_with_claude(self, image_data, text_content):
        """Process page with Claude"""
        try:
            # Convert image to base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Create messages
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": f"""这个是一个pdf第一页的图像和parse的文本信息。请你：
1. 利用图像结合文字输入，用文本信息辅助定位输出位置，从高层理解这个文档的内容和目的。
2. 输出中文翻译。要求是输出的位置如果写上这个中文字，看起来观感需要和看英文原文layout差不多。比如如果原文是两个column中间左边的column，译文的位置也要在左边。如果原文是单栏的，译文也要是单栏的。输出要是一整个文字块，比如一个段落。
3. 辨别哪些地方是图片，这样我们可以原样贴回去。注意图片不会出现在parse的文本信息中。你要找到适当的文本，和图片和这个文本的相对关系，然后推理图片的位置。

请只输出json，不要输出其他东西。注意json字符串里面的双引号要escape。
输出格式：{{"texts": [{{"bbox": [x1, y1, x2, y2], "content": <text>}}, ...], "images": [[x1, y1, x2, y2], ...]}}

文本内容：
{text_content}"""
                        }
                    ]
                }
            ]
            
            # Get first response
            response = await self.client.messages.create(
                model="claude-3-5-sonnet-latest",
                max_tokens=8192,
                messages=messages,
                system="Respond in JSON format."
            )
            
            part1 = response.content[0].text
            logger.info("Received first part of the response")
            
            # Continue the conversation
            messages.append({
                "role": "assistant",
                "content": part1
            })
            messages.append({
                "role": "user",
                "content": [{"type": "text", "text": "继续。尤其是上一次没有翻译的部分。如果实在是没有要补充的了，输出空的texts和images"}]
            })
            
            # Get second response
            response = await self.client.messages.create(
                model="claude-3-5-sonnet-latest",
                max_tokens=8192,
                messages=messages,
                system="Respond in JSON format."
            )
            
            part2 = response.content[0].text
            logger.info("Received second part of the response")
            
            # Combine responses
            try:
                json1 = json.loads(part1)
                try:
                    json2 = json.loads(part2)
                except json.JSONDecodeError:
                    logger.warning("Could not parse part2 JSON, using only part1")
                    json2 = {"texts": [], "images": []}
                
                # Merge the results
                result = {
                    "texts": json1.get("texts", []) + json2.get("texts", []),
                    "images": json1.get("images", []) + json2.get("images", [])
                }
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error in part1: {str(e)}")
                logger.error(f"Part 1: {part1}")
                # Return a default structure if JSON parsing fails
                return {
                    "texts": [
                        {
                            "bbox": [0.1, 0.1, 0.9, 0.9],
                            "content": "Error: Could not parse Claude's response"
                        }
                    ],
                    "images": []
                }
            
        except Exception as e:
            logger.error(f"Error processing with Claude: {str(e)}")
            raise

    def crop_regions(self, image, regions):
        """Crop regions from image"""
        width, height = image.size
        cropped_images = []
        
        for bbox in regions:
            x1 = int(bbox[0] * width)
            y1 = int(bbox[1] * height)
            x2 = int(bbox[2] * width)
            y2 = int(bbox[3] * height)
            
            cropped = image.crop((x1, y1, x2, y2))
            img_byte_arr = io.BytesIO()
            cropped.save(img_byte_arr, format='JPEG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Convert to base64 for HTML embedding
            img_base64 = base64.b64encode(img_byte_arr).decode('utf-8')
            cropped_images.append(img_base64)
            
        return cropped_images

async def process_page(pdf_processor, page, page_num):
    """Process a single page"""
    try:
        # 获取页面尺寸
        page_width = page.rect.width
        page_height = page.rect.height
        
        # Render original page
        rendered_image = pdf_processor.render_page(page)
        
        # Convert rendered image to JPEG bytes
        img_byte_arr = io.BytesIO()
        rendered_image.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()
        img_base64 = base64.b64encode(img_byte_arr).decode('utf-8')
        
        # Process with Claude for translation
        result = await pdf_processor.process_with_claude(img_byte_arr, pdf_processor.parse_page(page))
        
        return {
            'page_num': page_num,
            'width': page_width,
            'height': page_height,
            'original_image': img_base64,
            'texts': result.get('texts', []),
        }
    except Exception as e:
        logger.error(f"Error processing page {page_num + 1}: {str(e)}")
        raise

@app.post("/process-pdf/")
async def process_pdf(file: UploadFile = File(..., max_size=50_000_000)):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Read the file content immediately
    try:
        logger.info("Starting to read PDF file")
        pdf_content = await file.read()
        logger.info(f"Read {len(pdf_content)} bytes from uploaded file")
    except Exception as e:
        logger.error(f"Error reading uploaded file: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    async def event_generator():
        doc = None
        pdf_stream = None
        try:
            pdf_stream = io.BytesIO(pdf_content)
            logger.info("Created BytesIO stream")
            
            doc = fitz.open(stream=pdf_stream, filetype="pdf")
            logger.info(f"Opened PDF document with {len(doc)} pages")
            
            # Initialize processor
            pdf_processor = PDFProcessor()
            logger.info("Initialized PDF processor")
            
            # Process pages sequentially
            for page_num in range(len(doc)):
                logger.info(f"Processing page {page_num + 1} of {len(doc)}")
                page = doc[page_num]
                result = await process_page(pdf_processor, page, page_num)
                logger.info(f"Completed processing page {page_num + 1}")
                
                # Generate HTML for this page
                html_template = """
                <div class="page">
                    <h2>Page {{ page.page_num + 1 }}</h2>
                    <div class="page-container">
                        <div class="page-section">
                            <h3>原文</h3>
                            <div class="page-content" style="padding-top: {{ (page.height / page.width * 100)|round(2) }}%;">
                                <img src="data:image/jpeg;base64,{{ page.original_image }}" alt="Original Page {{ page.page_num + 1 }}" class="page-image">
                            </div>
                        </div>
                        <div class="page-section">
                            <h3>译文</h3>
                            <div class="page-content" style="padding-top: {{ (page.height / page.width * 100)|round(2) }}%;">
                                {% for text in page.texts %}
                                <div class="text-block" style="left: {{ text.bbox[0] * 100 }}%; top: {{ text.bbox[1] * 100 }}%; width: {{ (text.bbox[2] - text.bbox[0]) * 100 }}%;">
                                    {{ text.content }}
                                </div>
                                {% endfor %}
                            </div>
                        </div>
                    </div>
                </div>
                """
                template = Template(html_template)
                page_html = template.render(page=result)
                logger.info(f"Generated HTML for page {page_num + 1}")
                
                # Add debug information
                debug_info = {
                    'page_number': page_num + 1,
                    'page_width': result['width'],
                    'page_height': result['height'],
                    'aspect_ratio': result['height'] / result['width'],
                    'text_blocks': len(result['texts'])
                }
                
                # Send the page HTML and debug info as an event
                yield f"data: {json.dumps({'html': page_html, 'debug': debug_info})}\n\n"
                
            # Send end message
            yield "data: {\"end\": true}\n\n"
            logger.info("Completed processing all pages")
            
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            logger.exception("Full traceback:")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            logger.info("Cleaning up resources")
            if doc:
                doc.close()
                logger.info("Closed PDF document")
            if pdf_stream:
                pdf_stream.close()
                logger.info("Closed PDF stream")
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010) 