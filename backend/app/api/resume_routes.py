from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.db.repo import ResumeRepo
from app.services.siliconflow_client import SiliconFlowClient
from app.services.resume_ocr import extract_text_from_pdf_bytes, llm_extract_sections
from app.services.suggestions import llm_generate_suggestions


router = APIRouter()


class ResumeIdRequest(BaseModel):
    resumeId: int


class OcrResponse(BaseModel):
    resumeId: int
    extractedTextPreview: str
    sections: Any


class SuggestionsResponse(BaseModel):
    resumeId: int
    overall_summary: str
    items: List[Dict[str, Any]]


def _preview(text: str, max_len: int = 800) -> str:
    text = text.strip()
    if len(text) <= max_len:
        return text
    return text[:max_len] + "\n...\n（省略部分内容）"


@router.post("/ocr", response_model=OcrResponse)
async def ocr_resume(file: UploadFile = File(...)) -> OcrResponse:
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="仅支持上传 PDF 文件")

    pdf_bytes = await file.read()
    if len(pdf_bytes) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件过大（建议 <= 20MB）")

    repo = ResumeRepo()
    resume_id = repo.create_record(filename=file.filename)

    try:
        extracted_text = extract_text_from_pdf_bytes(pdf_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 文本抽取失败: {e}")

    if not extracted_text or len(extracted_text.strip()) < 30:
        # 课程里你可以强调：如果是纯扫描件，需要换视觉OCR方案
        extracted_text = ""

    try:
        client = SiliconFlowClient()
        sections = llm_extract_sections(client, extracted_text or "(未能抽取到足够文本，请检查简历PDF格式)")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"硅基流动解析失败: {e}")

    repo.set_ocr_result(resume_id, extracted_text, sections)

    return OcrResponse(
        resumeId=resume_id,
        extractedTextPreview=_preview(extracted_text),
        sections=sections,
    )


@router.post("/suggestions", response_model=SuggestionsResponse)
async def generate_suggestions(req: ResumeIdRequest) -> SuggestionsResponse:
    repo = ResumeRepo()
    record = repo.get_record(req.resumeId)
    if record is None:
        raise HTTPException(status_code=404, detail="未找到该 resumeId 的记录")
    if not record.extracted_text or not record.sections_json:
        raise HTTPException(status_code=400, detail="请先调用 /api/ocr 完成简历解析")

    extracted_text = record.extracted_text or ""
    sections = repo.get_sections(req.resumeId)
    if sections is None:
        raise HTTPException(status_code=400, detail="简历模块数据缺失")

    try:
        client = SiliconFlowClient()
        suggestions = llm_generate_suggestions(client, extracted_text, sections)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"硅基流动生成建议失败: {e}")

    repo.set_suggestions(req.resumeId, suggestions)

    return SuggestionsResponse(
        resumeId=req.resumeId,
        overall_summary=suggestions.get("overall_summary", ""),
        items=suggestions.get("items", []),
    )


@router.get("/resume/{resume_id}")
async def get_resume(resume_id: int) -> Dict[str, Any]:
    repo = ResumeRepo()
    record = repo.get_record(resume_id)
    if record is None:
        raise HTTPException(status_code=404, detail="未找到该 resumeId 的记录")

    return {
        "resumeId": record.id,
        "filename": record.filename,
        "extractedTextPreview": _preview(record.extracted_text or ""),
        "sections": record.sections_json,
        "suggestions": record.suggestions_json,
        "createdAt": record.created_at,
        "updatedAt": record.updated_at,
    }

