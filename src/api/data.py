"""API helpers for web frontend."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from src.analysis.sentiment import analyze_options_sentiment
from src.storage import Storage

ID_FIELDS = {"ins_code", "underlying_ins_code", "underlying_key"}


def _serialize_value(val: Any, key: Optional[str] = None) -> Any:
    if key in ID_FIELDS and _is_present(val):
        return _code_to_string(val)
    if isinstance(val, datetime):
        return val.isoformat()
    if isinstance(val, pd.Timestamp):
        return val.isoformat()
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    return val


def _df_to_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    if df.empty:
        return []
    records = df.to_dict(orient="records")
    return [
        {k: _serialize_value(v, k) for k, v in row.items()}
        for row in records
    ]


def get_merged_contracts(storage: Storage) -> pd.DataFrame:
    contracts = storage.get_contracts_df()
    if contracts.empty:
        return contracts
    client_type = storage.get_latest_client_type_df()
    if client_type.empty:
        return contracts
    ct_cols = list(client_type.columns)
    drop_cols = [c for c in ct_cols if c in contracts.columns and c != "ins_code"]
    client_type = client_type.drop(columns=drop_cols, errors="ignore")
    return contracts.merge(client_type, on="ins_code", how="left")


def _is_present(value: Any) -> bool:
    if value is None:
        return False
    try:
        if pd.isna(value):
            return False
    except (TypeError, ValueError):
        pass
    return str(value).strip() != ""


def _normalize_text(value: Any) -> str:
    if not _is_present(value):
        return ""
    return (
        str(value)
        .strip()
        .lower()
        .replace("ي", "ی")
        .replace("ك", "ک")
        .replace("\u200c", "")
    )


def _text_mask(df: pd.DataFrame, columns: tuple[str, ...], query: str) -> pd.Series:
    normalized_query = _normalize_text(query)
    mask = pd.Series(False, index=df.index)
    if not normalized_query:
        return mask
    for col in columns:
        if col in df.columns:
            normalized_col = df[col].map(_normalize_text)
            mask = mask | normalized_col.str.contains(normalized_query, na=False, regex=False)
    return mask


def _code_to_string(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    if isinstance(value, float):
        return str(int(value)) if value.is_integer() else str(value)
    return str(value).strip()


def _underlying_key(row: pd.Series) -> Optional[str]:
    code = row.get("underlying_ins_code")
    if _is_present(code):
        return _code_to_string(code)
    symbol = row.get("underlying_symbol")
    if _is_present(symbol):
        return _normalize_text(symbol)
    return None


def _sum_or_none(series: pd.Series) -> Optional[float]:
    value = pd.to_numeric(series, errors="coerce").sum(min_count=1)
    return None if pd.isna(value) else float(value)


def _min_or_none(series: pd.Series) -> Optional[float]:
    value = pd.to_numeric(series, errors="coerce").min()
    return None if pd.isna(value) else float(value)


def _max_or_none(series: pd.Series) -> Optional[float]:
    value = pd.to_numeric(series, errors="coerce").max()
    return None if pd.isna(value) else float(value)


def _first_present(series: pd.Series) -> Any:
    for value in series:
        if _is_present(value):
            return value
    return None


def get_underlyings(storage: Storage, q: Optional[str] = None) -> Dict[str, Any]:
    merged = get_merged_contracts(storage)
    if merged.empty:
        return {"items": [], "total": 0}

    df = merged.copy()
    df["underlying_key"] = df.apply(_underlying_key, axis=1)
    df = df[df["underlying_key"].notna()]
    if q:
        df = df[_text_mask(df, ("underlying_symbol", "underlying_short_name"), q)]

    items: List[Dict[str, Any]] = []
    for key, group in df.groupby("underlying_key", dropna=True):
        end_dates = pd.to_numeric(group.get("end_date"), errors="coerce") if "end_date" in group else pd.Series(dtype=float)
        strikes = group.get("strike_price", pd.Series(dtype=float))
        items.append(
            {
                "underlying_key": key,
                "underlying_ins_code": _serialize_value(
                    _first_present(group.get("underlying_ins_code", pd.Series(dtype=object))),
                    "underlying_ins_code",
                ),
                "underlying_symbol": _first_present(group.get("underlying_symbol", pd.Series(dtype=object))),
                "underlying_short_name": _first_present(group.get("underlying_short_name", pd.Series(dtype=object))),
                "underlying_last_price": _first_present(group.get("underlying_last_price", pd.Series(dtype=object))),
                "underlying_closing_price": _first_present(group.get("underlying_closing_price", pd.Series(dtype=object))),
                "contract_count": int(group.shape[0]),
                "call_count": int((group.get("option_type") == "call").sum()) if "option_type" in group else 0,
                "put_count": int((group.get("option_type") == "put").sum()) if "option_type" in group else 0,
                "nearest_end_date": None if end_dates.empty or pd.isna(end_dates.min()) else int(end_dates.min()),
                "latest_end_date": None if end_dates.empty or pd.isna(end_dates.max()) else int(end_dates.max()),
                "min_strike_price": _min_or_none(strikes),
                "max_strike_price": _max_or_none(strikes),
                "trade_volume": _sum_or_none(group.get("trade_volume", pd.Series(dtype=float))),
                "trade_value": _sum_or_none(group.get("trade_value", pd.Series(dtype=float))),
                "open_interest": _sum_or_none(group.get("buy_open_positions", pd.Series(dtype=float))),
                "natural_money_flow": _sum_or_none(group.get("natural_money_flow", pd.Series(dtype=float))),
                "legal_money_flow": _sum_or_none(group.get("legal_money_flow", pd.Series(dtype=float))),
                "updated_at": _first_present(group.get("updated_at", pd.Series(dtype=object))),
            }
        )

    items.sort(key=lambda item: str(item.get("underlying_symbol") or ""))
    return {"items": items, "total": len(items)}


def get_underlying_contracts(storage: Storage, underlying_key: str, q: Optional[str] = None) -> Dict[str, Any]:
    merged = get_merged_contracts(storage)
    if merged.empty:
        return {"items": [], "total": 0, "underlying": None}

    df = merged.copy()
    df["underlying_key"] = df.apply(_underlying_key, axis=1)
    df = df[df["underlying_key"] == str(underlying_key)]
    if q:
        df = df[_text_mask(df, ("symbol", "short_name", "long_name"), q)]

    underlying = None
    if not df.empty:
        underlying = {
            "underlying_key": str(underlying_key),
            "underlying_ins_code": _serialize_value(
                _first_present(df.get("underlying_ins_code", pd.Series(dtype=object))),
                "underlying_ins_code",
            ),
            "underlying_symbol": _first_present(df.get("underlying_symbol", pd.Series(dtype=object))),
            "underlying_short_name": _first_present(df.get("underlying_short_name", pd.Series(dtype=object))),
            "underlying_last_price": _first_present(df.get("underlying_last_price", pd.Series(dtype=object))),
            "underlying_closing_price": _first_present(df.get("underlying_closing_price", pd.Series(dtype=object))),
        }
    return {"items": _df_to_records(df), "total": len(df), "underlying": underlying}


def get_summary(storage: Storage) -> Dict[str, Any]:
    merged = get_merged_contracts(storage)
    contracts = storage.get_contracts_df()
    last_update = None
    if not contracts.empty and "updated_at" in contracts.columns:
        last_update = contracts["updated_at"].max()
    summary: Dict[str, Any] = {
        "contract_count": len(contracts),
        "underlying_count": 0,
        "call_count": 0,
        "put_count": 0,
        "total_trade_volume": None,
        "total_trade_value": None,
        "last_update": _serialize_value(last_update),
        "total_natural_flow": None,
        "total_legal_flow": None,
        "total_buy_oi": None,
        "total_sell_oi": None,
    }
    if not merged.empty:
        if "natural_money_flow" in merged.columns:
            value = merged["natural_money_flow"].sum(min_count=1)
            summary["total_natural_flow"] = None if pd.isna(value) else float(value)
        if "legal_money_flow" in merged.columns:
            value = merged["legal_money_flow"].sum(min_count=1)
            summary["total_legal_flow"] = None if pd.isna(value) else float(value)
        if "buy_open_positions" in merged.columns:
            value = merged["buy_open_positions"].sum(min_count=1)
            summary["total_buy_oi"] = None if pd.isna(value) else float(value)
        if "sell_open_positions" in merged.columns:
            value = merged["sell_open_positions"].sum(min_count=1)
            summary["total_sell_oi"] = None if pd.isna(value) else float(value)
        if "underlying_symbol" in merged.columns:
            summary["underlying_count"] = int(merged["underlying_symbol"].dropna().nunique())
        if "option_type" in merged.columns:
            summary["call_count"] = int((merged["option_type"] == "call").sum())
            summary["put_count"] = int((merged["option_type"] == "put").sum())
        if "trade_volume" in merged.columns:
            summary["total_trade_volume"] = _sum_or_none(merged["trade_volume"])
        if "trade_value" in merged.columns:
            summary["total_trade_value"] = _sum_or_none(merged["trade_value"])
    return summary


def get_sentiment(storage: Storage, q: Optional[str] = None) -> Dict[str, Any]:
    merged = get_merged_contracts(storage)
    result = analyze_options_sentiment(merged)
    items = result["items"]
    if q:
        q_lower = _normalize_text(q)
        items = [
            item
            for item in items
            if q_lower in _normalize_text(item.get("underlying_symbol"))
            or q_lower in _normalize_text(item.get("underlying_ins_code"))
            or q_lower in _normalize_text(item.get("sentiment_label"))
        ]
    return {
        "items": items,
        "total": len(items),
        "summary": result["summary"],
    }
