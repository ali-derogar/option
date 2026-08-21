"""FastAPI application for TSETMC options web UI."""

from __future__ import annotations

import asyncio
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.data import (
    _df_to_records,
    _text_mask,
    get_merged_contracts,
    get_summary,
    get_sentiment,
    get_underlying_contracts,
    get_underlyings,
)
from src.pipeline import run_pipeline
from src.storage import Storage

logger = logging.getLogger(__name__)

WEB_ROOT = Path(__file__).resolve().parent.parent.parent / "web"
STATIC_DIR = WEB_ROOT / "static"

app = FastAPI(title="TSETMC Options", version="1.0.0")
storage = Storage()

_refresh_lock = threading.Lock()
_refresh_status: Dict[str, Any] = {
    "running": False,
    "last_result": None,
    "last_error": None,
    "stage": None,
    "message": None,
    "started_at": None,
    "finished_at": None,
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _update_refresh_status(**payload: Any) -> None:
    with _refresh_lock:
        _refresh_status.update(payload)


def _run_refresh(limit: Optional[int] = None) -> None:
    global _refresh_status
    with _refresh_lock:
        if _refresh_status["running"]:
            return
        _refresh_status["running"] = True
        _refresh_status["last_error"] = None
        _refresh_status["last_result"] = None
        _refresh_status["stage"] = "starting"
        _refresh_status["message"] = "شروع به‌روزرسانی"
        _refresh_status["started_at"] = _utc_now_iso()
        _refresh_status["finished_at"] = None
    try:
        result = run_pipeline(
            limit=limit,
            skip_client_type=False,
            delay_between_calls=0.15,
            progress_callback=lambda payload: _update_refresh_status(**payload),
        )
        _update_refresh_status(
            last_result=result,
            stage="done",
            message=f"به‌روزرسانی کامل شد؛ {result.get('options', 0)} قرارداد",
        )
    except Exception as exc:
        logger.exception("Refresh failed")
        _update_refresh_status(
            last_error=str(exc),
            stage="failed",
            message=f"خطا در به‌روزرسانی: {exc}",
        )
    finally:
        _update_refresh_status(running=False, finished_at=_utc_now_iso())


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/summary")
def summary() -> Dict[str, Any]:
    return get_summary(storage)


@app.get("/api/contracts")
def contracts(
    q: Optional[str] = Query(None, description="Search symbol or name"),
) -> Dict[str, Any]:
    merged = get_merged_contracts(storage)
    if merged.empty:
        return {"items": [], "total": 0}
    if q:
        merged = merged[_text_mask(merged, ("symbol", "short_name", "long_name"), q)]
    return {"items": _df_to_records(merged), "total": len(merged)}


@app.get("/api/underlyings")
def underlyings(
    q: Optional[str] = Query(None, description="Search underlying symbol or name"),
) -> Dict[str, Any]:
    return get_underlyings(storage, q=q)


@app.get("/api/underlyings/{underlying_key}/contracts")
def underlying_contracts(
    underlying_key: str,
    q: Optional[str] = Query(None, description="Search contract symbol or name"),
) -> Dict[str, Any]:
    return get_underlying_contracts(storage, underlying_key=underlying_key, q=q)


@app.get("/api/sentiment")
def sentiment(
    q: Optional[str] = Query(None, description="Search underlying symbol or sentiment"),
) -> Dict[str, Any]:
    return get_sentiment(storage, q=q)


@app.get("/api/open-interest/{ins_code}")
def open_interest_history(ins_code: str) -> Dict[str, Any]:
    try:
        exact_ins_code = int(ins_code)
    except ValueError as exc:
        raise HTTPException(400, "invalid ins_code") from exc
    df = storage.get_open_interest_history_df(ins_code=exact_ins_code)
    return {"ins_code": str(exact_ins_code), "history": _df_to_records(df)}


@app.get("/api/refresh/status")
def refresh_status() -> Dict[str, Any]:
    return dict(_refresh_status)


@app.post("/api/refresh")
def refresh(
    background_tasks: BackgroundTasks,
    limit: Optional[int] = Query(None),
) -> Dict[str, Any]:
    if _refresh_status["running"]:
        return {"status": "already_running"}
    background_tasks.add_task(_run_refresh, limit)
    return {"status": "started"}


@app.get("/")
async def index() -> FileResponse:
    index_path = WEB_ROOT / "index.html"
    if not index_path.exists():
        raise HTTPException(404, "index.html not found")
    return FileResponse(index_path)


@app.get("/underlying/{underlying_key}")
async def underlying_page(underlying_key: str) -> FileResponse:
    index_path = WEB_ROOT / "index.html"
    if not index_path.exists():
        raise HTTPException(404, "index.html not found")
    return FileResponse(index_path)


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
