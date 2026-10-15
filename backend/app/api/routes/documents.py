from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from backend.app.services.documents import get_document, locate_source


router = APIRouter(prefix="/documents")


@router.get("/{document_id}")
def read_document(document_id: str):
    document = get_document(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Source document not found")

    safe_filename = document["filename"].replace('"', "")
    return Response(
        content=document["content"],
        media_type=document["content_type"],
        headers={
            "Content-Disposition": f'inline; filename="{safe_filename}"',
            "Cache-Control": "private, no-store",
        },
    )


@router.get("/{document_id}/source")
def find_document_source(
    document_id: str,
    field_path: str = Query(min_length=1, max_length=200),
    value: str = Query(min_length=1, max_length=500),
    context: str = Query(default="", max_length=500),
):
    result = locate_source(document_id, field_path, value, context)
    if result is None:
        raise HTTPException(status_code=404, detail="Source document not found")
    return result
