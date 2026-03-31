import streamlit as st
import sqlite3
import pandas as pd
import time

# ─────────────────────────────────────────
# 警示門檻設定
# ─────────────────────────────────────────
TEMP_MAX  = 33.0   # 超過這個溫度 → 警示
HUMID_MIN = 45.0   # 低於這個濕度 → 警示
HUMID_MAX = 75.0   # 超過這個濕度 → 警示

# ─────────────────────────────────────────
# 頁面設定
# ─────────────────────────────────────────
st.set_page_config(page_title="AIoT Dashboard", layout="wide", page_icon="🌡️")

# 自訂 CSS：讓 KPI 卡片更好看
st.markdown("""
<style>
    .kpi-card {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 20px 24px;
        border-left: 4px solid #4C72B0;
        margin-bottom: 8px;
    }
    .kpi-card.warning {
        border-left: 4px solid #e74c3c;
        background: #fff5f5;
    }
    .kpi-label { font-size: 13px; color: #888; font-weight: 600; letter-spacing: 0.5px; }
    .kpi-value { font-size: 32px; font-weight: 700; color: #1a1a2e; margin: 4px 0; }
    .kpi-sub   { font-size: 12px; color: #aaa; }
    .badge-real { background:#d4edda; color:#155724; padding:2px 10px; border-radius:20px; font-size:12px; font-weight:600; }
    .badge-sim  { background:#d1ecf1; color:#0c5460; padding:2px 10px; border-radius:20px; font-size:12px; font-weight:600; }
    .alert-box  { background:#fff3cd; border-left:4px solid #ffc107; padding:12px 16px; border-radius:8px; margin:8px 0; }
    .alert-box.danger { background:#f8d7da; border-left:4px solid #e74c3c; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# 讀取資料庫
# ─────────────────────────────────────────
def load_data():
    conn = sqlite3.connect('aiotdb.db')
    df = pd.read_sql("SELECT * FROM sensors ORDER BY timestamp DESC", conn)
    conn.close()
    return df

df = load_data()

# ─────────────────────────────────────────
# 側邊欄
# ─────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Controls")

    source_filter = st.selectbox("Data Source", ["All", "simulated", "real"])

    st.divider()
    st.subheader("📊 Statistics")

    if not df.empty:
        real_count = len(df[df['source'] == 'real'])
        sim_count  = len(df[df['source'] == 'simulated'])
        st.markdown(f'<span class="badge-real">🔴 Real</span> &nbsp; **{real_count}** readings', unsafe_allow_html=True)
        st.markdown(f'<span class="badge-sim">🔵 Simulated</span> &nbsp; **{sim_count}** readings', unsafe_allow_html=True)

    st.divider()
    st.subheader("🚨 Alert Thresholds")
    st.caption(f"Temp > {TEMP_MAX}°C")
    st.caption(f"Humid < {HUMID_MIN}% or > {HUMID_MAX}%")

# ─────────────────────────────────────────
# 主畫面標題
# ─────────────────────────────────────────
st.title("🌡️ AIoT Sensor Dashboard")

if df.empty:
    st.warning("No data yet. Please start Flask and esp32_sim.py first.")
    st.stop()

# 套用 source 過濾
df_filtered = df if source_filter == "All" else df[df['source'] == source_filter]

if df_filtered.empty:
    st.info(f"No data from source: {source_filter}")
    st.stop()

# ─────────────────────────────────────────
# 最新一筆資料
# ─────────────────────────────────────────
latest      = df_filtered.iloc[0]
latest_time = pd.to_datetime(latest['timestamp'])
seconds_ago = int((pd.Timestamp.utcnow().replace(tzinfo=None) - latest_time).total_seconds())
latest_temp = float(latest['temperature'])
latest_humid= float(latest['humidity'])

# ─────────────────────────────────────────
# 警示區塊（有問題才顯示）
# ─────────────────────────────────────────
if latest_temp > TEMP_MAX:
    st.markdown(f'<div class="alert-box danger">🔥 High temperature alert: {latest_temp}°C (threshold: {TEMP_MAX}°C)</div>', unsafe_allow_html=True)
if latest_humid < HUMID_MIN:
    st.markdown(f'<div class="alert-box danger">💧 Low humidity alert: {latest_humid}% (threshold: {HUMID_MIN}%)</div>', unsafe_allow_html=True)
if latest_humid > HUMID_MAX:
    st.markdown(f'<div class="alert-box">💧 High humidity alert: {latest_humid}% (threshold: {HUMID_MAX}%)</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────
# KPI 卡片
# ─────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

temp_warning  = latest_temp > TEMP_MAX
humid_warning = latest_humid < HUMID_MIN or latest_humid > HUMID_MAX

with col1:
    card_class = "kpi-card warning" if temp_warning else "kpi-card"
    st.markdown(f"""
    <div class="{card_class}">
        <div class="kpi-label">TEMPERATURE</div>
        <div class="kpi-value">{latest_temp:.1f}°C</div>
        <div class="kpi-sub">avg {df_filtered['temperature'].mean():.1f}°C</div>
    </div>""", unsafe_allow_html=True)

with col2:
    card_class = "kpi-card warning" if humid_warning else "kpi-card"
    st.markdown(f"""
    <div class="{card_class}">
        <div class="kpi-label">HUMIDITY</div>
        <div class="kpi-value">{latest_humid:.1f}%</div>
        <div class="kpi-sub">avg {df_filtered['humidity'].mean():.1f}%</div>
    </div>""", unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">TOTAL READINGS</div>
        <div class="kpi-value">{len(df_filtered)}</div>
        <div class="kpi-sub">from {df_filtered['source'].nunique()} source(s)</div>
    </div>""", unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">LAST UPDATE</div>
        <div class="kpi-value" style="font-size:22px">{seconds_ago}s ago</div>
        <div class="kpi-sub">{latest['device_id']}</div>
    </div>""", unsafe_allow_html=True)

st.divider()

# ─────────────────────────────────────────
# 圖表：用不同顏色區分 real vs simulated
# ─────────────────────────────────────────
df_chart = df_filtered.copy()
df_chart['timestamp'] = pd.to_datetime(df_chart['timestamp'])
df_chart = df_chart.sort_values('timestamp')

# 把 real 和 simulated 拆成兩欄，這樣圖表才能分色
df_temp = df_chart.pivot_table(index='timestamp', columns='source', values='temperature', aggfunc='mean')
df_humid = df_chart.pivot_table(index='timestamp', columns='source', values='humidity', aggfunc='mean')

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("🌡️ Temperature Over Time")
    if not df_temp.empty:
        st.line_chart(df_temp, height=250)

with col_right:
    st.subheader("💧 Humidity Over Time")
    if not df_humid.empty:
        st.line_chart(df_humid, height=250)

st.divider()

# ─────────────────────────────────────────
# Raw data 表格
# ─────────────────────────────────────────
st.subheader("📋 Raw Data")
st.dataframe(
    df_filtered.head(100),
    use_container_width=True,
    hide_index=True
)

# ─────────────────────────────────────────
# 自動重整
# ─────────────────────────────────────────
st.caption("⏱ Auto-refreshing every 2 seconds")
time.sleep(2)
st.rerun()
