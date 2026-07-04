from __future__ import annotations

from fastapi import APIRouter, Response

from backend.schemas import ExportRequest
from core.report import export_docx

router = APIRouter(tags=["export"])

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


@router.post("/export/docx")
def export(req: ExportRequest) -> Response:
    data = export_docx(req.bullets)
    is_docx = data[:2] == b"PK"
    filename = "tailored_cv." + ("docx" if is_docx else "md")
    return Response(
        content=data,
        media_type=DOCX_MIME if is_docx else "text/markdown",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
