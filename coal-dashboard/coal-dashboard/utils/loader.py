"""
utils/loader.py
Fungsi ETL: baca Excel template Asset Wellness Coal Handling,
normalisasi, dan siapkan dataframe siap pakai untuk dashboard.
"""

import pandas as pd
import streamlit as st
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "data" / "wellness_data.xlsx"

WELLNESS_ORDER = {"Hijau": 0, "Kuning": 1, "Merah": 2}
WELLNESS_COLOR = {"Hijau": "#2D7D32", "Kuning": "#F9A825", "Merah": "#C62828"}
WELLNESS_BG    = {"Hijau": "#E8F5E9", "Kuning": "#FFF8E1", "Merah": "#FFEBEE"}

# ─────────────────────────────────────────────────────────────────────────────
# MASTER ASET
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_master(filepath=None) -> pd.DataFrame:
    path = filepath or DATA_PATH
    df = pd.read_excel(path, sheet_name="1_Master_Aset", header=1)

    # Normalise column names
    df.columns = df.columns.str.strip()

    # Rename to safe keys
    rename = {
        "Site": "site",
        "Asset ID": "asset_id",
        "Subsistem": "subsistem",
        "Deskripsi Aset": "deskripsi",
        "Wellness W-19": "wellness",
        "Wellness Score (0-100)": "wellness_score",
        "Kondisi Saat Ini": "kondisi",
        "Tgl Komisioning": "tgl_komisioning",
        "Umur Aset (tahun)": "umur_tahun",
        "Jam Operasi Kumulatif": "jam_ops",
        "Jam Operasi Bulan Ini": "jam_ops_bulan",
        "ACR Rank": "acr",
        "MPI Rank": "mpi",
        "No. WO Aktif": "wo_no",
        "Tipe WO": "wo_tipe",
        "Jadwal Selesai WO": "wo_jadwal",
        "PIC WO": "wo_pic",
        "Tgl PM Terakhir": "tgl_pm_terakhir",
        "Interval PM (jam)": "interval_pm",
        "Rekomendasi Tindakan": "rekomendasi",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    # Drop rows without asset_id
    df = df.dropna(subset=["asset_id"])
    df = df[df["asset_id"].astype(str).str.startswith("TK")]

    # Wellness label cleanup
    if "wellness" in df.columns:
        df["wellness"] = df["wellness"].astype(str).str.strip().str.capitalize()
        df["wellness"] = df["wellness"].replace({"Hijau": "Hijau", "Kuning": "Kuning", "Merah": "Merah"})

    # Wellness score fallback
    if "wellness_score" not in df.columns:
        df["wellness_score"] = 0
    fallback = {"Hijau": 85, "Kuning": 55, "Merah": 25}
    for label, score in fallback.items():
        mask = df["wellness"] == label
        df.loc[mask & df["wellness_score"].isna(), "wellness_score"] = score
    df["wellness_score"] = pd.to_numeric(df["wellness_score"], errors="coerce").fillna(0)

    # Numeric cols
    for col in ["jam_ops", "jam_ops_bulan", "acr", "mpi", "interval_pm", "umur_tahun"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Date cols
    for col in ["tgl_komisioning", "wo_jadwal", "tgl_pm_terakhir"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)

    # Jam sampai PM berikutnya
    if "jam_ops" in df.columns and "interval_pm" in df.columns:
        last_pm_ops = df["jam_ops"] - (df["jam_ops"] % df["interval_pm"].replace(0, 9999))
        df["jam_ke_pm"] = (last_pm_ops + df["interval_pm"]) - df["jam_ops"]
        df["jam_ke_pm"] = df["jam_ke_pm"].clip(lower=0)

    # Wellness sort key
    df["wellness_rank"] = df["wellness"].map(WELLNESS_ORDER).fillna(99)

    return df.reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# HISTORI WO
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_wo(filepath=None) -> pd.DataFrame:
    path = filepath or DATA_PATH
    try:
        df = pd.read_excel(path, sheet_name="2_Histori_WO", header=1)
        df.columns = df.columns.str.strip()
        rename = {
            "No. WO": "wo_no", "Asset ID": "asset_id", "Deskripsi Aset": "deskripsi",
            "Subsistem": "subsistem", "Tipe WO": "tipe", "Prioritas": "prioritas",
            "Tgl Dibuat": "tgl_dibuat", "Tgl Mulai": "tgl_mulai",
            "Tgl Selesai Rencana": "tgl_rencana", "Tgl Selesai Aktual": "tgl_aktual",
            "Durasi Aktual (jam)": "durasi_jam", "Downtime Terkait (jam)": "downtime_jam",
            "PIC": "pic", "Keterangan / Temuan": "keterangan",
        }
        df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
        df = df.dropna(subset=["wo_no"])
        df = df[~df["wo_no"].astype(str).str.startswith("⬆")]
        for col in ["tgl_dibuat", "tgl_mulai", "tgl_rencana", "tgl_aktual"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
        for col in ["durasi_jam", "downtime_jam"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df.reset_index(drop=True)
    except Exception:
        return pd.DataFrame()


# ─────────────────────────────────────────────────────────────────────────────
# TREN MINGGUAN
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_tren(filepath=None) -> pd.DataFrame:
    path = filepath or DATA_PATH
    try:
        df = pd.read_excel(path, sheet_name="4_Tren_Mingguan", header=1)
        df.columns = df.columns.str.strip()
        df = df.rename(columns={df.columns[0]: "status"})
        df = df[df["status"].isin(["MERAH", "KUNING", "HIJAU", "TOTAL"])]
        # Melt ke long format
        week_cols = [c for c in df.columns if str(c).startswith("W")]
        df_long = df.melt(id_vars=["status"], value_vars=week_cols,
                          var_name="minggu", value_name="jumlah")
        df_long["jumlah"] = pd.to_numeric(df_long["jumlah"], errors="coerce")
        return df_long.dropna(subset=["jumlah"]).reset_index(drop=True)
    except Exception:
        return pd.DataFrame()


# ─────────────────────────────────────────────────────────────────────────────
# HELPER METRICS
# ─────────────────────────────────────────────────────────────────────────────
def summary_metrics(df: pd.DataFrame) -> dict:
    total   = len(df)
    hijau   = (df["wellness"] == "Hijau").sum()
    kuning  = (df["wellness"] == "Kuning").sum()
    merah   = (df["wellness"] == "Merah").sum()
    avg_score = df["wellness_score"].mean()
    wo_open = df["wo_no"].notna().sum()
    return {
        "total": int(total),
        "hijau": int(hijau),
        "kuning": int(kuning),
        "merah": int(merah),
        "avg_score": round(float(avg_score), 1),
        "wo_open": int(wo_open),
    }
