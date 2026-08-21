"""Mock end-to-end pipeline test (no live API credentials required)."""

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from src.pipeline import run_pipeline
from src.storage import Storage


def test_pipeline_with_mock_api() -> dict:
    mock_options = [
        {
            "InsCode": 1001,
            "InstrumentID": "OPT001",
            "BuyOP": 500,
            "SellOP": 300,
            "YesterdayOP": 450,
            "ContractSize": 1000,
            "StrikePrice": 12000,
            "UAInsCode": 2001,
            "BeginDate": 20250101,
            "EndDate": 20250630,
            "AFactor": 1.0,
            "BFactor": 1.0,
            "CFactor": 1.0,
        }
    ]
    mock_instruments = [
        {
            "InsCode": 1001,
            "CValMne": "ضخود1230",
            "LVal18": "اختیارخ",
            "LVal30": "اختیار خرید خودرو",
            "CIsin": "IRTEST001",
            "YMarNSC": "بازار مشتقه",
            "CGdSVal": "خودرو",
        }
    ]
    mock_client_type = [
        {
            "RecDate": 20250614,
            "InsCode": 1001,
            "Buy_N_Volume": 1000,
            "Buy_I_Volume": 5000,
            "Buy_N_Value": 1_000_000,
            "Buy_I_Value": 5_000_000,
            "Buy_Count_ClientN": 10,
            "Buy_Count_ClientI": 2,
            "Sell_N_Volume": 800,
            "Sell_I_Volume": 4000,
            "Sell_N_Value": 800_000,
            "Sell_I_Value": 4_000_000,
            "Sell_Count_ClientN": 8,
            "Sell_Count_ClientI": 1,
        }
    ]
    mock_trades = [
        {
            "InsCode": 1001,
            "DEven": 20250614,
            "LVal18AFC": "اختیارخ",
            "LVal30": "اختیار خرید",
            "ZTotTran": 50,
            "QTotTran5J": 10000,
            "QTotCap": 120_000_000,
            "PClosing": 1200,
            "PDrCotVal": 1210,
            "PriceChange": "+10",
            "PriceMin": 1180,
            "PriceMax": 1220,
            "PriceFirst": 1190,
            "PriceYesterday": 1200,
        }
    ]

    client = MagicMock()
    client.login.return_value = "mock-token"

    def mock_call(endpoint_key, json_body=None):
        mapping = {
            "option": mock_options,
            "instrument": mock_instruments,
            "trade_last_day": mock_trades,
            "client_type_by_ins": mock_client_type,
        }
        return mapping.get(endpoint_key, [])

    client.call = mock_call

    with TemporaryDirectory() as tmp:
        storage = Storage(
            db_path=Path(tmp) / "test_options.db",
            export_dir=Path(tmp) / "exports",
        )
        with patch("src.pipeline.validate_credentials"), patch(
            "src.pipeline.TsetmcClient", return_value=client
        ), patch("src.pipeline.Storage", return_value=storage):
            return run_pipeline(limit=None, skip_client_type=False, delay_between_calls=0)


if __name__ == "__main__":
    result = test_pipeline_with_mock_api()
    print("Mock pipeline result:", result)
