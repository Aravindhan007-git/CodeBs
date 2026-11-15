from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@lru_cache
def _load_landing_page() -> str:
    return (_STATIC_DIR / "index.html").read_text(encoding="utf-8")


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def landing_page() -> HTMLResponse:
    return HTMLResponse(content=_load_landing_page())