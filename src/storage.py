"""SQLite storage and CSV export."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
    inspect,
    select,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.config import DATA_DIR, DATABASE_PATH

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


class Contract(Base):
    __tablename__ = "contracts"

    ins_code = Column(Integer, primary_key=True)
    instrument_id = Column(String(64), nullable=True)
    option_type = Column(String(16), nullable=True)
    symbol = Column(String(128), nullable=True)
    short_name = Column(String(256), nullable=True)
    long_name = Column(String(512), nullable=True)
    isin = Column(String(32), nullable=True)
    buy_open_positions = Column(Float, nullable=True)
    sell_open_positions = Column(Float, nullable=True)
    yesterday_open_positions = Column(Float, nullable=True)
    contract_size = Column(Float, nullable=True)
    strike_price = Column(Float, nullable=True)
    underlying_ins_code = Column(Integer, nullable=True)
    underlying_symbol = Column(String(128), nullable=True)
    underlying_short_name = Column(String(256), nullable=True)
    underlying_last_price = Column(Float, nullable=True)
    underlying_closing_price = Column(Float, nullable=True)
    moneyness = Column(String(16), nullable=True)
    intrinsic_value = Column(Float, nullable=True)
    begin_date = Column(Integer, nullable=True)
    end_date = Column(Integer, nullable=True)
    a_factor = Column(Float, nullable=True)
    b_factor = Column(Float, nullable=True)
    c_factor = Column(Float, nullable=True)
    market_name = Column(String(256), nullable=True)
    sector = Column(String(256), nullable=True)
    last_price = Column(Float, nullable=True)
    closing_price = Column(Float, nullable=True)
    price_change = Column(String(32), nullable=True)
    trade_volume = Column(Float, nullable=True)
    trade_value = Column(Float, nullable=True)
    trade_count = Column(Integer, nullable=True)
    price_min = Column(Float, nullable=True)
    price_max = Column(Float, nullable=True)
    instrument_json = Column(Text, nullable=True)
    fetched_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class OpenInterestSnapshot(Base):
    __tablename__ = "open_interest"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ins_code = Column(Integer, nullable=False, index=True)
    buy_open_positions = Column(Float, nullable=True)
    sell_open_positions = Column(Float, nullable=True)
    yesterday_open_positions = Column(Float, nullable=True)
    fetched_at = Column(DateTime, nullable=False, index=True)


class MoneyFlowSnapshot(Base):
    __tablename__ = "money_flow"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ins_code = Column(Integer, nullable=False, index=True)
    rec_date = Column(Integer, nullable=True)
    natural_money_flow = Column(Float, nullable=True)
    legal_money_flow = Column(Float, nullable=True)
    fetched_at = Column(DateTime, nullable=False, index=True)


class ClientTypeStats(Base):
    __tablename__ = "client_type_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ins_code = Column(Integer, nullable=False, index=True)
    rec_date = Column(Integer, nullable=True)
    natural_buy_volume = Column(Float, nullable=True)
    natural_buy_value = Column(Float, nullable=True)
    natural_buy_count = Column(Integer, nullable=True)
    natural_sell_volume = Column(Float, nullable=True)
    natural_sell_value = Column(Float, nullable=True)
    natural_sell_count = Column(Integer, nullable=True)
    legal_buy_volume = Column(Float, nullable=True)
    legal_buy_value = Column(Float, nullable=True)
    legal_buy_count = Column(Integer, nullable=True)
    legal_sell_volume = Column(Float, nullable=True)
    legal_sell_value = Column(Float, nullable=True)
    legal_sell_count = Column(Integer, nullable=True)
    natural_money_flow = Column(Float, nullable=True)
    legal_money_flow = Column(Float, nullable=True)
    fetched_at = Column(DateTime, nullable=False, index=True)


class Storage:
    def __init__(self, db_path: Optional[Path] = None, export_dir: Optional[Path] = None):
        self.db_path = db_path or DATABASE_PATH
        self.export_dir = export_dir or DATA_DIR
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        Base.metadata.create_all(self.engine)
        self._ensure_schema()
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def session(self) -> Session:
        return self.SessionLocal()

    def now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _ensure_schema(self) -> None:
        """Add lightweight columns for existing SQLite databases."""
        inspector = inspect(self.engine)
        if "contracts" not in inspector.get_table_names():
            return
        existing = {col["name"] for col in inspector.get_columns("contracts")}
        columns = {
            "option_type": "VARCHAR(16)",
            "underlying_symbol": "VARCHAR(128)",
            "underlying_short_name": "VARCHAR(256)",
            "underlying_last_price": "FLOAT",
            "underlying_closing_price": "FLOAT",
            "moneyness": "VARCHAR(16)",
            "intrinsic_value": "FLOAT",
        }
        missing = [(name, sql_type) for name, sql_type in columns.items() if name not in existing]
        if not missing:
            return
        with self.engine.begin() as conn:
            for name, sql_type in missing:
                conn.execute(text(f"ALTER TABLE contracts ADD COLUMN {name} {sql_type}"))

    def upsert_contracts(self, contracts: List[Dict[str, Any]]) -> int:
        now = self.now()
        count = 0
        with self.session() as session:
            for c in contracts:
                ins_code = c.get("ins_code")
                if not ins_code:
                    continue
                existing = session.get(Contract, ins_code)
                instrument_meta = c.get("instrument_meta")
                fields = {
                    "instrument_id": c.get("instrument_id"),
                    "option_type": c.get("option_type"),
                    "symbol": c.get("symbol"),
                    "short_name": c.get("short_name"),
                    "long_name": c.get("long_name"),
                    "isin": c.get("isin"),
                    "buy_open_positions": c.get("buy_open_positions"),
                    "sell_open_positions": c.get("sell_open_positions"),
                    "yesterday_open_positions": c.get("yesterday_open_positions"),
                    "contract_size": c.get("contract_size"),
                    "strike_price": c.get("strike_price"),
                    "underlying_ins_code": c.get("underlying_ins_code"),
                    "underlying_symbol": c.get("underlying_symbol"),
                    "underlying_short_name": c.get("underlying_short_name"),
                    "underlying_last_price": c.get("underlying_last_price"),
                    "underlying_closing_price": c.get("underlying_closing_price"),
                    "moneyness": c.get("moneyness"),
                    "intrinsic_value": c.get("intrinsic_value"),
                    "begin_date": c.get("begin_date"),
                    "end_date": c.get("end_date"),
                    "a_factor": c.get("a_factor"),
                    "b_factor": c.get("b_factor"),
                    "c_factor": c.get("c_factor"),
                    "market_name": c.get("market_name"),
                    "sector": c.get("sector"),
                    "last_price": c.get("last_price"),
                    "closing_price": c.get("closing_price"),
                    "price_change": c.get("price_change"),
                    "trade_volume": c.get("trade_volume"),
                    "trade_value": c.get("trade_value"),
                    "trade_count": c.get("trade_count"),
                    "price_min": c.get("price_min"),
                    "price_max": c.get("price_max"),
                    "instrument_json": json.dumps(instrument_meta, ensure_ascii=False)
                    if instrument_meta
                    else None,
                    "fetched_at": now,
                    "updated_at": now,
                }
                if existing:
                    for key, val in fields.items():
                        setattr(existing, key, val)
                else:
                    session.add(Contract(ins_code=ins_code, **fields))
                count += 1
            session.commit()
        return count

    def insert_open_interest(self, rows: List[Dict[str, Any]]) -> int:
        now = self.now()
        with self.session() as session:
            for row in rows:
                session.add(
                    OpenInterestSnapshot(
                        ins_code=row["ins_code"],
                        buy_open_positions=row.get("buy_open_positions"),
                        sell_open_positions=row.get("sell_open_positions"),
                        yesterday_open_positions=row.get("yesterday_open_positions"),
                        fetched_at=now,
                    )
                )
            session.commit()
        return len(rows)

    def insert_money_flow(self, rows: List[Dict[str, Any]]) -> int:
        now = self.now()
        with self.session() as session:
            for row in rows:
                session.add(
                    MoneyFlowSnapshot(
                        ins_code=row["ins_code"],
                        rec_date=row.get("rec_date"),
                        natural_money_flow=row.get("natural_money_flow"),
                        legal_money_flow=row.get("legal_money_flow"),
                        fetched_at=now,
                    )
                )
            session.commit()
        return len(rows)

    def insert_client_type_stats(self, rows: List[Dict[str, Any]]) -> int:
        now = self.now()
        with self.session() as session:
            for row in rows:
                session.add(
                    ClientTypeStats(
                        ins_code=row["ins_code"],
                        rec_date=row.get("rec_date"),
                        natural_buy_volume=row.get("natural_buy_volume"),
                        natural_buy_value=row.get("natural_buy_value"),
                        natural_buy_count=row.get("natural_buy_count"),
                        natural_sell_volume=row.get("natural_sell_volume"),
                        natural_sell_value=row.get("natural_sell_value"),
                        natural_sell_count=row.get("natural_sell_count"),
                        legal_buy_volume=row.get("legal_buy_volume"),
                        legal_buy_value=row.get("legal_buy_value"),
                        legal_buy_count=row.get("legal_buy_count"),
                        legal_sell_volume=row.get("legal_sell_volume"),
                        legal_sell_value=row.get("legal_sell_value"),
                        legal_sell_count=row.get("legal_sell_count"),
                        natural_money_flow=row.get("natural_money_flow"),
                        legal_money_flow=row.get("legal_money_flow"),
                        fetched_at=now,
                    )
                )
            session.commit()
        return len(rows)

    def get_contracts_df(self) -> pd.DataFrame:
        with self.session() as session:
            rows = session.scalars(select(Contract)).all()
            if not rows:
                return pd.DataFrame()
            return pd.DataFrame([self._contract_to_dict(r) for r in rows])

    def get_latest_client_type_df(self) -> pd.DataFrame:
        with self.session() as session:
            rows = session.scalars(select(ClientTypeStats)).all()
            if not rows:
                return pd.DataFrame()
            df = pd.DataFrame([self._client_type_to_dict(r) for r in rows])
            if "fetched_at" in df.columns:
                latest = df.groupby("ins_code")["fetched_at"].transform("max")
                df = df[df["fetched_at"] == latest]
            return df

    def get_open_interest_history_df(self, ins_code: Optional[int] = None) -> pd.DataFrame:
        with self.session() as session:
            rows = session.scalars(select(OpenInterestSnapshot)).all()
            if not rows:
                return pd.DataFrame()
            df = pd.DataFrame(
                [
                    {
                        "ins_code": r.ins_code,
                        "buy_open_positions": r.buy_open_positions,
                        "sell_open_positions": r.sell_open_positions,
                        "yesterday_open_positions": r.yesterday_open_positions,
                        "fetched_at": r.fetched_at,
                    }
                    for r in rows
                ]
            )
            if ins_code is not None:
                df = df[df["ins_code"] == ins_code]
            return df

    def export_csv(self, prefix: str = "") -> Dict[str, Path]:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = f"{prefix}_" if prefix else ""
        paths: Dict[str, Path] = {}

        contracts_df = self.get_contracts_df()
        if not contracts_df.empty:
            p = self.export_dir / f"{prefix}contracts_{timestamp}.csv"
            contracts_df.to_csv(p, index=False, encoding="utf-8-sig")
            paths["contracts"] = p

        ct_df = self.get_latest_client_type_df()
        if not ct_df.empty:
            p = self.export_dir / f"{prefix}client_type_stats_{timestamp}.csv"
            ct_df.to_csv(p, index=False, encoding="utf-8-sig")
            paths["client_type_stats"] = p

            mf = ct_df[
                ["ins_code", "rec_date", "natural_money_flow", "legal_money_flow", "fetched_at"]
            ].copy()
            p = self.export_dir / f"{prefix}money_flow_{timestamp}.csv"
            mf.to_csv(p, index=False, encoding="utf-8-sig")
            paths["money_flow"] = p

        oi_df = self.get_open_interest_history_df()
        if not oi_df.empty:
            latest_oi = oi_df.sort_values("fetched_at").groupby("ins_code").tail(1)
            p = self.export_dir / f"{prefix}open_interest_{timestamp}.csv"
            latest_oi.to_csv(p, index=False, encoding="utf-8-sig")
            paths["open_interest"] = p

        logger.info("Exported CSV files: %s", list(paths.keys()))
        return paths

    @staticmethod
    def _contract_to_dict(r: Contract) -> Dict[str, Any]:
        return {
            "ins_code": r.ins_code,
            "instrument_id": r.instrument_id,
            "option_type": r.option_type,
            "symbol": r.symbol,
            "short_name": r.short_name,
            "long_name": r.long_name,
            "isin": r.isin,
            "buy_open_positions": r.buy_open_positions,
            "sell_open_positions": r.sell_open_positions,
            "yesterday_open_positions": r.yesterday_open_positions,
            "contract_size": r.contract_size,
            "strike_price": r.strike_price,
            "underlying_ins_code": r.underlying_ins_code,
            "underlying_symbol": r.underlying_symbol,
            "underlying_short_name": r.underlying_short_name,
            "underlying_last_price": r.underlying_last_price,
            "underlying_closing_price": r.underlying_closing_price,
            "moneyness": r.moneyness,
            "intrinsic_value": r.intrinsic_value,
            "begin_date": r.begin_date,
            "end_date": r.end_date,
            "a_factor": r.a_factor,
            "b_factor": r.b_factor,
            "c_factor": r.c_factor,
            "market_name": r.market_name,
            "sector": r.sector,
            "last_price": r.last_price,
            "closing_price": r.closing_price,
            "price_change": r.price_change,
            "trade_volume": r.trade_volume,
            "trade_value": r.trade_value,
            "trade_count": r.trade_count,
            "price_min": r.price_min,
            "price_max": r.price_max,
            "fetched_at": r.fetched_at,
            "updated_at": r.updated_at,
        }

    @staticmethod
    def _client_type_to_dict(r: ClientTypeStats) -> Dict[str, Any]:
        return {
            "ins_code": r.ins_code,
            "rec_date": r.rec_date,
            "natural_buy_volume": r.natural_buy_volume,
            "natural_buy_value": r.natural_buy_value,
            "natural_buy_count": r.natural_buy_count,
            "natural_sell_volume": r.natural_sell_volume,
            "natural_sell_value": r.natural_sell_value,
            "natural_sell_count": r.natural_sell_count,
            "legal_buy_volume": r.legal_buy_volume,
            "legal_buy_value": r.legal_buy_value,
            "legal_buy_count": r.legal_buy_count,
            "legal_sell_volume": r.legal_sell_volume,
            "legal_sell_value": r.legal_sell_value,
            "legal_sell_count": r.legal_sell_count,
            "natural_money_flow": r.natural_money_flow,
            "legal_money_flow": r.legal_money_flow,
            "fetched_at": r.fetched_at,
        }
