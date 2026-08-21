"""Streamlit dashboard for TSETMC options data."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.analysis.sentiment import analyze_options_sentiment
from src.storage import Storage

st.set_page_config(
    page_title="TSETMC Options Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("TSETMC Options Data Dashboard")
st.caption("داده‌های اختیار معامله از وب‌سرویس رسمی api.tsetmc.com")

storage = Storage()
contracts_df = storage.get_contracts_df()
client_type_df = storage.get_latest_client_type_df()
oi_history_df = storage.get_open_interest_history_df()


def _fmt_num(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "-"
    if isinstance(val, (int, float)):
        return f"{val:,.0f}"
    return str(val)


def _color_flow(val) -> str:
    if val is None or pd.isna(val):
        return ""
    if val > 0:
        return "background-color: #d4edda; color: #155724"
    if val < 0:
        return "background-color: #f8d7da; color: #721c24"
    return ""


if contracts_df.empty:
    st.warning(
        "هنوز داده‌ای در دیتابیس نیست. ابتدا pipeline را اجرا کنید:\n\n"
        "`python -m src.pipeline`"
    )
    st.stop()

merged = contracts_df.copy()
if not client_type_df.empty:
    ct_cols = [
        "ins_code",
        "rec_date",
        "natural_buy_volume",
        "natural_buy_value",
        "natural_buy_count",
        "natural_sell_volume",
        "natural_sell_value",
        "natural_sell_count",
        "legal_buy_volume",
        "legal_buy_value",
        "legal_buy_count",
        "legal_sell_volume",
        "legal_sell_value",
        "legal_sell_count",
        "natural_money_flow",
        "legal_money_flow",
    ]
    merged = merged.merge(
        client_type_df[ct_cols],
        on="ins_code",
        how="left",
    )

sentiment_result = analyze_options_sentiment(merged)

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "همه قراردادها",
        "موقعیت‌های باز",
        "ورود/خروج پول",
        "خرید/فروش حقیقی و حقوقی",
        "سنتیمنت",
    ]
)

with tab1:
    st.subheader("همه اطلاعات قراردادهای اختیار معامله")
    display_cols = [
        "symbol",
        "short_name",
        "ins_code",
        "strike_price",
        "end_date",
        "contract_size",
        "last_price",
        "closing_price",
        "trade_volume",
        "trade_value",
        "buy_open_positions",
        "sell_open_positions",
        "underlying_ins_code",
        "market_name",
        "updated_at",
    ]
    cols = [c for c in display_cols if c in merged.columns]
    st.dataframe(merged[cols], use_container_width=True, height=500)
    st.download_button(
        "دانلود CSV",
        merged.to_csv(index=False).encode("utf-8-sig"),
        file_name="all_contracts.csv",
        mime="text/csv",
    )

with tab2:
    st.subheader("موقعیت‌های باز هر اپشن")
    oi_cols = [
        "symbol",
        "short_name",
        "ins_code",
        "buy_open_positions",
        "sell_open_positions",
        "yesterday_open_positions",
        "strike_price",
        "end_date",
    ]
    oi_view = merged[[c for c in oi_cols if c in merged.columns]].copy()
    st.dataframe(oi_view, use_container_width=True, height=400)

    if not oi_history_df.empty and "symbol" in merged.columns:
        symbols = merged[["ins_code", "symbol"]].dropna()
        symbol_map = dict(zip(symbols["ins_code"], symbols["symbol"]))
        selected = st.selectbox(
            "انتخاب نماد برای نمودار روند",
            options=sorted(symbol_map.keys()),
            format_func=lambda x: f"{symbol_map.get(x, x)} ({x})",
        )
        hist = oi_history_df[oi_history_df["ins_code"] == selected].sort_values("fetched_at")
        if not hist.empty:
            chart_df = hist.set_index("fetched_at")[
                ["buy_open_positions", "sell_open_positions"]
            ]
            st.line_chart(chart_df)
        else:
            st.info("تاریخچه موقعیت باز برای این نماد موجود نیست.")

with tab3:
    st.subheader("ورود و خروج پول حقیقی و حقوقی")
    if "natural_money_flow" not in merged.columns:
        st.info("داده جریان پول موجود نیست. pipeline را با client type اجرا کنید.")
    else:
        flow_cols = [
            "symbol",
            "short_name",
            "ins_code",
            "natural_money_flow",
            "legal_money_flow",
            "rec_date",
        ]
        flow_view = merged[[c for c in flow_cols if c in merged.columns]].copy()

        styled = flow_view.style.map(
            _color_flow,
            subset=[c for c in ["natural_money_flow", "legal_money_flow"] if c in flow_view.columns],
        )
        st.dataframe(styled, use_container_width=True, height=400)

        st.caption(
            "ورود پول = ارزش خرید − ارزش فروش | "
            "مثبت = ورود پول | منفی = خروج پول"
        )

        summary = pd.DataFrame(
            {
                "نوع": ["حقیقی", "حقوقی"],
                "جمع خالص جریان پول": [
                    flow_view["natural_money_flow"].sum(),
                    flow_view["legal_money_flow"].sum(),
                ],
            }
        )
        st.bar_chart(summary.set_index("نوع"))

with tab4:
    st.subheader("اطلاعات عددی خرید و فروش حقیقی و حقوقی")
    if client_type_df.empty:
        st.info("داده client type موجود نیست.")
    else:
        detail_cols = [
            "symbol",
            "short_name",
            "ins_code",
            "natural_buy_count",
            "natural_buy_volume",
            "natural_buy_value",
            "natural_sell_count",
            "natural_sell_volume",
            "natural_sell_value",
            "legal_buy_count",
            "legal_buy_volume",
            "legal_buy_value",
            "legal_sell_count",
            "legal_sell_volume",
            "legal_sell_value",
        ]
        if "symbol" in merged.columns:
            detail_view = merged[[c for c in detail_cols if c in merged.columns]]
        else:
            detail_view = client_type_df

        st.dataframe(detail_view, use_container_width=True, height=500)

        selected_ins = st.selectbox(
            "جزئیات یک قرارداد",
            options=merged["ins_code"].tolist(),
            format_func=lambda x: (
                f"{merged.loc[merged['ins_code'] == x, 'symbol'].iloc[0]} ({x})"
                if "symbol" in merged.columns and not merged.loc[merged["ins_code"] == x, "symbol"].empty
                else str(x)
            ),
        )
        row = merged[merged["ins_code"] == selected_ins].iloc[0]

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### حقیقی")
            st.metric("تعداد خریدار", _fmt_num(row.get("natural_buy_count")))
            st.metric("حجم خرید", _fmt_num(row.get("natural_buy_volume")))
            st.metric("ارزش خرید", _fmt_num(row.get("natural_buy_value")))
            st.metric("تعداد فروشنده", _fmt_num(row.get("natural_sell_count")))
            st.metric("حجم فروش", _fmt_num(row.get("natural_sell_volume")))
            st.metric("ارزش فروش", _fmt_num(row.get("natural_sell_value")))
        with col2:
            st.markdown("### حقوقی")
            st.metric("تعداد خریدار", _fmt_num(row.get("legal_buy_count")))
            st.metric("حجم خرید", _fmt_num(row.get("legal_buy_volume")))
            st.metric("ارزش خرید", _fmt_num(row.get("legal_buy_value")))
            st.metric("تعداد فروشنده", _fmt_num(row.get("legal_sell_count")))
            st.metric("حجم فروش", _fmt_num(row.get("legal_sell_volume")))
            st.metric("ارزش فروش", _fmt_num(row.get("legal_sell_value")))

with tab5:
    st.subheader("تحلیل سنتیمنت اختیار معامله")
    sentiment_items = sentiment_result["items"]
    if not sentiment_items:
        st.info("داده کافی برای تحلیل سنتیمنت موجود نیست.")
    else:
        summary = sentiment_result["summary"]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("گروه‌ها", _fmt_num(summary.get("group_count")))
        col2.metric("صعودی", _fmt_num(summary.get("bullish") + summary.get("cautious_bullish")))
        col3.metric("نزولی", _fmt_num(summary.get("bearish")))
        col4.metric("میانگین اعتبار", _fmt_num(summary.get("average_confidence")))

        sentiment_df = pd.DataFrame(sentiment_items)
        sentiment_df["reasons"] = sentiment_df["reasons"].apply(lambda rows: "، ".join(rows or []))
        sentiment_df["warnings"] = sentiment_df["warnings"].apply(lambda rows: "، ".join(rows or []))
        display_cols = [
            "underlying_symbol",
            "underlying_ins_code",
            "end_date",
            "sentiment_label",
            "confidence",
            "call_put_ratio",
            "call_buy_volume",
            "call_sell_volume",
            "put_buy_volume",
            "put_sell_volume",
            "call_otm_share",
            "open_interest_change",
            "reasons",
            "warnings",
        ]
        st.dataframe(
            sentiment_df[[c for c in display_cols if c in sentiment_df.columns]],
            use_container_width=True,
            height=500,
        )

st.sidebar.markdown("### آمار")
st.sidebar.metric("تعداد قراردادها", len(contracts_df))
if not client_type_df.empty:
    st.sidebar.metric("رکورد client type", len(client_type_df))
st.sidebar.markdown("---")
st.sidebar.markdown(
    "برای به‌روزرسانی داده:\n`python -m src.pipeline`"
)
