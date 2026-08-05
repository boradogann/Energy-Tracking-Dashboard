import time
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Enerji Takip Dashboard", page_icon="⚡", layout="wide"
)

st.title("⚡ Akıllı Enerji Tüketim Dashboard'u")
st.caption("Gerçek Zamanlı Kaggle Sensör Akışı & Anomali Tespit Sistemi")


# Veriyi İnternet Kaynağından Çeken Fonksiyon
@st.cache_data
def load_data():
    url = "https://archive.ics.uci.edu/static/public/235/individual+household+electric+power+consumption.zip"
    df = pd.read_csv(
        url,
        sep=";",
        compression="zip",
        low_memory=False,
        na_values=["?"],
        nrows=10000,
    )
    df.ffill(inplace=True)
    df["Timestamp"] = pd.to_datetime(
        df["Date"] + " " + df["Time"], format="%d/%m/%Y %H:%M:%S"
    )
    for c in ["Global_active_power", "Voltage", "Global_intensity"]:
        df[c] = df[c].astype(float)
    return df


try:
    with st.spinner("Enerji veri seti yükleniyor..."):
        energy_df = load_data()
except Exception as e:
    st.error(f"Veri kaynağına bağlanılamadı: {e}")
    energy_df = None

if energy_df is not None:
    col1, col2, col3 = st.columns(3)
    status_metric = col1.empty()
    power_metric = col2.empty()
    voltage_metric = col3.empty()
    chart_spot = st.empty()

    # 1. Grafiği tamamen BOŞ (0 noktasında) başlatıyoruz
    if "history" not in st.session_state:
        st.session_state.history = {"time": [], "power": []}

    # 2. Döngüyü en baştan (0. veriden) başlatıyoruz
    for index in range(len(energy_df)):
        row = energy_df.iloc[index]
        time_str = row["Timestamp"].strftime("%H:%M:%S")
        power_val = float(row["Global_active_power"])
        voltage_val = float(row["Voltage"])

        # Veriyi ekle
        st.session_state.history["time"].append(time_str)
        st.session_state.history["power"].append(power_val)

        # Ekran dolana kadar (son 25 nokta) grafiği genişlet, 25'ten sonra kaydır
        if len(st.session_state.history["time"]) > 25:
            st.session_state.history["time"].pop(0)
            st.session_state.history["power"].pop(0)

        # Metrik Güncelleme
        if power_val > 4.0:
            status_metric.error("⚠️ YÜKSEK TÜKETİM ALARMI!")
        else:
            status_metric.success("✅ NORMAL ÇALIŞMA")

        power_metric.subheader(f"⚡ Aktif Güç: {power_val:.2f} kW")
        voltage_metric.subheader(f"🔌 Gerilim: {voltage_val:.1f} V")

        # 3. Canlı Grafik
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=st.session_state.history["time"],
                y=st.session_state.history["power"],
                mode="lines+markers",
                line=dict(color="#38bdf8", width=3),
                fill="tozeroy",
                fillcolor="rgba(56, 189, 248, 0.1)",
            )
        )

        fig.update_layout(
            template="plotly_dark",
            height=380,
            margin=dict(l=20, r=20, t=30, b=20),
            xaxis_title="Zaman",
            yaxis_title="Aktif Güç (kW)",
            # Y ekseni ölçeği veri geldikçe bozulmasın diye sabit alan
            yaxis=dict(range=[0, max(max(st.session_state.history["power"], default=1) + 1, 6)]),
        )

        chart_spot.plotly_chart(fig, use_container_width=True)
        time.sleep(0.5)
