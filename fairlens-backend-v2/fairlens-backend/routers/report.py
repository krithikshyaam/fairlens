"""
routers/report.py
POST /report
Generates a PDF bias audit report for a completed analysis.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from core import store
from core.reporter import generate_pdf
from models.schemas import ReportRequest

router = APIRouter(prefix="/report", tags=["Report"])


@router.post("")
async def generate_report(req: ReportRequest):
    """
    Generate a PDF bias audit report for a completed analysis.

    If include_mitigation=true and a /mitigate call was previously run
    for this analysis_id, the PDF will include the before/after comparison.

    Returns: application/pdf binary response.
    """
    saved = store.load(req.analysis_id)
    if saved is None:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis '{req.analysis_id}' not found. Run /analyze first."
        )

    analysis = saved["result"]
    mitigation = saved.get("mitigation") if req.include_mitigation else None

    try:
        pdf_bytes = generate_pdf(analysis, mitigation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation error: {str(e)}")

    filename = f"fairlens_audit_{req.analysis_id[:8]}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
