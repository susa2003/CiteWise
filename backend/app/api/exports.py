from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.analysis import AnalysisRun
from backend.app.schemas.exports import ExportRequest
from backend.app.services.exports.report import render_report


router = APIRouter(tags=["exports"])
MIME_TYPES = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@router.post("/exports")
def export_report(request: ExportRequest, session: Session = Depends(get_db)) -> StreamingResponse:
    run = session.get(AnalysisRun, request.run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Analysis report not found.")
    try:
        content = render_report(run.kind, run.result_data, request.format)
    except ImportError as exc:
        raise HTTPException(status_code=503, detail=f"The {request.format.upper()} export library is not installed.") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="The report could not be generated.") from exc
    filename = f"citewise-{run.kind}-{run.id[:8]}.{request.format}"
    return StreamingResponse(
        iter([content]),
        media_type=MIME_TYPES[request.format],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
