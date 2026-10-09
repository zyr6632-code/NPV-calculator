"""NPV 投资经济性评价 — Streamlit Community Cloud 部署版。"""
import csv
import io

import pandas as pd
import streamlit as st

st.set_page_config(page_title="NPV投资经济性评价", page_icon="📈", layout="wide")

st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #eaf3ff 0%, #f4faff 100%); }
.block-container { max-width: 1300px; padding-top: 2.2rem; padding-bottom: 2rem; }
h1, h2, h3 { color: #134982 !important; }
[data-testid="stNumberInput"] input { border-radius: 10px; }
[data-testid="stButton"] button[kind="primary"] {
    background: linear-gradient(90deg, #156ade, #084bb8);
    border: none; border-radius: 11px; color: #fff; font-weight: 700;
}
.metric-panel {
    border-radius: 18px;
    padding: 26px 28px;
    border: 1px solid #cadfff;
    background: linear-gradient(120deg, #fff 0%, #e8f3ff 100%);
    min-height: 180px;
    box-shadow: 0 6px 20px rgba(30, 88, 160, 0.06);
}
.metric-label { color: #5b7b99; font-size: 17px; font-weight: 600; }
.metric-value { color: #1250a0; font-size: 40px; font-weight: 800; margin: 17px 0; }
.metric-note { font-size: 16px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)


def npv_and_discounted(investment: float, rate_percent: float, flows: list[float]):
    r = rate_percent / 100.0
    discounted = [amount / (1 + r) ** year for year, amount in enumerate(flows, 1)]
    return sum(discounted) - investment, discounted


def simple_payback(investment: float, flows: list[float]):
    """首个回收点的静态回收期；每年内按均匀发生的现金流插值。"""
    if investment <= 0:
        return 0.0
    cumulative = -investment
    for year, amount in enumerate(flows, 1):
        previous = cumulative
        cumulative += amount
        if previous < 0 <= cumulative and amount > 0:
            return year - 1 + (-previous) / amount
    return None


@st.dialog("NPV计算明细与现金流可视化", width="large")
def show_detail(investment: float, rate_percent: float, flows: list[float]):
    npv, discounted = npv_and_discounted(investment, rate_percent, flows)
    years = [f"第{i}年" for i in range(1, len(flows) + 1)]
    detail = pd.DataFrame({
        "年份": years,
        "净现金流量（万元）": flows,
        "折现值（万元）": discounted,
    })
    st.markdown("### 现金流量折现明细")
    st.dataframe(
        detail,
        hide_index=True,
        width="stretch",
        column_config={
            "净现金流量（万元）": st.column_config.NumberColumn(format="%.2f"),
            "折现值（万元）": st.column_config.NumberColumn(format="%.2f"),
        },
    )
    st.markdown("### 年度现金流量与折现值对比")
    chart_data = pd.DataFrame({
        "年份": years,
        "净现金流量": flows,
        "折现值": discounted,
    })
    st.bar_chart(
        chart_data,
        x="年份", y=["净现金流量", "折现值"],
        color=["#165ac5", "#80c5f8"], stack=False, height=330,
    )
    st.caption("单位：万元。深蓝为当年净现金流量，浅蓝为折现值；两者是比较关系，不应相加。")
    st.write(f"**初始投资：** {investment:.2f} 万元　　**折现率：** {rate_percent:.1f}%")
    label = "满足基准收益要求" if npv >= 0 else "未满足基准收益要求"
    st.write(f"**净现值（NPV）：{npv:.2f} 万元** · {label}")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["年份", "净现金流量（万元）", "折现值（万元）"])
    for year, cash, present in zip(years, flows, discounted):
        writer.writerow([year, f"{cash:.2f}", f"{present:.2f}"])
    st.download_button(
        "导出 CSV 明细", data=output.getvalue().encode("utf-8-sig"),
        file_name="NPV现金流量明细.csv", mime="text/csv",
    )


st.title("NPV投资经济性评价")
st.subheader("投资参数设置")
left, right = st.columns(2)
with left:
    investment = st.number_input("初始投资（万元）", min_value=0.0, value=200.0, step=10.0)
with right:
    rate_percent = st.slider("折现率（%）", min_value=0, max_value=25, value=10, step=1)

st.subheader("年度净现金流量（万元）")
columns = st.columns(5)
flows = []
for index, (column, initial) in enumerate(zip(columns, [60.0, 80.0, 90.0, 100.0, 101.0]), 1):
    with column:
        flows.append(st.number_input(f"第{index}年", value=initial, step=1.0, key=f"flow_{index}"))

# 即使没有点击按钮，两张评价卡片也随输入实时更新。
npv, _ = npv_and_discounted(investment, rate_percent, flows)
payback = simple_payback(investment, flows)
if npv > 1e-9:
    label, color = "满足基准收益要求", "#0a9b60"
elif npv < -1e-9:
    label, color = "未满足基准收益要求", "#d84b46"
else:
    label, color = "恰好达到基准收益要求", "#ba8716"

st.subheader("投资经济性评价")
left_result, right_result = st.columns(2)
with left_result:
    st.markdown(
        f'<div class="metric-panel"><div class="metric-label">净现值 NPV</div>'
        f'<div class="metric-value">{npv:,.2f} 万元</div>'
        f'<div class="metric-note" style="color:{color};">{label}</div></div>',
        unsafe_allow_html=True,
    )
with right_result:
    display_payback = f"{payback:.2f} 年" if payback is not None else "项目期内未回收"
    st.markdown(
        f'<div class="metric-panel"><div class="metric-label">静态投资回收期</div>'
        f'<div class="metric-value">{display_payback}</div>'
        '<div class="metric-note" style="color:#0a9b60;">不考虑资金时间价值</div></div>',
        unsafe_allow_html=True,
    )

st.write("")
if st.button("计算 NPV · 查看表格与柱状图", type="primary"):
    show_detail(investment, rate_percent, flows)

st.caption("模拟测算：初始投资发生于第0年，每年净现金流量视为年末发生；未计项目期末残值。请勿将会计利润直接当作现金流量。")
