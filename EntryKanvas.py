from datetime import datetime
from io import BytesIO
import hmac
import os
import sqlite3

import pandas as pd
import pytz
import requests
import streamlit as st


TZ_WIB = pytz.timezone("Asia/Jakarta")
DB_NAME = os.environ.get("KANVAS_DB_PATH", "laporan_kanvas.db")

PROMOTOR_ZONA = {
    "Achmad Danu Ardi": "Bubutan",
    "Arik Wibisono": "Bubutan",
    "Arum Ganda Fajar Ria": "Bubutan",
    "Candra Budi Eka": "Bubutan",
    "Rofi Wijayanto": "Bubutan",
    "Angga Budi Setiawan": "Gresik Selatan",
    "Dhimas Prayoga": "Gresik Selatan",
    "Hendra": "Gresik Selatan",
    "Rusdianto": "Gresik Selatan",
    "Septian Chandra": "Gresik Selatan",
    "Surya Hadi Pratama": "Gresik Selatan",
    "Alfianto Nur Huda": "Gresik Selatan",
    "Heru Setiawan": "Gresik Selatan",
    "Pisga Andriyanto": "Gresik Selatan",
    "Muhammad Rizky Pratama Putra": "Gresik Selatan",
    "Aldi Dwi Prasetyo": "Gresik Utara",
    "Budi Setyawan": "Gresik Utara",
    "Dwi Nor Fais": "Gresik Utara",
    "Khoirur Rijal": "Gresik Utara",
    "Lurico Umar Raffsanjani": "Gresik Utara",
    "Rahmad Dani": "Gresik Utara",
    "M Holidi": "Gresik Utara",
    "Daniel Arief Kurniawan": "Karangpilang",
    "Dimas Rizky Dermawan": "Karangpilang",
    "Guntur Vicki Prasetyo": "Karangpilang",
    "Zayd Abigail Johansyah": "Karangpilang",
    "Axel Setiawan": "Sawahan",
    "Delpiero Kevin Santoso": "Sawahan",
    "Muhamad Baharudin Yusuf": "Sawahan",
    "Muhammad Luthfi Anshori": "Sawahan",
    "Rendi Wahyudi": "Sawahan",
    "Arik Setiawan": "Tandes",
    "Syarif Usman Fadholi": "Tandes",
    "Surya Wisnu Wibisono": "Tandes",
    "Eko Sucipto": "Tandes",
}

FIELDS = {
    "canvas_plan": "Canvas Plan",
    "outlet_beli_ada": "Outlet Beli Ada",
    "outlet_ks_tb": "Outlet Ks Tb",
    "outlet_ks_b": "Outlet Ks B",
    "outlet_tb_ada_a": "Outlet TB Ada A",
    "outlet_tb_ada_p": "Outlet TB Ada P",
    "outlet_tb_ks": "Outlet TB Ks",
    "omset_bungkus": "Omset (Bungkus)",
    "promsus_10_1": "Promsus 10+1",
    "promsus_3_1": "Promsus 3+1",
    "promsus_2_1": "Promsus 2+1",
    "promsus_1_1": "Promsus 1+1",
    "promsus_n_mie_instan": "N+ Mie Instan",
    "outlet_buka_ecer": "Outlet Buka Ecer",
    "jumlah_rokok_sampling": "Jumlah Rokok Sampling",
    "jumlah_konsumen_trial": "Jumlah Konsumen Trial",
    "direct_selling": "Direct Selling",
}

st.set_page_config(
    page_title="Form Entry Laporan Kanvas",
    page_icon="📋",
    layout="wide",
)


def secret(name, default=""):
    """Read an optional Streamlit secret without requiring a local secrets file."""
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


