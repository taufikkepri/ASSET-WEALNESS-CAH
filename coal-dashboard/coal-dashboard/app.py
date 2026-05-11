"""
app.py — Asset Wellness Dashboard | Coal Handling System PLTU
Jalankan: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

from utils.loader import (
    load_master, load_wo, load_tren,
    summary_metrics, WELLNESS_COLOR, WELLNESS_BG
)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Asset Wellness | Coal Handling PLTU",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Fonts & base ─────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }

/* ── Sidebar ──────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #1F4E79;
    color: white;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] .stMarkdown { color: #CADDF2 !important; }
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #FFFFFF !important; }

/* ── KPI Card ─────────────────────────────────────────────── */
.kpi-card {
    background: white;
    border-radius: 10px;
    padding: 16px 20px;
    border-left: 4px solid #1F4E79;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
}
.kpi-label { font-size: 11px; font-weight: 600; letter-spacing: .06em;
             text-transform: uppercase; color: #6B7280; margin-bottom: 4px; }
.kpi-value { font-size: 28px; font-weight: 600; line-height: 1; color: #1A1A2E; }
.kpi-sub   { font-size: 11px; color: #9CA3AF; margin-top: 4px; }

/* ── Status badge ─────────────────────────────────────────── */
.badge-hijau  { background:#E8F5E9; color:#2D7D32; padding:2px 10px;
                border-radius:20px; font-size:12px; font-weight:600; }
.badge-kuning { background:#FFF8E1; color:#F57F17; padding:2px 10px;
                border-radius:20px; font-size:12px; font-weight:600; }
.badge-merah  { background:#FFEBEE; color:#C62828; padding:2px 10px;
                border-radius:20px; font-size:12px; font-weight:600; }

/* ── Section header ───────────────────────────────────────── */
.section-title { font-size: 13px; font-weight: 600; letter-spacing: .04em;
                 text-transform: uppercase; color: #6B7280;
                 border-bottom: 1px solid #E5E7EB; padding-bottom: 6px;
                 margin-bottom: 12px; }

/* ── Scrollable table ─────────────────────────────────────── */
.stDataFrame { border-radius: 8px; overflow: hidden; }

/* ── Top header bar ───────────────────────────────────────── */
.top-header {
    background: linear-gradient(135deg, #1F4E79 0%, #2E6DA4 100%);
    border-radius: 12px;
    padding: 20px 28px;
    margin-bottom: 20px;
    color: white;
}
.top-header h1 { font-size: 22px; font-weight: 600; margin: 0; color: white; }
.top-header p  { font-size: 13px; color: #CADDF2; margin: 4px 0 0; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_data(uploaded=None):
    if uploaded:
        return load_master(uploaded), load_wo(uploaded), load_tren(uploaded)
    return load_master(), load_wo(), load_tren()


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Coal Handling\n### Asset Wellness")
    st.markdown("---")

    uploaded = st.file_uploader(
        "📂 Upload file Excel (.xlsx)",
        type=["xlsx"],
        help="Upload file template Asset Wellness yang sudah diisi"
    )

    st.markdown("---")
    st.markdown("### Filter")

    df_master, df_wo, df_tren = get_data(uploaded)

    # Subsistem filter
    subsystems = ["Semua"] + sorted(df_master["subsistem"].dropna().unique().tolist())
    sel_sub = st.selectbox("Subsistem", subsystems)

    # Wellness filter
    sel_wellness = st.multiselect(
        "Status Wellness",
        ["Hijau", "Kuning", "Merah"],
        default=["Hijau", "Kuning", "Merah"]
    )

    st.markdown("---")
    st.markdown("### Navigasi")
    page = st.radio("Halaman", [
        "📊 Overview",
        "🔧 Detail Aset",
        "📋 Work Order",
        "📈 Tren Mingguan",
    ])

    st.markdown("---")
    st.caption("Asset Wellness Dashboard v1.0\nCoal Handling System PLTU")


# ── Filter dataframe ──────────────────────────────────────────────────────────
df = df_master.copy()
if sel_sub != "Semua":
    df = df[df["subsistem"] == sel_sub]
if sel_wellness:
    df = df[df["wellness"].isin(sel_wellness)]

metrics_all = summary_metrics(df_master)  # KPI cards always full data
metrics = summary_metrics(df) if (sel_sub != 'Semua' or len(sel_wellness) < 3) else metrics_all


# ─────────────────────────────────────────────────────────────────────────────
# ── PAGE: OVERVIEW ────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
if page == "📊 Overview":
    st.markdown("""
    <div class="top-header">
        <h1>Asset Wellness Dashboard</h1>
        <p>Coal Handling System PLTU · Minggu Berjalan</p>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI Row ───────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    kpis = [
        (c1, "Total Aset",     metrics["total"],       "#1F4E79", "unit"),
        (c2, "Status Hijau",   metrics["hijau"],        "#2D7D32", f"{metrics['hijau']/metrics['total']*100:.0f}% dari total"),
        (c3, "Status Kuning",  metrics["kuning"],       "#F57F17", "Perlu perhatian"),
        (c4, "Status Merah",   metrics["merah"],        "#C62828", "Kritis"),
        (c5, "Avg Wellness",   f"{metrics['avg_score']}",  "#1F4E79", "Skor 0–100"),
        (c6, "WO Aktif",       metrics["wo_open"],      "#7B2D8B", "Work order berjalan"),
    ]
    for col, label, val, color, sub in kpis:
        with col:
            st.markdown(f"""
            <div class="kpi-card" style="border-left-color:{color}">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value" style="color:{color}">{val}</div>
                <div class="kpi-sub">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Row 2: Donut + Bar subsistem ──────────────────────────────────────────
    col_left, col_right = st.columns([1, 2])
    color_map = {"Hijau": "#2D7D32", "Kuning": "#F9A825", "Merah": "#C62828"}
    df_ov = df.copy()  # pakai df yang sudah difilter

    with col_left:
        st.markdown('<div class="section-title">Distribusi Wellness</div>', unsafe_allow_html=True)
        wcount = df_ov["wellness"].value_counts().reset_index()
        wcount.columns = ["Wellness", "Jumlah"]
        fig_donut = px.pie(
            wcount, names="Wellness", values="Jumlah",
            color="Wellness", color_discrete_map=color_map,
            hole=0.55,
        )
        fig_donut.update_traces(textposition="outside", textinfo="percent+label",
                                textfont_size=12)
        fig_donut.update_layout(
            showlegend=False, margin=dict(t=10, b=10, l=10, r=10),
            height=260, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with col_right:
        st.markdown('<div class="section-title">Wellness per Subsistem</div>', unsafe_allow_html=True)
        sub_count = df_ov.groupby(["subsistem", "wellness"]).size().reset_index(name="n")
        fig_bar = px.bar(
            sub_count, x="subsistem", y="n", color="wellness",
            color_discrete_map=color_map,
            barmode="stack",
            labels={"subsistem": "", "n": "Jumlah Aset", "wellness": "Status"},
        )
        fig_bar.update_layout(
            margin=dict(t=10, b=60, l=10, r=10), height=260,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis_tickangle=-30,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # ── Row 3: Tabel aset non-Hijau + Gauge avg score ─────────────────────────
    col_tbl, col_gauge = st.columns([2, 1])

    with col_tbl:
        st.markdown('<div class="section-title">Aset Perlu Perhatian (Kuning & Merah)</div>',
                    unsafe_allow_html=True)
        df_warn = df_ov[df_ov["wellness"].isin(["Kuning", "Merah"])].copy()
        df_warn = df_warn.sort_values("wellness_rank")
        show_cols = ["asset_id", "deskripsi", "subsistem", "wellness",
                     "wellness_score", "kondisi", "wo_no", "wo_pic"]
        show_cols = [c for c in show_cols if c in df_warn.columns]

        def highlight_wellness(val):
            colors = {"Hijau": "background-color:#E8F5E9;color:#2D7D32",
                      "Kuning": "background-color:#FFF8E1;color:#F57F17",
                      "Merah": "background-color:#FFEBEE;color:#C62828"}
            return colors.get(val, "")

        if not df_warn.empty:
            styled = df_warn[show_cols].style.map(
                highlight_wellness, subset=["wellness"]
            )
            st.dataframe(styled, use_container_width=True, height=220)
        else:
            st.success("✅ Semua aset dalam status Hijau!")

    with col_gauge:
        st.markdown('<div class="section-title">Overall Wellness Score</div>',
                    unsafe_allow_html=True)
        avg = metrics["avg_score"]
        color_gauge = "#2D7D32" if avg >= 75 else ("#F9A825" if avg >= 50 else "#C62828")
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=avg,
            number={"suffix": "%", "font": {"size": 36, "color": color_gauge}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": color_gauge, "thickness": 0.25},
                "steps": [
                    {"range": [0, 40],  "color": "#FFEBEE"},
                    {"range": [40, 75], "color": "#FFF8E1"},
                    {"range": [75, 100],"color": "#E8F5E9"},
                ],
                "threshold": {"line": {"color": "#1F4E79", "width": 3},
                              "thickness": 0.85, "value": avg},
            },
        ))
        fig_gauge.update_layout(
            height=220, margin=dict(t=20, b=0, l=20, r=20),
            paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_gauge, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# ── PAGE: DETAIL ASET ────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
elif page == "🔧 Detail Aset":
    st.markdown('<div class="section-title">Detail Aset — Coal Handling System</div>',
                unsafe_allow_html=True)

    # Search bar
    search = st.text_input("🔍 Cari aset (nama / asset ID)", placeholder="Contoh: BELT CONVEYOR atau TK00EAC...")
    if search:
        mask = (df["deskripsi"].str.upper().str.contains(search.upper(), na=False) |
                df["asset_id"].str.upper().str.contains(search.upper(), na=False))
        df_show = df[mask]
    else:
        df_show = df.sort_values(["wellness_rank", "subsistem"])

    st.caption(f"Menampilkan {len(df_show)} aset")

    # ── Wellness score scatter per subsistem ──────────────────────────────────
    if not df_show.empty and "wellness_score" in df_show.columns:
        col_a, col_b = st.columns([3, 1])
        with col_a:
            st.markdown('<div class="section-title">Wellness Score per Aset</div>',
                        unsafe_allow_html=True)
            fig_scatter = px.strip(
                df_show.sort_values("wellness_score"),
                x="subsistem", y="wellness_score",
                color="wellness",
                color_discrete_map={"Hijau": "#2D7D32", "Kuning": "#F9A825", "Merah": "#C62828"},
                hover_data=["asset_id", "deskripsi", "kondisi"],
                labels={"wellness_score": "Score (0-100)", "subsistem": ""},
                stripmode="overlay",
            )
            fig_scatter.add_hline(y=75, line_dash="dot", line_color="#2D7D32",
                                  annotation_text="Batas Hijau (75)")
            fig_scatter.add_hline(y=40, line_dash="dot", line_color="#F9A825",
                                  annotation_text="Batas Kuning (40)")
            fig_scatter.update_layout(
                height=320, margin=dict(t=10, b=60, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                xaxis_tickangle=-25,
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

        with col_b:
            st.markdown('<div class="section-title">PM Due Soon</div>',
                        unsafe_allow_html=True)
            if "jam_ke_pm" in df_show.columns:
                due = df_show.dropna(subset=["jam_ke_pm"]).sort_values("jam_ke_pm").head(5)
                for _, row in due.iterrows():
                    jam = int(row["jam_ke_pm"])
                    color = "#C62828" if jam < 200 else ("#F57F17" if jam < 500 else "#2D7D32")
                    st.markdown(f"""
                    <div style="background:white;border-radius:8px;padding:8px 12px;
                                margin-bottom:6px;border-left:3px solid {color};">
                        <div style="font-size:11px;font-weight:600;color:#374151">
                            {str(row.get('deskripsi',''))[:35]}…</div>
                        <div style="font-size:13px;font-weight:600;color:{color}">
                            {jam:,} jam lagi</div>
                    </div>
                    """, unsafe_allow_html=True)

    # ── Full table ────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">Tabel Lengkap Aset</div>', unsafe_allow_html=True)
    display_cols = [c for c in [
        "asset_id", "subsistem", "deskripsi", "wellness", "wellness_score",
        "jam_ops", "acr", "mpi", "wo_no", "wo_tipe", "jam_ke_pm", "kondisi"
    ] if c in df_show.columns]

    col_rename = {
        "asset_id": "Asset ID", "subsistem": "Subsistem", "deskripsi": "Deskripsi",
        "wellness": "Wellness", "wellness_score": "Score",
        "jam_ops": "Jam Ops", "acr": "ACR", "mpi": "MPI",
        "wo_no": "No WO", "wo_tipe": "Tipe WO",
        "jam_ke_pm": "Jam ke PM", "kondisi": "Kondisi",
    }
    df_disp = df_show[display_cols].rename(columns=col_rename)

    def color_wellness_col(val):
        m = {"Hijau": "background-color:#E8F5E9;color:#2D7D32",
             "Kuning": "background-color:#FFF8E1;color:#F57F17",
             "Merah": "background-color:#FFEBEE;color:#C62828"}
        return m.get(val, "")

    styled_tbl = df_disp.style.map(color_wellness_col, subset=["Wellness"])
    st.dataframe(styled_tbl, use_container_width=True, height=380)

    # Download button
    csv = df_show.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV (filtered)", csv,
                       "asset_wellness_filtered.csv", "text/csv")


# ─────────────────────────────────────────────────────────────────────────────
# ── PAGE: WORK ORDER ─────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
elif page == "📋 Work Order":
    st.markdown('<div class="section-title">Histori & Status Work Order</div>',
                unsafe_allow_html=True)

    if df_wo.empty:
        st.info("Data WO belum tersedia. Isi sheet '2_Histori_WO' pada file Excel dan upload ulang.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        total_wo    = len(df_wo)
        wo_pm       = (df_wo["tipe"] == "PM").sum() if "tipe" in df_wo.columns else 0
        wo_cm       = (df_wo["tipe"] == "CM").sum() if "tipe" in df_wo.columns else 0
        total_dt    = df_wo["downtime_jam"].sum() if "downtime_jam" in df_wo.columns else 0

        for col, label, val, color in [
            (c1, "Total WO",     total_wo,         "#1F4E79"),
            (c2, "WO PM",        wo_pm,            "#2D7D32"),
            (c3, "WO CM / EM",   wo_cm,            "#F57F17"),
            (c4, "Total Downtime",f"{total_dt:.0f} jam", "#C62828"),
        ]:
            with col:
                st.markdown(f"""
                <div class="kpi-card" style="border-left-color:{color}">
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value" style="color:{color}">{val}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        col_chart, col_tbl = st.columns([1, 2])

        with col_chart:
            st.markdown('<div class="section-title">Distribusi Tipe WO</div>',
                        unsafe_allow_html=True)
            if "tipe" in df_wo.columns:
                tipe_count = df_wo["tipe"].value_counts().reset_index()
                tipe_count.columns = ["Tipe", "Jumlah"]
                fig_wo = px.bar(tipe_count, x="Tipe", y="Jumlah",
                                color="Tipe",
                                color_discrete_sequence=["#1F4E79","#F9A825","#C62828","#2D7D32"],
                                text="Jumlah")
                fig_wo.update_traces(textposition="outside")
                fig_wo.update_layout(showlegend=False, height=260,
                                     margin=dict(t=10,b=10,l=10,r=10),
                                     paper_bgcolor="rgba(0,0,0,0)",
                                     plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_wo, use_container_width=True)

        with col_tbl:
            st.markdown('<div class="section-title">Daftar Work Order</div>',
                        unsafe_allow_html=True)
            show_wo_cols = [c for c in [
                "wo_no", "asset_id", "subsistem", "tipe", "prioritas",
                "tgl_dibuat", "tgl_rencana", "durasi_jam", "downtime_jam", "pic", "keterangan"
            ] if c in df_wo.columns]
            st.dataframe(df_wo[show_wo_cols], use_container_width=True, height=260)


# ─────────────────────────────────────────────────────────────────────────────
# ── PAGE: TREN MINGGUAN ──────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
elif page == "📈 Tren Mingguan":
    st.markdown('<div class="section-title">Tren Wellness Mingguan — 2026</div>',
                unsafe_allow_html=True)

    if df_tren.empty:
        st.info("Data tren belum tersedia. Pastikan sheet '4_Tren_Mingguan' sudah diisi.")
    else:
        # Filter hanya data ada
        df_plot = df_tren[df_tren["status"].isin(["HIJAU","KUNING","MERAH"])]
        df_plot = df_plot.dropna(subset=["jumlah"])

        color_map_tren = {"HIJAU": "#2D7D32", "KUNING": "#F9A825", "MERAH": "#C62828"}

        col_line, col_area = st.columns(2)

        with col_line:
            st.markdown('<div class="section-title">Jumlah Aset per Status (Line)</div>',
                        unsafe_allow_html=True)
            fig_line = px.line(
                df_plot, x="minggu", y="jumlah", color="status",
                color_discrete_map=color_map_tren,
                markers=True,
                labels={"minggu": "Minggu", "jumlah": "Jumlah Aset", "status": "Status"},
            )
            fig_line.update_layout(
                height=300, margin=dict(t=10, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", y=1.1),
            )
            st.plotly_chart(fig_line, use_container_width=True)

        with col_area:
            st.markdown('<div class="section-title">Komposisi Wellness (Stacked Area)</div>',
                        unsafe_allow_html=True)
            df_pivot = df_plot.pivot_table(index="minggu", columns="status",
                                           values="jumlah", aggfunc="sum").reset_index()
            df_pivot = df_pivot.fillna(0)
            fig_area = go.Figure()
            for status, color in [("MERAH","#C62828"),("KUNING","#F9A825"),("HIJAU","#2D7D32")]:
                if status in df_pivot.columns:
                    fig_area.add_trace(go.Scatter(
                        x=df_pivot["minggu"], y=df_pivot[status],
                        name=status, fill="tonexty",
                        mode="lines", line=dict(color=color, width=1.5),
                        fillcolor=color.replace(")", ",0.35)").replace("rgb","rgba") if "rgb" in color
                                 else color + "59",
                    ))
            fig_area.update_layout(
                height=300, margin=dict(t=10, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", y=1.1),
            )
            st.plotly_chart(fig_area, use_container_width=True)

        # Raw tren table
        with st.expander("Lihat data tren mentah"):
            df_raw = df_tren.pivot_table(
                index="status", columns="minggu", values="jumlah", aggfunc="sum"
            )
            st.dataframe(df_raw, use_container_width=True)
