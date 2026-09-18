"""Streamlit briefing dashboard — Rail Ops Briefing DSS."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.recommend import briefing_recommendations
from src.synthetic_kpis import apply_whatif, generate_ops_panel

st.set_page_config(page_title="Rail Ops Briefing DSS", layout="wide")
st.title("Rail Ops Briefing DSS｜鐵道營運簡報決策輔助")
st.caption(
    "合成 KPI 面板｜延誤風險／擁擠代理指標｜What-if 槓桿｜規則式建議 — "
    "學習向示範（與臺鐵數據力企劃相關研究脈絡；**未宣稱得獎**）"
)

with st.sidebar:
    st.header("資料與槓桿")
    n_days = st.slider("模擬天數", 7, 30, 14)
    seed = st.number_input("種子", 0, 9999, 42)
    st.markdown("---")
    st.subheader("What-if")
    add_cars = st.slider("加掛／運能提升", 0.0, 0.30, 0.0, 0.05, help="額外運能比例")
    buffer = st.slider("調度緩衝（分）", 0.0, 10.0, 0.0, 0.5)
    demand_shift = st.slider("尖峰需求轉移", 0.0, 0.20, 0.0, 0.02, help="尖峰需求移出比例")
    apply = st.button("重新產生／套用", type="primary")

if apply or "panel" not in st.session_state:
    base = generate_ops_panel(n_days=n_days, seed=int(seed))
    st.session_state["base"] = base
    st.session_state["panel"] = apply_whatif(
        base, add_cars=add_cars, dispatch_buffer_min=buffer, demand_shift=demand_shift
    )

panel: pd.DataFrame = st.session_state["panel"]
base: pd.DataFrame = st.session_state["base"]

# KPI strip (latest day)
latest_day = panel["date"].max()
today = panel[panel["date"] == latest_day]
c1, c2, c3, c4 = st.columns(4)
c1.metric("當日平均延誤風險", f"{today['delay_risk'].mean():.1%}")
c2.metric("當日平均擁擠度", f"{today['crowding'].mean():.1%}")
c3.metric("當日平均準點率 OTP", f"{today['otp'].mean():.1%}")
c4.metric("當日平均延誤(分)", f"{today['avg_delay_min'].mean():.1f}")

left, right = st.columns(2)
with left:
    st.subheader("路線 × 尖離峰：延誤風險熱力")
    heat = today.pivot_table(index="line", columns="peak", values="delay_risk", aggfunc="mean")
    fig = px.imshow(heat, text_auto=".2f", aspect="auto", color_continuous_scale="YlOrRd")
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("擁擠度 vs 延誤風險（當日）")
    fig2 = px.scatter(
        today,
        x="crowding",
        y="delay_risk",
        color="line",
        size="ridership",
        hover_data=["peak", "otp"],
    )
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("規則式簡報建議（最新一日）")
recs = briefing_recommendations(panel, top_n=5)
st.dataframe(pd.DataFrame(recs), use_container_width=True)

with st.expander("What-if 效果對照（相對基準面板）"):
    cmp = pd.DataFrame(
        {
            "指標": ["平均延誤風險", "平均擁擠度", "平均 OTP", "平均延誤(分)"],
            "基準": [
                base["delay_risk"].mean(),
                base["crowding"].mean(),
                base["otp"].mean(),
                base["avg_delay_min"].mean(),
            ],
            "What-if 後": [
                panel["delay_risk"].mean(),
                panel["crowding"].mean(),
                panel["otp"].mean(),
                panel["avg_delay_min"].mean(),
            ],
        }
    )
    st.dataframe(cmp, use_container_width=True)

st.info(
    "本儀表板使用**合成資料**與**可解釋規則**，目的是展示鐵道營運簡報／決策支援的資訊架構與互動槓桿。"
    "與「臺鐵數據力」相關研究為學習脈絡延伸，**不宣稱競賽得獎或正式營運採用**。"
)