def init_db():
    # Keep the existing SQLite filename/schema so existing local data is retained.
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS kanvas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tanggal TEXT, nama_promotor TEXT, zona TEXT, brand TEXT,
                canvas_plan INTEGER, outlet_beli_ada INTEGER, outlet_ks_tb INTEGER,
                outlet_ks_b INTEGER, outlet_tb_ada_a INTEGER, outlet_tb_ada_p INTEGER,
                outlet_tb_ks INTEGER, omset_bungkus INTEGER, promsus_10_1 INTEGER DEFAULT 0,
                promsus_3_1 INTEGER DEFAULT 0, promsus_2_1 INTEGER DEFAULT 0,
                promsus_1_1 INTEGER DEFAULT 0, promsus_n_mie_instan INTEGER DEFAULT 0,
                outlet_buka_ecer INTEGER DEFAULT 0, jumlah_rokok_sampling INTEGER DEFAULT 0,
                jumlah_konsumen_trial INTEGER DEFAULT 0, direct_selling INTEGER DEFAULT 0,
                waktu_submit TEXT
            )"""
        )
        # Migrate older databases that predate newer report fields.
        existing = {row[1] for row in conn.execute("PRAGMA table_info(kanvas)")}
        additions = {
            "nama_promotor": "TEXT", "zona": "TEXT", "promsus_10_1": "INTEGER DEFAULT 0",
            "promsus_3_1": "INTEGER DEFAULT 0", "promsus_2_1": "INTEGER DEFAULT 0",
            "promsus_1_1": "INTEGER DEFAULT 0", "promsus_n_mie_instan": "INTEGER DEFAULT 0",
            "outlet_buka_ecer": "INTEGER DEFAULT 0", "jumlah_rokok_sampling": "INTEGER DEFAULT 0",
            "jumlah_konsumen_trial": "INTEGER DEFAULT 0", "direct_selling": "INTEGER DEFAULT 0",
        }
        for name, kind in additions.items():
            if name not in existing:
                conn.execute(f"ALTER TABLE kanvas ADD COLUMN {name} {kind}")
        if "pic" in existing and "nama_promotor" not in existing:
            conn.execute("ALTER TABLE kanvas RENAME COLUMN pic TO nama_promotor")


def load_data():
    with sqlite3.connect(DB_NAME) as conn:
        return pd.read_sql_query("SELECT * FROM kanvas ORDER BY waktu_submit DESC", conn)


def backup_to_sheets(payload):
    url = secret("WEBHOOK_URL").strip()
    if not url:
        return False, "Backup Google Sheets belum dikonfigurasi."
    if not url.startswith("https://"):
        return False, "Webhook harus menggunakan HTTPS."
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True, "Backup Google Sheets berhasil."
    except requests.RequestException as exc:
        # Avoid showing full request details or secrets in the UI.
        return False, f"Backup gagal ({type(exc).__name__}); data lokal tetap tersimpan."


def save_report(data):
    names = ["tanggal", "nama_promotor", "zona", "brand", *FIELDS.keys(), "waktu_submit"]
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            f"INSERT INTO kanvas ({', '.join(names)}) VALUES ({', '.join('?' for _ in names)})",
            [data[name] for name in names],
        )
    return backup_to_sheets(data)


init_db()
st.title("📋 Form Entry Laporan Kanvas")
st.caption("Sistem Perekaman Data Kanvas Lapangan")

now = datetime.now(TZ_WIB)
today = now.strftime("%Y-%m-%d")
st.subheader("📝 Masukkan Data Laporan Baru")
with st.form("form_laporan_kanvas"):
    c1, c2 = st.columns(2)
    with c1:
        date_value = st.date_input("Tanggal", value=now.date())
        promoter = st.selectbox("Nama Promotor", list(PROMOTOR_ZONA))
        brand = st.selectbox("Brand", ["Djarum 76 Aksara"])
    with c2:
        st.text_input("Zona (Otomatis)", value=PROMOTOR_ZONA[promoter], disabled=True)
        canvas_plan = st.number_input("Canvas Plan", min_value=0, step=1)
        omset = st.number_input("Omset (bungkus)", min_value=0, step=1)

    st.markdown("#### 📊 Rincian Outlet dan Promosi")
    values = {}
    for key, label in FIELDS.items():
        if key == "canvas_plan":
            values[key] = int(canvas_plan)
        elif key == "omset_bungkus":
            values[key] = int(omset)
        else:
            values[key] = int(st.number_input(label, min_value=0, step=1, key=f"entry_{key}"))
    submitted = st.form_submit_button("💾 Simpan Laporan", type="primary")

if submitted:
    report = {
        "tanggal": date_value.strftime("%Y-%m-%d"),
        "nama_promotor": promoter,
        "zona": PROMOTOR_ZONA[promoter],
        "brand": brand,
        **values,
        "waktu_submit": datetime.now(TZ_WIB).strftime("%Y-%m-%d %H:%M:%S"),
    }
    backup_ok, backup_message = save_report(report)
    st.success("Laporan tersimpan di database lokal.")
    if backup_ok:
        st.success(backup_message)
    elif secret("WEBHOOK_URL"):
        st.warning(backup_message)
    else:
        st.info(backup_message)

# Public view only shows totals; the roster of who has/hasn't reported is private.
st.markdown("---")
st.subheader("🔍 Status Entry Hari Ini")
df = load_data()
today_df = df[df["tanggal"] == today] if not df.empty else pd.DataFrame()
entered = today_df["nama_promotor"].nunique() if not today_df.empty else 0
m1, m2 = st.columns(2)
m1.metric("Promotor sudah entry", f"{entered} / {len(PROMOTOR_ZONA)}")
m2.metric("Laporan hari ini", len(today_df))

st.markdown("---")
st.subheader("🔐 Area Admin")
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False
admin_password = secret("ADMIN_PASSWORD").strip()
if not admin_password:
    st.warning("Admin dinonaktifkan: atur ADMIN_PASSWORD di Streamlit Secrets sebelum digunakan.")
elif not st.session_state.admin_authenticated:
    with st.form("admin_login"):
        entered_password = st.text_input("Password Admin", type="password")
        login = st.form_submit_button("Buka Area Admin")
    if login:
        if hmac.compare_digest(entered_password, admin_password):
            st.session_state.admin_authenticated = True
            st.rerun()
        st.error("Password salah.")
else:
    if st.button("🔒 Keluar dari Area Admin"):
        st.session_state.admin_authenticated = False
        st.rerun()

    st.subheader("📊 Log Laporan")
    df = load_data()
    if df.empty:
        st.info("Belum ada data laporan.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Laporan Kanvas")
        st.download_button(
            "📥 Unduh Semua Data (Excel)", output.getvalue(),
            file_name=f"laporan_kanvas_{datetime.now(TZ_WIB):%Y%m%d_%H%M%S}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        st.markdown("#### Rekap Mingguan")
        df["tanggal_dt"] = pd.to_datetime(df["tanggal"], errors="coerce")
        iso = df["tanggal_dt"].dt.isocalendar()
        df["tahun_iso"] = iso.year
        df["minggu_iso"] = iso.week
        years = sorted(df["tahun_iso"].dropna().astype(int).unique(), reverse=True)
        if years:
            selected_year = st.selectbox("Tahun ISO", years)
            weeks = sorted(
                df.loc[df["tahun_iso"] == selected_year, "minggu_iso"].dropna().astype(int).unique(),
                reverse=True,
            )
            selected_week = st.selectbox("Minggu ISO", weeks)
            week_df = df[(df["tahun_iso"] == selected_year) & (df["minggu_iso"] == selected_week)]
            st.dataframe(
                week_df.groupby("tanggal", as_index=False).agg(
                    promotor=("nama_promotor", "nunique"),
                    laporan=("id", "count"),
                    omset_bungkus=("omset_bungkus", "sum"),
                    sampling=("jumlah_rokok_sampling", "sum"),
                    konsumen_trial=("jumlah_konsumen_trial", "sum"),
                    direct_selling=("direct_selling", "sum"),
                ),
                use_container_width=True,
                hide_index=True,
            )

        st.markdown("#### Hapus Data")
        delete_scope = st.selectbox("Rentang penghapusan", ["Hari Ini", "Semua Data"])
        confirm = st.checkbox("Saya memahami data yang dipilih akan dihapus permanen.")
        if st.button("Hapus Data", type="secondary", disabled=not confirm):
            with sqlite3.connect(DB_NAME) as conn:
                if delete_scope == "Hari Ini":
                    conn.execute("DELETE FROM kanvas WHERE tanggal = ?", (today,))
                else:
                    conn.execute("DELETE FROM kanvas")
            st.success("Data terpilih berhasil dihapus.")
            st.rerun()
