"""SignalGate Audit Trail Routers"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Response
from backend.app.schemas import AuditListResponse
from backend.app.services.audit import AuditService
from backend.app.dependencies import get_audit_service

router = APIRouter(prefix="/audit", tags=["Audit Trail"])


@router.get("", response_model=AuditListResponse)
def list_audit_records(
    limit: int = Query(50, ge=1, le=200, description="Page limit (max 200)."),
    offset: int = Query(0, ge=0, description="Offset for pagination."),
    action: Optional[str] = Query(None, description="Filter by triage action."),
    reason_code: Optional[str] = Query(None, description="Filter by reason code."),
    case_id: Optional[str] = Query(None, description="Filter by case identifier."),
    audit_service: AuditService = Depends(get_audit_service),
) -> AuditListResponse:
    """Read actual persisted JSONL audit records with filtering and pagination."""
    return audit_service.list_records(
        limit=limit,
        offset=offset,
        action=action,
        reason_code=reason_code,
        case_id=case_id,
    )


@router.get("/export")
def export_audit_records(
    format: str = Query("jsonl", pattern="^(jsonl|csv)$", description="Export format: 'jsonl' or 'csv'."),
    action: Optional[str] = Query(None, description="Filter by triage action."),
    reason_code: Optional[str] = Query(None, description="Filter by reason code."),
    case_id: Optional[str] = Query(None, description="Filter by case identifier."),
    audit_service: AuditService = Depends(get_audit_service),
) -> Response:
    """Download filtered audit trail records as JSONL or CSV."""
    exported_data = audit_service.export_records(
        format_type=format,
        action=action,
        reason_code=reason_code,
        case_id=case_id,
    )

    media_type = "application/x-ndjson" if format == "jsonl" else "text/csv"
    filename = f"audit_export.{format}"

    return Response(
        content=exported_data,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
