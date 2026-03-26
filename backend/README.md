# Resume Optimizer Backend (FastAPI + SQLite)

## 运行
1. 进入后端目录
   - `cd backend`
2. 安装依赖
   - `pip install -r requirements.txt`
3. 配置环境变量
   - 复制环境变量模板：`cp .env.example .env`
   - 编辑 `.env` 文件，填写硅基流动 API 密钥等配置：
     - `SILICONFLOW_API_KEY`: 硅基流动 API 密钥
     - `SILICONFLOW_BASE_URL`: 硅基流动 API 基础 URL（默认：`https://api.siliconflow.cn/v1`）
     - `SILICONFLOW_MODEL`: 使用的模型名称（默认：`Qwen/Qwen2.5-VL-72B-Instruct`）
     - 其他可选配置：
       - `DATABASE_URL`: 数据库路径（默认：`sqlite:///data/resume.db`）
       - `ALLOWED_ORIGINS`: CORS 允许的源（默认：`http://localhost:5173,http://localhost:3000`）
4. 启动服务
   - `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`

## 接口说明
### `POST /api/ocr`
上传 `pdf`，后端会：
1) 用本地 `pymupdf` 尽量抽取文本  
2) 调用硅基流动“结构化解析”（返回 sections）  
3) 写入 SQLite

请求：`multipart/form-data`，字段 `file`

响应：
```json
{
  "resumeId": 1,
  "extractedTextPreview": "...",
  "sections": [
    { "name": "基本信息", "content": "..." }
  ]
}
```

### `POST /api/suggestions`
请求体：
```json
{ "resumeId": 1 }
```
响应：
```json
{
  "resumeId": 1,
  "overall_summary": "...",
  "items": [
    { "name": "...", "issues": ["..."], "recommendations": ["..."], "rewrite_example": "..." }
  ]
}
```

## 备注（课程可讲点）
- 这个演示把“OCR接口”定义为：用模型把简历文本结构化分模块（更稳定、更好讲）。
- 如果你学员需要“扫描件真正 OCR（图片文字识别）”，后续可以在本地增加 `pytesseract` 或接入硅基流动视觉 OCR，再替换 `extract_text_from_pdf_bytes` 这一段。

