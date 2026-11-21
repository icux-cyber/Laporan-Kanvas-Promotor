from datetime import datetime
from io import BytesIO
import json
import os
import sqlite3
import base64
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd
import pytz
import requests
import streamlit as st
from PIL import Image as PILImage


TZ_WIB = pytz.timezone("Asia/Jakarta")
DB_NAME = "laporan_kanvas.db"
BRAND_DATA_FILE = "Merk_Rokok_All_Pabrikan_&_Nama_Karyawan.json"
BANNER_IMAGE_FILE = "76aksara.png"
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyRAigBCyzy2RZYD0FgeMc5PaiZbEVMSnCWJ2s--QGi1P3WMjqZE7hmhnel9C-nX1Ri/exec"
ADMIN_PASSWORD = "admin123"

PROMOTOR_ZONA = {
    "Achmad Danu Ardi": "Bubutan", "Arik Wibisono": "Bubutan",
    "Arum Ganda Fajar Ria": "Bubutan", "Candra Budi Eka": "Bubutan",
    "Rofi Wijayanto": "Bubutan", "Angga Budi Setiawan": "Gresik Selatan",
    "Dhimas Prayoga": "Gresik Selatan", "Hendra": "Gresik Selatan",
    "Rusdianto": "Gresik Selatan", "Septian Chandra": "Gresik Selatan",
    "Surya Hadi Pratama": "Gresik Selatan", "Alfianto Nur Huda": "Gresik Selatan",
    "Heru Setiawan": "Gresik Selatan", "Pisga Andriyanto": "Gresik Selatan",
    "Muhammad Rizky Pratama Putra": "Gresik Selatan", "Aldi Dwi Prasetyo": "Gresik Utara",
    "Budi Setyawan": "Gresik Utara", "Dwi Nor Fais": "Gresik Utara",
    "Khoirur Rijal": "Gresik Utara", "Lurico Umar Raffsanjani": "Gresik Utara",
    "Rahmad Dani": "Gresik Utara", "M Holidi": "Gresik Utara",
    "Daniel Arief Kurniawan": "Karangpilang", "Dimas Rizky Dermawan": "Karangpilang",
    "Guntur Vicki Prasetyo": "Karangpilang", "Zayd Abigail Johansyah": "Karangpilang",
    "Axel Setiawan": "Sawahan", "Delpiero Kevin Santoso": "Sawahan",
    "Muhamad Baharudin Yusuf": "Sawahan", "Muhammad Luthfi Anshori": "Sawahan",
    "Rendi Wahyudi": "Sawahan", "Arik Setiawan": "Tandes",
    "Syarif Usman Fadholi": "Tandes", "Surya Wisnu Wibisono": "Tandes",
    "Eko Sucipto": "Tandes",
    "Indra Fredi Wibowo": "Tandes",
}

FIELD_LABELS = {
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

OUTLET_KEYS = [
    "outlet_beli_ada", "outlet_ks_tb", "outlet_ks_b",
    "outlet_tb_ada_a", "outlet_tb_ada_p", "outlet_tb_ks",
]
PROMOTION_KEYS = [
    "promsus_10_1", "promsus_3_1", "promsus_2_1", "promsus_1_1",
    "promsus_n_mie_instan", "outlet_buka_ecer", "jumlah_rokok_sampling",
    "jumlah_konsumen_trial", "direct_selling",
]
SURVEY_AGE_RANGES = ["18-24 Tahun", "25-30 Tahun", "31-34 Tahun", "35-40 Tahun", "40+ Tahun"]
SURVEY_ASPECTS = ["Rasa", "Aroma", "Hisapan", "Harga", "Kemasan", "Lainnya"]
SURVEY_AWARENESS_SOURCES = [
    "Papan Reklame",
    "Iklan di TV",
    "Media Sosial (Facebook, IG, TikTok, dll)",
    "Teman / Tetangga",
]
SURVEY_BUY_WARUNG_OPTIONS = ["Ya", "Tidak", "Pikir-Pikir"]
SURVEY_LONG_TERM_OPTIONS = [
    "Ya (Jadi Rokok Utama)",
    "Belum Tentu (Jadi Rokok Selingan)",
    "Tidak Sama sekali",
]
SURVEY_EXTRA_FIELDS = {
    "Bersedia Beli di Warung/Toko/Minimarket": "bersedia_beli_warung",
    "Beralih Konsumsi Jangka Panjang": "beralih_jangka_panjang",
}
SURVEY_FEEDBACK_FIELDS = {
    "Komentar Positif - Rasa": "komentar_positif_rasa",
    "Komentar Positif - Aroma": "komentar_positif_aroma",
    "Komentar Positif - Hisapan": "komentar_positif_hisapan",
    "Komentar Positif - Harga": "komentar_positif_harga",
    "Komentar Positif - Kemasan": "komentar_positif_kemasan",
    "Komentar Positif - Lainnya": "komentar_positif_lainnya",
    "Komentar Negatif - Rasa": "komentar_negatif_rasa",
    "Komentar Negatif - Aroma": "komentar_negatif_aroma",
    "Komentar Negatif - Hisapan": "komentar_negatif_hisapan",
    "Komentar Negatif - Harga": "komentar_negatif_harga",
    "Komentar Negatif - Kemasan": "komentar_negatif_kemasan",
    "Komentar Negatif - Lainnya": "komentar_negatif_lainnya",
}

st.set_page_config(
    page_title="Sistem Kanvas & Survey — Djarum 76 Aksara",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 50%, #f8fafc 100%);
}

h1, h2, h3, h4 {
    color: #0f172a;
    font-weight: 700;
    letter-spacing: -0.02em;
}

.login-hero-combined {
    background: #09090b;
    border-radius: 16px;
    border: 1px solid #27272a;
    box-shadow: 0 12px 26px -8px rgba(15, 23, 42, 0.32);
    overflow: hidden;
    margin-bottom: 0.75rem;
}

.login-hero-combined img {
    width: 100%;
    height: auto;
    display: block;
    border-radius: 15px 15px 0 0;
}

.login-title-strip {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 65%, #991b1b 100%);
    padding: 0.8rem 1.2rem;
    color: #ffffff;
    border-top: 1px solid rgba(255, 255, 255, 0.14);
}

.login-title-strip h2 {
    color: #ffffff !important;
    font-size: 1.22rem;
    margin: 0 0 0.15rem 0;
    font-weight: 800;
    line-height: 1.2;
}

.login-title-strip p {
    color: #e2e8f0;
    font-size: 0.84rem;
    margin: 0;
    line-height: 1.3;
}

.hero-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 55%, #b91c1c 100%);
    padding: 1.35rem 1.75rem;
    border-radius: 16px;
    color: #ffffff;
    box-shadow: 0 12px 28px -8px rgba(15, 23, 42, 0.32);
    margin-bottom: 1.2rem;
    border: 1px solid rgba(255, 255, 255, 0.12);
}
.hero-header h1 {
    color: #ffffff !important;
    font-size: 1.65rem;
    margin: 0 0 0.25rem 0;
    font-weight: 800;
}
.hero-header p {
    color: #cbd5e1;
    font-size: 0.92rem;
    margin: 0;
}
.hero-badge {
    display: inline-block;
    background: rgba(255, 255, 255, 0.16);
    color: #fef08a;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 0.2rem 0.65rem;
    border-radius: 999px;
    margin-bottom: 0.5rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

.user-pill {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    color: #ffffff;
    padding: 0.95rem 1.1rem;
    border-radius: 14px;
    margin-bottom: 1rem;
    border: 1px solid #334155;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15);
}
.user-pill .role-tag {
    display: inline-block;
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    padding: 0.18rem 0.55rem;
    border-radius: 999px;
    background: #dc2626;
    color: #ffffff;
    margin-bottom: 0.35rem;
}
.user-pill .role-tag.admin {
    background: #d97706;
}
.user-pill .user-name {
    font-size: 1rem;
    font-weight: 700;
    color: #f8fafc;
    line-height: 1.3;
}
.user-pill .user-sub {
    font-size: 0.8rem;
    color: #94a3b8;
    margin-top: 0.15rem;
}

.stButton>button {
    border-radius: 10px;
    font-weight: 600;
    width: 100%;
    padding: 0.5rem 0.95rem;
    transition: all 0.18s ease;
}

div[data-testid="stForm"] {
    background: #ffffff;
    padding: 1.15rem 1.35rem;
    border-radius: 14px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
}

div[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #e2e8f0;
    background: #ffffff;
}

div[data-testid="stMetric"] {
    background: #ffffff;
    padding: 1rem 1.2rem;
    border-radius: 14px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 2px 10px rgba(15, 23, 42, 0.03);
}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def _get_banner_base64():
    if not os.path.exists(BANNER_IMAGE_FILE):
        return None
    with open(BANNER_IMAGE_FILE, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")


def login_page():
    _, center_col, _ = st.columns([0.5, 3.0, 0.5])
    with center_col:
        banner_b64 = _get_banner_base64()
        banner_html = (
            f'<img src="data:image/png;base64,{banner_b64}" alt="Djarum 76 Aksara">'
            if banner_b64 else ""
        )
        st.markdown(f"""
        <div class="login-hero-combined">
            {banner_html}
            <div class="login-title-strip">
                <h2>📋 Sistem Laporan Kanvas & Survey Konsumen</h2>
                <p>Silakan masuk sebagai Promotor atau Admin untuk melanjutkan aktivitas lapangan.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        tab_promotor, tab_admin = st.tabs(["🧑‍💼 Login Promotor", "🔐 Login Admin"])

        with tab_promotor:
            st.markdown("**Masuk Sebagai Promotor**")
            st.caption("Pilih nama Anda terlebih dahulu, lalu tentukan menu kerja yang ingin dibuka.")

            promoter_list = ["-- Pilih Nama Promotor --"] + list(PROMOTOR_ZONA.keys())
            selected_promotor = st.selectbox(
                "Nama Promotor",
                promoter_list,
                index=0,
                key="login_select_promotor",
            )

            is_promoter_chosen = selected_promotor != "-- Pilih Nama Promotor --"
            if is_promoter_chosen:
                zona_promotor = PROMOTOR_ZONA[selected_promotor]
                st.info(f"📍 Zona Tugas: **{zona_promotor}**")
            else:
                st.caption("Pilih nama promotor terlebih dahulu untuk mengaktifkan pilihan menu.")

            selected_module = st.radio(
                "Pilih Menu Tujuan:",
                ["📝 Entry Laporan Kanvas", "🗣️ Survey Konsumen"],
                horizontal=True,
                disabled=not is_promoter_chosen,
                key="login_promotor_module",
            )

            if st.button(
                "🚀 Masuk ke Aplikasi (Promotor)",
                type="primary",
                disabled=not is_promoter_chosen,
                key="btn_login_promotor",
            ):
                st.session_state["auth_role"] = "promotor"
                st.session_state["auth_promotor"] = selected_promotor
                st.session_state["promotor_assigned_module"] = (
                    "survey" if "Survey" in selected_module else "kanvas"
                )
                st.session_state["active_page"] = (
                    "Survey Konsumen" if "Survey" in selected_module else "Laporan Kanvas"
                )
                st.rerun()

        with tab_admin:
            st.markdown("**Masuk Sebagai Admin**")
            st.caption("Masukkan password admin untuk mengakses seluruh modul Laporan Kanvas & Survey Konsumen.")

            with st.form("form_login_admin_portal"):
                admin_pwd = st.text_input("Password Admin", type="password", placeholder="Masukkan password...")
                submit_admin = st.form_submit_button("🔓 Masuk Sebagai Admin", type="primary")

            if submit_admin:
                if admin_pwd == ADMIN_PASSWORD:
                    st.session_state["auth_role"] = "admin"
                    st.session_state["auth_promotor"] = None
                    st.session_state["active_page"] = "Laporan Kanvas"
                    st.rerun()
                else:
                    st.error("❌ Password Admin salah. Silakan coba lagi.")


def report_form(locked_promoter=None):
    st.subheader("📝 Masukkan Data Laporan Baru")
    version = st.session_state.get("entry_form_version", 0)
    with st.form("form_laporan_kanvas"):
        c1, c2 = st.columns(2)
        with c1:
            date_value = st.date_input("Date", value=datetime.now(TZ_WIB).date(), key=f"entry_date_{version}")
            if locked_promoter:
                promoter = locked_promoter
                st.text_input("Nama Promotor", value=promoter, disabled=True)
            else:
                promoter = st.selectbox("Nama Promotor", list(PROMOTOR_ZONA), key=f"entry_promoter_{version}")
            brand = st.selectbox("Brand", ["Djarum 76 Aksara"], key=f"entry_brand_{version}")
        with c2:
            st.text_input("Zona (Otomatis)", value=PROMOTOR_ZONA[promoter], disabled=True)
            canvas_plan = st.number_input("Canvas Plan", min_value=0, step=1, value=0, key=f"entry_plan_{version}")
            omset = st.number_input("Omset (bungkus)", min_value=0, step=1, value=0, key=f"entry_omset_{version}")

        st.markdown("#### 🏪 Rincian Outlet")
        outlet_values = {}
        outlet_columns = st.columns(3)
        for index, key in enumerate(OUTLET_KEYS):
            with outlet_columns[index % 3]:
                outlet_values[key] = int(st.number_input(
                    FIELD_LABELS[key], min_value=0, step=1, value=0,
                    key=f"entry_{key}_{version}",
                ))
        st.markdown("#### 🎁 Rincian Promosi dan Aktivitas")
        promotion_values = {}
        promotion_columns = st.columns(3)
        for index, key in enumerate(PROMOTION_KEYS):
            with promotion_columns[index % 3]:
                promotion_values[key] = int(st.number_input(
                    FIELD_LABELS[key], min_value=0, step=1, value=0,
                    key=f"entry_{key}_{version}",
                ))
        b1, b2 = st.columns(2)
        with b1:
            preview = st.form_submit_button("👁️ Lihat Preview", type="secondary")
        with b2:
            submit = st.form_submit_button("🚀 Langsung Kirim", type="primary")

    if preview or submit:
        report = {
            "tanggal": date_value.strftime("%Y-%m-%d"), "nama_promotor": promoter,
            "zona": PROMOTOR_ZONA[promoter], "brand": brand,
            "canvas_plan": int(canvas_plan), "omset_bungkus": int(omset),
            **outlet_values, **promotion_values,
            "waktu_submit": datetime.now(TZ_WIB).strftime("%Y-%m-%d %H:%M:%S"),
        }
        if preview:
            st.session_state["form_preview_data"] = report
        else:
            save_report(report)
            st.session_state["form_preview_data"] = None
            st.session_state["entry_form_version"] = version + 1
            st.session_state["notifikasi_sukses"] = "🎉 Data laporan kanvas berhasil dikirim ke database & sheet DataKanvasAksara! Form entry telah dikosongkan."
        st.rerun()

    pending = st.session_state.get("form_preview_data")
    if pending:
        st.markdown("### 📋 Preview Data Laporan Baru")
        st.dataframe(pd.DataFrame(list(pending.items()), columns=["Keterangan", "Nilai"]), use_container_width=True, hide_index=True)
        b1, b2 = st.columns(2)
        with b1:
            if st.button("❌ Batal / Edit Kembali"):
                st.session_state["form_preview_data"] = None
                st.rerun()
        with b2:
            if st.button("🚀 Konfirmasi & Simpan Laporan", type="primary"):
                save_report(pending)
                st.session_state["form_preview_data"] = None
                st.session_state["entry_form_version"] = version + 1
                st.session_state["notifikasi_sukses"] = "🎉 Data laporan kanvas berhasil disimpan ke database & sheet DataKanvasAksara! Form entry telah dikosongkan."
                st.rerun()


def daily_status(df, today):
    st.subheader("🔍 Monitoring Status Entry Promotor Hari Ini")
    st.caption(f"Tanggal Monitoring: {today}")
    today_df = df[df["Tanggal"] == today] if not df.empty else pd.DataFrame()
    entered = today_df["Nama Promotor"].dropna().unique().tolist() if not today_df.empty else []
    yes, no = st.tabs([f"✅ Sudah Entry ({len(entered)})", f"⚠️ Belum Entry ({len(PROMOTOR_ZONA)-len(entered)})"])
    with yes:
        if entered:
            st.success(f"Terdapat **{len(entered)}** promotor yang sudah melakukan entry laporan hari ini.")
            st.dataframe(pd.DataFrame([{"Nama Promotor": p, "Zona": PROMOTOR_ZONA.get(p, "-")} for p in entered]), use_container_width=True)
        else:
            st.info("📭 Belum ada promotor yang melakukan entry laporan pada hari ini.")
    with no:
        missing = [{"Nama Promotor": p, "Zona": z} for p, z in PROMOTOR_ZONA.items() if p not in entered]
        if missing:
            st.warning(f"⚠️ Terdapat **{len(missing)}** promotor yang belum melakukan entry laporan hari ini.")
            st.dataframe(pd.DataFrame(missing), use_container_width=True)
        else:
            st.success("🎉 Seluruh promotor telah melakukan entry laporan hari ini.")


def survey_promoter_status(survey_df):
    st.subheader("👥 Status Promotor Sudah & Belum Survey Konsumen")
    work = survey_df.copy()
    work["_dt"] = pd.to_datetime(work["Waktu Survey"], errors="coerce")
    work["_tgl"] = work["_dt"].dt.strftime("%Y-%m-%d")

    available_dates = sorted(work["_tgl"].dropna().unique().tolist(), reverse=True)
    today_wib = datetime.now(TZ_WIB).strftime("%Y-%m-%d")
    date_options = ["Semua Tanggal"] + available_dates
    default_idx = date_options.index(today_wib) if today_wib in date_options else 0

    selected_date = st.selectbox(
        "Filter Tanggal Survey:",
        date_options,
        index=default_idx,
        key="survey_promoter_status_date",
    )
    filtered_df = work if selected_date == "Semua Tanggal" else work[work["_tgl"] == selected_date]

    promoter_names = (
        filtered_df["Nama Promotor"]
        .dropna()
        .astype(str)
        .str.strip()
    )
    promoter_names = promoter_names[promoter_names != ""]
    counts_by_promoter = promoter_names.value_counts().to_dict()

    done_promoters = [p for p in PROMOTOR_ZONA if p in counts_by_promoter]
    not_done_promoters = [p for p in PROMOTOR_ZONA if p not in counts_by_promoter]

    tab_done, tab_not_done = st.tabs([
        f"✅ Sudah Survey ({len(done_promoters)})",
        f"⚠️ Belum Survey ({len(not_done_promoters)})",
    ])
    with tab_done:
        if done_promoters:
            done_rows = [
                {
                    "Nama Promotor": p,
                    "Zona": PROMOTOR_ZONA[p],
                    "Jumlah Survey": int(counts_by_promoter[p]),
                }
                for p in done_promoters
            ]
            st.success(f"Terdapat **{len(done_promoters)}** promotor yang sudah melakukan survey konsumen.")
            st.dataframe(pd.DataFrame(done_rows), use_container_width=True, hide_index=True)
        else:
            st.info("📭 Belum ada promotor yang melakukan survey konsumen pada periode ini.")
    with tab_not_done:
        if not_done_promoters:
            not_done_rows = [
                {
                    "Nama Promotor": p,
                    "Zona": PROMOTOR_ZONA[p],
                    "Jumlah Survey": 0,
                }
                for p in not_done_promoters
            ]
            st.warning(f"⚠️ Terdapat **{len(not_done_promoters)}** promotor yang belum melakukan survey konsumen.")
            st.dataframe(pd.DataFrame(not_done_rows), use_container_width=True, hide_index=True)
        else:
            st.success("🎉 Seluruh promotor telah melakukan survey konsumen.")


def consumer_survey_entry_page(locked_promoter=None):
    st.markdown("""
    <div class="hero-header">
        <div class="hero-badge">Voice of Customer • Djarum 76 Aksara</div>
        <h1>🗣️ Entry Survey Konsumen</h1>
        <p>Perekaman respon konsumen setelah mencoba produk di lapangan.</p>
    </div>
    """, unsafe_allow_html=True)

    version = st.session_state.get("survey_form_version", 0)
    bumo_options = load_bumo_options()

    c_id1, c_id2 = st.columns(2)
    with c_id1:
        if locked_promoter:
            nama_promotor = locked_promoter
            st.text_input("Nama Promotor", value=nama_promotor, disabled=True, key=f"survey_promoter_locked_{version}")
        else:
            promoter_options = [""] + list(PROMOTOR_ZONA)
            nama_promotor = st.selectbox(
                "Nama Promotor",
                promoter_options,
                index=0,
                format_func=lambda value: "-- Belum dipilih / Kosong --" if value == "" else value,
                key=f"survey_promoter_{version}",
            )
        sektor_survey = st.text_input("Sektor Survey", key=f"survey_sector_{version}")
        nama_konsumen = st.text_input("Nama Konsumen", key=f"survey_consumer_{version}")
    with c_id2:
        range_usia = st.selectbox(
            "Range Umur Konsumen", SURVEY_AGE_RANGES, key=f"survey_age_{version}",
        )
        pekerjaan = st.text_input("Pekerjaan Konsumen", key=f"survey_job_{version}")
        bumo = st.selectbox(
            "BUMO Rokok Konsumen",
            bumo_options,
            index=0,
            format_func=lambda value: "-- Belum dipilih / Kosong --" if value == "" else value,
            key=f"survey_bumo_{version}",
        )

    st.markdown("#### 📢 Awareness Djarum 76 Aksara")
    tahu_76_aksara = st.radio(
        "Apakah anda pernah mengetahui Djarum 76 Aksara?",
        ["Tidak", "Ya"],
        horizontal=True,
        key=f"survey_tahu_76_aksara_{version}",
    )
    if tahu_76_aksara == "Ya":
        sumber_info_list = st.multiselect(
            "Kalau iya melihatnya dari mana?",
            SURVEY_AWARENESS_SOURCES,
            key=f"survey_sumber_76_aksara_{version}",
        )
        sumber_info_str = ", ".join(sumber_info_list)
    else:
        sumber_info_str = ""

    st.markdown("#### 🛒 Minat Pembelian & Jangka Panjang Setelah Mencoba")
    bersedia_beli_warung = st.radio(
        "Setelah mencoba apakah anda bersedia membeli di Warung/Toko/Minimarket?",
        SURVEY_BUY_WARUNG_OPTIONS,
        horizontal=True,
        key=f"survey_bersedia_beli_warung_{version}",
    )
    beralih_jangka_panjang = st.radio(
        "Apakah setelah mencoba Anda akan beralih mengkonsumsi rokok ini dalam jangka panjang?",
        SURVEY_LONG_TERM_OPTIONS,
        horizontal=True,
        key=f"survey_beralih_jangka_panjang_{version}",
    )

    with st.form(f"form_survey_konsumen_{version}"):
        positive_comments = {}
        negative_comments = {}
        positive_column, negative_column = st.columns(2)
        with positive_column:
            st.markdown("#### ✅ Komentar Positif dari Rokok yang Dicoba")
            for aspect in SURVEY_ASPECTS:
                label = f"Komentar Positif - {aspect}"
                key = SURVEY_FEEDBACK_FIELDS[label]
                positive_comments[key] = st.text_area(
                    label, key=f"survey_{key}_{version}",
                )
        with negative_column:
            st.markdown("#### ⚠️ Komentar Negatif dari Rokok yang Dicoba")
            for aspect in SURVEY_ASPECTS:
                label = f"Komentar Negatif - {aspect}"
                key = SURVEY_FEEDBACK_FIELDS[label]
                negative_comments[key] = st.text_area(
                    label, key=f"survey_{key}_{version}",
                )
        submit = st.form_submit_button("💾 Simpan Survey", type="primary")

    if submit:
        feedback = {**positive_comments, **negative_comments}
        columns = [
            "waktu_survey", "nama_promotor", "sektor_survey", "nama_konsumen",
            "range_usia_konsumen", "pekerjaan_konsumen", "bumo_rokok_konsumen",
            "tahu_76_aksara", "sumber_info_76_aksara",
            *SURVEY_EXTRA_FIELDS.values(),
            *SURVEY_FEEDBACK_FIELDS.values(),
        ]
        values = [
            datetime.now(TZ_WIB).strftime("%Y-%m-%d %H:%M:%S"),
            nama_promotor, sektor_survey.strip(), nama_konsumen.strip(),
            range_usia, pekerjaan.strip(), bumo,
            tahu_76_aksara, sumber_info_str,
            bersedia_beli_warung, beralih_jangka_panjang,
            *[feedback[column].strip() for column in SURVEY_FEEDBACK_FIELDS.values()],
        ]
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.execute(
                f"INSERT INTO survey_konsumen ({', '.join(columns)}) "
                f"VALUES ({', '.join('?' for _ in columns)})",
                values,
            )
            survey_record = dict(zip(columns, values))
            survey_record["id"] = int(cursor.lastrowid)
        try:
            sync_survey_to_sheets("upsert", survey_record)
        except RuntimeError as error:
            st.session_state["notifikasi_error"] = (
                f"Survey tersimpan di database lokal, tetapi backup Google Sheets gagal: {error}"
            )
        else:
            st.session_state["notifikasi_sukses"] = "✅ Survey berhasil disimpan dan di-backup ke Google Sheets."
        st.session_state["survey_form_version"] = version + 1
        st.rerun()


def survey_log_page(is_admin=False, locked_promoter=None):
    st.title("📋 Log Entry Survey Konsumen")
    survey_df = load_survey_data()
    if locked_promoter and not is_admin:
        survey_df = survey_df[survey_df["Nama Promotor"] == locked_promoter]
    if survey_df.empty:
        st.info("📭 Belum ada data survey konsumen.")
    else:
        st.dataframe(survey_df, use_container_width=True, hide_index=True)
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            survey_df.to_excel(writer, index=False, sheet_name="Survey Konsumen")
        st.download_button(
            "💾 Download Log Survey ke Excel",
            output.getvalue(),
            file_name=f"log_survey_konsumen_{datetime.now(TZ_WIB).strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        if is_admin:
            st.markdown("#### 🗑️ Hapus Survey per Baris")
            delete_id = st.selectbox(
                "Pilih survey yang akan dihapus:",
                survey_df["ID"].tolist(),
                format_func=lambda value: (
                    f"ID #{value} — {survey_df.loc[survey_df['ID'] == value, 'Nama Konsumen'].iloc[0]} "
                    f"— {survey_df.loc[survey_df['ID'] == value, 'Nama Promotor'].iloc[0]}"
                ),
                key="delete_survey_id",
            )
            with st.form("form_hapus_satu_survey"):
                confirm_delete = st.checkbox("Saya yakin ingin menghapus survey yang dipilih.")
                delete_survey = st.form_submit_button("🗑️ Hapus Survey Terpilih", type="secondary")
            if delete_survey:
                if not confirm_delete:
                    st.error("Centang konfirmasi sebelum menghapus survey.")
                else:
                    try:
                        sync_survey_to_sheets("delete", delete_id)
                    except RuntimeError as error:
                        st.error(f"Penghapusan dibatalkan karena backup Google Sheets gagal: {error}")
                    else:
                        with sqlite3.connect(DB_NAME) as conn:
                            conn.execute("DELETE FROM survey_konsumen WHERE id = ?", (int(delete_id),))
                        st.session_state["notifikasi_sukses"] = (
                            f"✅ Survey ID #{delete_id} berhasil dihapus dari lokal dan Google Sheets."
                        )
                        st.rerun()


def build_bumo_acceptability_summary(survey_df):
    work = survey_df.copy()
    pos_cols = [f"Komentar Positif - {aspect}" for aspect in SURVEY_ASPECTS]
    neg_cols = [f"Komentar Negatif - {aspect}" for aspect in SURVEY_ASPECTS]

    work["_pos_count"] = sum(
        work[col].fillna("").astype(str).str.strip().ne("").astype(int)
        for col in pos_cols
    )
    work["_neg_count"] = sum(
        work[col].fillna("").astype(str).str.strip().ne("").astype(int)
        for col in neg_cols
    )
    work["_bumo"] = (
        work["BUMO Rokok Konsumen"]
        .fillna("")
        .astype(str)
        .str.strip()
        .replace("", "Tidak Diisi")
    )

    records = []
    for bumo_name, group in work.groupby("_bumo", sort=False):
        pos_total = int(group["_pos_count"].sum())
        neg_total = int(group["_neg_count"].sum())
        respondents = int(len(group))
        if pos_total > neg_total:
            status = "Diterima"
            kesimpulan = (
                f"Diterima — respon positif ({pos_total}) lebih banyak daripada respon negatif ({neg_total})."
            )
        elif neg_total > pos_total:
            status = "Tidak Diterima"
            kesimpulan = (
                f"Tidak Diterima — respon negatif ({neg_total}) lebih banyak daripada respon positif ({pos_total})."
            )
        else:
            status = "Imbang / Perlu Evaluasi"
            kesimpulan = (
                f"Imbang — jumlah respon positif ({pos_total}) sama dengan respon negatif ({neg_total})."
            )

        records.append({
            "BUMO Rokok Konsumen": bumo_name,
            "Jumlah Responden": respondents,
            "Respon Positif": pos_total,
            "Respon Negatif": neg_total,
            "Selisih (Pos - Neg)": pos_total - neg_total,
            "Status Acceptable D.76 Aksara": status,
            "Kesimpulan": kesimpulan,
        })

    summary_df = pd.DataFrame(records)
    if not summary_df.empty:
        summary_df = summary_df.sort_values(
            by=["Jumlah Responden", "Respon Positif"],
            ascending=[False, False],
        ).reset_index(drop=True)
    return summary_df


def _render_donut_with_center_kpi(
    values,
    labels,
    title,
    kpi_value,
    kpi_sublabel,
    colors=None,
    figsize=(7.5, 5.5),
):
    fig, ax = plt.subplots(figsize=figsize, facecolor="#f8fafc")
    ax.set_facecolor("#f8fafc")

    total = float(sum(values))
    wedges, _ = ax.pie(
        values,
        labels=None,
        startangle=90,
        colors=colors,
        counterclock=False,
        wedgeprops={"width": 0.36, "edgecolor": "white", "linewidth": 2.2},
    )

    for wedge, val, lbl in zip(wedges, values, labels):
        if total <= 0 or val <= 0:
            continue
        pct = (val / total) * 100.0
        angle = np.deg2rad((wedge.theta1 + wedge.theta2) / 2.0)
        mid_r = 0.82
        x = mid_r * np.cos(angle)
        y = mid_r * np.sin(angle)
        if pct >= 8.0:
            ax.text(
                x,
                y,
                f"{int(val)}\n({pct:.1f}%)",
                ha="center",
                va="center",
                color="white",
                fontsize=8.5,
                fontweight="bold",
            )
        else:
            outer_x = 1.14 * np.cos(angle)
            outer_y = 1.14 * np.sin(angle)
            ha = "left" if outer_x >= 0 else "right"
            ax.annotate(
                f"{lbl}: {int(val)} ({pct:.1f}%)",
                xy=(1.0 * np.cos(angle), 1.0 * np.sin(angle)),
                xytext=(outer_x, outer_y),
                ha=ha,
                va="center",
                fontsize=8,
                color="#1e293b",
                arrowprops={"arrowstyle": "-", "color": "#94a3b8", "lw": 0.9},
            )

    center_circle = plt.Circle((0, 0), 0.62, fc="white", ec="#e2e8f0", lw=1.5)
    ax.add_patch(center_circle)
    ax.text(
        0,
        0.10,
        str(kpi_value),
        ha="center",
        va="center",
        fontsize=18,
        fontweight="bold",
        color="#0f172a",
    )
    ax.text(
        0,
        -0.18,
        str(kpi_sublabel),
        ha="center",
        va="center",
        fontsize=8.5,
        color="#475569",
    )

    ax.legend(
        wedges,
        labels,
        title="Kategori",
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        frameon=True,
        facecolor="white",
        edgecolor="#e2e8f0",
        fontsize=8.5,
        title_fontsize=9,
    )
    ax.set_title(title, fontsize=11.5, fontweight="bold", color="#0f172a", pad=14)
    ax.axis("equal")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def _render_rounded_bar_highlight(aspects, positive_counts, negative_counts):
    pos_arr = np.array(positive_counts, dtype=float)
    neg_arr = np.array(negative_counts, dtype=float)
    totals = pos_arr + neg_arr

    highlight_idx = int(np.argmax(totals)) if len(totals) > 0 and np.max(totals) > 0 else None
    max_val = max(float(np.max(pos_arr)) if len(pos_arr) else 0.0,
                  float(np.max(neg_arr)) if len(neg_arr) else 0.0,
                  1.0)

    fig, ax = plt.subplots(figsize=(10.5, 5.2), facecolor="#f8fafc")
    ax.set_facecolor("#ffffff")

    x_positions = np.arange(len(aspects), dtype=float)
    bar_width = 0.34
    offset = 0.19
    radius = min(bar_width * 0.28, max_val * 0.03)

    if highlight_idx is not None:
        ax.axvspan(
            highlight_idx - 0.45,
            highlight_idx + 0.45,
            color="#fef9c3",
            alpha=0.55,
            zorder=0,
            label="Aspek Tertinggi (Highlight)",
        )

    for idx in range(len(aspects)):
        is_top = (highlight_idx == idx)
        pos_val = pos_arr[idx]
        neg_val = neg_arr[idx]

        pos_color = "#15803d" if is_top else "#4ade80"
        neg_color = "#b91c1c" if is_top else "#f87171"
        edge_color = "#0f172a" if is_top else "none"
        edge_lw = 1.4 if is_top else 0.0

        if pos_val > 0:
            r_pos = min(radius, pos_val * 0.45)
            pos_patch = FancyBboxPatch(
                (x_positions[idx] - offset - bar_width / 2, 0.0),
                bar_width,
                pos_val,
                boxstyle=f"round,pad=0,rounding_size={r_pos}",
                facecolor=pos_color,
                edgecolor=edge_color,
                linewidth=edge_lw,
                zorder=3,
            )
            ax.add_patch(pos_patch)
            ax.text(
                x_positions[idx] - offset,
                pos_val + max_val * 0.02,
                f"{int(pos_val)}",
                ha="center",
                va="bottom",
                fontsize=8.5,
                fontweight="bold" if is_top else "normal",
                color="#0f172a",
                zorder=4,
            )

        if neg_val > 0:
            r_neg = min(radius, neg_val * 0.45)
            neg_patch = FancyBboxPatch(
                (x_positions[idx] + offset - bar_width / 2, 0.0),
                bar_width,
                neg_val,
                boxstyle=f"round,pad=0,rounding_size={r_neg}",
                facecolor=neg_color,
                edgecolor=edge_color,
                linewidth=edge_lw,
                zorder=3,
            )
            ax.add_patch(neg_patch)
            ax.text(
                x_positions[idx] + offset,
                neg_val + max_val * 0.02,
                f"{int(neg_val)}",
                ha="center",
                va="bottom",
                fontsize=8.5,
                fontweight="bold" if is_top else "normal",
                color="#0f172a",
                zorder=4,
            )

    legend_handles = [
        FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0,rounding_size=0.2", facecolor="#4ade80", edgecolor="none"),
        FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0,rounding_size=0.2", facecolor="#f87171", edgecolor="none"),
    ]
    legend_labels = ["Positif", "Negatif"]
    if highlight_idx is not None:
        legend_handles.append(
            FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0,rounding_size=0.2", facecolor="#fef9c3", edgecolor="#eab308", linewidth=1.0)
        )
        legend_labels.append(f"Highlight: {aspects[highlight_idx]} ({int(totals[highlight_idx])})")

    ax.set_xlim(-0.6, len(aspects) - 0.4)
    ax.set_ylim(0, max_val * 1.18)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(
        [f"★ {a}" if highlight_idx == i else a for i, a in enumerate(aspects)],
        fontsize=9.5,
        fontweight="bold",
    )
    ax.set_ylabel("Jumlah Komentar", fontsize=9.5, color="#334155")
    ax.set_title("Komentar per Aspek Rokok (Rounded Bar + Highlight)", fontsize=11.5, fontweight="bold", color="#0f172a", pad=12)
    ax.grid(axis="y", linestyle="--", alpha=0.4, color="#cbd5e1", zorder=1)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(legend_handles, legend_labels, loc="upper right", frameon=True, facecolor="white", edgecolor="#e2e8f0", fontsize=8.5)

    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def survey_monitoring_page():
    st.title("📊 Monitoring Survey Konsumen")
    survey_df = load_survey_data()
    if survey_df.empty:
        st.info("📭 Belum ada data survey untuk dimonitor.")
        return

    survey_promoter_status(survey_df)
    st.markdown("---")

    positive_counts = [
        survey_df[f"Komentar Positif - {aspect}"].fillna("").astype(str).str.strip().ne("").sum()
        for aspect in SURVEY_ASPECTS
    ]
    negative_counts = [
        survey_df[f"Komentar Negatif - {aspect}"].fillna("").astype(str).str.strip().ne("").sum()
        for aspect in SURVEY_ASPECTS
    ]
    metrics = st.columns(3)
    metrics[0].metric("Total Konsumen Survey", len(survey_df))
    metrics[1].metric("Komentar Positif", sum(positive_counts))
    metrics[2].metric("Komentar Negatif", sum(negative_counts))

    st.markdown("---")
    st.subheader("🛒 Kesediaan Membeli di Warung/Toko/Minimarket & Beralih Jangka Panjang")
    c_buy, c_long = st.columns(2)

    with c_buy:
        buy_col = "Bersedia Beli di Warung/Toko/Minimarket"
        buy_series = survey_df[buy_col].fillna("").astype(str).str.strip().replace("", "Tidak Diisi")
        buy_counts = buy_series.value_counts()
        ordered_buy = [opt for opt in SURVEY_BUY_WARUNG_OPTIONS if opt in buy_counts.index]
        ordered_buy.extend(sorted(opt for opt in buy_counts.index if opt not in SURVEY_BUY_WARUNG_OPTIONS))
        buy_counts = buy_counts.reindex(ordered_buy)
        buy_color_map = {
            "Ya": "#16a34a",
            "Tidak": "#dc2626",
            "Pikir-Pikir": "#f59e0b",
            "Tidak Diisi": "#94a3b8",
        }
        buy_colors = [buy_color_map.get(lbl, "#3b82f6") for lbl in buy_counts.index]
        ya_buy = int(buy_counts.get("Ya", 0))
        _render_donut_with_center_kpi(
            values=buy_counts.values.tolist(),
            labels=buy_counts.index.tolist(),
            title="Bersedia Beli di Warung/Toko/Minimarket",
            kpi_value=f"{ya_buy}/{int(buy_counts.sum())}",
            kpi_sublabel="Responden 'Ya'",
            colors=buy_colors,
            figsize=(7.2, 5.2),
        )

    with c_long:
        long_col = "Beralih Konsumsi Jangka Panjang"
        long_series = survey_df[long_col].fillna("").astype(str).str.strip().replace("", "Tidak Diisi")
        long_counts = long_series.value_counts()
        ordered_long = [opt for opt in SURVEY_LONG_TERM_OPTIONS if opt in long_counts.index]
        ordered_long.extend(sorted(opt for opt in long_counts.index if opt not in SURVEY_LONG_TERM_OPTIONS))
        long_counts = long_counts.reindex(ordered_long)
        long_color_map = {
            "Ya (Jadi Rokok Utama)": "#15803d",
            "Belum Tentu (Jadi Rokok Selingan)": "#f59e0b",
            "Tidak Sama sekali": "#dc2626",
            "Tidak Diisi": "#94a3b8",
        }
        long_colors = [long_color_map.get(lbl, "#3b82f6") for lbl in long_counts.index]
        utama_count = int(long_counts.get("Ya (Jadi Rokok Utama)", 0))
        _render_donut_with_center_kpi(
            values=long_counts.values.tolist(),
            labels=long_counts.index.tolist(),
            title="Beralih Konsumsi Jangka Panjang",
            kpi_value=f"{utama_count}/{int(long_counts.sum())}",
            kpi_sublabel="Jadi Rokok Utama",
            colors=long_colors,
            figsize=(7.2, 5.2),
        )

    st.markdown("---")
    st.subheader("🎯 Kesimpulan Acceptable D.76 Aksara Berdasarkan BUMO")
    st.caption(
        "Kriteria: Jika jumlah respon positif > respon negatif maka D.76 Aksara Diterima; "
        "jika respon negatif > respon positif maka Tidak Diterima."
    )
    bumo_summary = build_bumo_acceptability_summary(survey_df)
    if not bumo_summary.empty:
        status_respondent_totals = (
            bumo_summary.groupby("Status Acceptable D.76 Aksara", sort=False)["Jumlah Responden"]
            .sum()
        )
        accepted_respondents = int(status_respondent_totals.get("Diterima", 0))
        rejected_respondents = int(status_respondent_totals.get("Tidak Diterima", 0))
        tie_respondents = int(status_respondent_totals.get("Imbang / Perlu Evaluasi", 0))
        total_bumo_respondents = int(bumo_summary["Jumlah Responden"].sum())

        k1, k2, k3 = st.columns(3)
        k1.metric("Responden BUMO Diterima", accepted_respondents)
        k2.metric("Responden BUMO Tidak Diterima", rejected_respondents)
        k3.metric("Responden BUMO Imbang", tie_respondents)

        st.dataframe(
            bumo_summary[[
                "BUMO Rokok Konsumen",
                "Jumlah Responden",
                "Respon Positif",
                "Respon Negatif",
                "Selisih (Pos - Neg)",
                "Status Acceptable D.76 Aksara",
            ]],
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("#### 🍩 Donut + Center KPI Penerimaan D.76 Aksara Berdasarkan Jumlah Responden BUMO")
        status_color_map = {
            "Diterima": "#16a34a",
            "Tidak Diterima": "#dc2626",
            "Imbang / Perlu Evaluasi": "#f59e0b",
        }
        status_colors = [status_color_map.get(lbl, "#3b82f6") for lbl in status_respondent_totals.index]
        _render_donut_with_center_kpi(
            values=status_respondent_totals.values.tolist(),
            labels=status_respondent_totals.index.tolist(),
            title="Proporsi Responden per Status Penerimaan BUMO",
            kpi_value=f"{accepted_respondents}/{total_bumo_respondents}",
            kpi_sublabel="Responden Diterima",
            colors=status_colors,
            figsize=(7.5, 5.2),
        )

        st.markdown("##### Rincian per Rokok BUMO & Status Penerimaan D.76 Aksara")
        bumo_pie_labels = [
            f"{row['BUMO Rokok Konsumen']} [{row['Status Acceptable D.76 Aksara']}]"
            for _, row in bumo_summary.iterrows()
        ]
        bumo_pie_values = bumo_summary["Jumlah Responden"].tolist()
        detail_palette = ["#2563eb", "#16a34a", "#f59e0b", "#8b5cf6", "#ec4899", "#06b6d4", "#f97316", "#64748b"]
        detail_colors = [detail_palette[i % len(detail_palette)] for i in range(len(bumo_pie_values))]
        _render_donut_with_center_kpi(
            values=bumo_pie_values,
            labels=bumo_pie_labels,
            title="Proporsi Responden per Rokok BUMO & Status Penerimaan",
            kpi_value=total_bumo_respondents,
            kpi_sublabel="Total Responden",
            colors=detail_colors,
            figsize=(8.5, 5.8),
        )

        st.markdown("##### Rincian Kesimpulan per BUMO")
        for _, item in bumo_summary.iterrows():
            label = f"**{item['BUMO Rokok Konsumen']}** ({item['Jumlah Responden']} responden): {item['Kesimpulan']}"
            if item["Status Acceptable D.76 Aksara"] == "Diterima":
                st.success(label)
            elif item["Status Acceptable D.76 Aksara"] == "Tidak Diterima":
                st.error(label)
            else:
                st.info(label)

    st.markdown("---")
    _render_rounded_bar_highlight(SURVEY_ASPECTS, positive_counts, negative_counts)

    age_values = survey_df["Range Umur Konsumen"].fillna("").astype(str).str.strip()
    age_values = age_values.replace("", "Tidak diisi")
    age_aliases = {
        "18-24": "18-24 Tahun",
        "25-30": "25-30 Tahun",
        "31-34": "31-34 Tahun",
        "35+": "35+ Tahun",
    }
    age_counts = age_values.replace(age_aliases).value_counts()
    ordered_ages = [age for age in SURVEY_AGE_RANGES if age in age_counts.index]
    ordered_ages.extend(sorted(age for age in age_counts.index if age not in SURVEY_AGE_RANGES))
    age_counts = age_counts.reindex(ordered_ages)

    age_palette = ["#0ea5e9", "#22c55e", "#eab308", "#f97316", "#a855f7", "#94a3b8"]
    age_colors = [age_palette[i % len(age_palette)] for i in range(len(age_counts))]
    _render_donut_with_center_kpi(
        values=age_counts.values.tolist(),
        labels=age_counts.index.tolist(),
        title="Sebaran Range Umur Konsumen",
        kpi_value=int(age_counts.sum()),
        kpi_sublabel="Total Konsumen",
        colors=age_colors,
        figsize=(8.0, 5.5),
    )


def recap_page(df):
    st.title("📈 Rekapitulasi Harian & Mingguan (Report Table)")
    if df.empty:
        st.info("📭 Belum ada data untuk direkap.")
        return
    work = df.copy()
    work["Tanggal_DT"] = pd.to_datetime(work["Tanggal"], errors="coerce")
    zones = ["All Zona"] + sorted(set(PROMOTOR_ZONA.values()))
    c1, c2, c3, c4 = st.columns(4)
    zone = c1.selectbox("Pilih Zona", zones, key="rekap_zona")
    if zone != "All Zona":
        work = work[work["Zona"] == zone]
    promoters = ["All Promotor"] + sorted(work["Nama Promotor"].dropna().unique().tolist())
    promoter = c2.selectbox("Pilih Promotor", promoters, key="rekap_promotor")
    if promoter != "All Promotor":
        work = work[work["Nama Promotor"] == promoter]
    years = sorted(work["Tanggal_DT"].dropna().dt.year.unique(), reverse=True)
    if not years:
        st.info("📭 Belum ada tanggal laporan yang valid untuk filter yang dipilih.")
        return
    year = c3.selectbox("Pilih Tahun", years, key="rekap_thn")
    year_data = work[work["Tanggal_DT"].dt.year == year]
    weeks = sorted(year_data["Tanggal_DT"].dt.isocalendar().week.dropna().unique(), reverse=True)
    if not weeks:
        st.info("📭 Tidak ada data pada tahun yang dipilih.")
        return
    week = c4.selectbox("Pilih Minggu ke- (Week)", weeks, key="rekap_mg")
    week_data = year_data[year_data["Tanggal_DT"].dt.isocalendar().week == week].copy()
    weekdays = {0: "Senin", 1: "Selasa", 2: "Rabu", 3: "Kamis", 4: "Jumat"}
    week_data["Nama Hari"] = week_data["Tanggal_DT"].dt.weekday.map(weekdays)
    rows = {}
    for day in weekdays.values():
        day_df = week_data[week_data["Nama Hari"] == day]
        if day_df.empty:
            rows[day] = {"Tanggal": "-", "Total Armada": 0, "Call": 0, "Beli Ada": 0, "Beli Ks Tambah": 0, "Beli Ks Baru": 0, "TBA Aktif": 0, "TBA Pasif": 0, "Kosong": 0, "Total Omset": 0, "Average Dropsize": 0.0, "% Availability Sebelum": "0.0%", "% Availability Sesudah": "0.0%", "EC": 0, "% EC": "0.0%", "% Repeat": "0.0%", "% OOS": "0.0%", "% Outlet Ecer": "0.0%", "Total Sampling": 0, "Kontak Konsumen": 0, "Laku Direct Selling": 0}
            continue
        total = lambda column: day_df[column].fillna(0).sum()
        beli, ks_tb, ks_b = total("Outlet Beli Ada"), total("Outlet Ks Tb"), total("Outlet Ks B")
        tba_a, tba_p, kosong = total("Outlet TB Ada A"), total("Outlet TB Ada P"), total("Outlet TB Ks")
        call = beli + ks_tb + ks_b + tba_a + tba_p + kosong
        total_beli = beli + ks_tb + ks_b
        available = beli + tba_a + tba_p
        available_after = beli + ks_tb + ks_b + tba_a + tba_p
        repeat_denominator = beli + ks_tb + tba_a + tba_p
        rows[day] = {
            "Tanggal": datetime.strptime(day_df["Tanggal"].iloc[0], "%Y-%m-%d").strftime("%d/%m/%Y"),
            "Total Armada": day_df["Nama Promotor"].nunique(), "Call": call,
            "Beli Ada": beli, "Beli Ks Tambah": ks_tb, "Beli Ks Baru": ks_b,
            "TBA Aktif": tba_a, "TBA Pasif": tba_p, "Kosong": kosong,
            "Total Omset": total("Omset (Bungkus)"),
            "Average Dropsize": round(total("Omset (Bungkus)") / total_beli, 1) if total_beli else 0.0,
            "% Availability Sebelum": f"{round(available / call * 100, 1) if call else 0.0}%",
            "% Availability Sesudah": f"{round(available_after / call * 100, 1) if call else 0.0}%",
            "EC": total_beli, "% EC": f"{round(total_beli / call * 100, 1) if call else 0.0}%",
            "% Repeat": f"{round((beli + ks_tb) / repeat_denominator * 100, 1) if repeat_denominator else 0.0}%",
            "% OOS": f"{round(ks_tb / call * 100, 1) if call else 0.0}%",
            "% Outlet Ecer": f"{round(total('Outlet Buka Ecer') / call * 100, 1) if call else 0.0}%",
            "Total Sampling": total("Jumlah Rokok Sampling"), "Kontak Konsumen": total("Jumlah Konsumen Trial"),
            "Laku Direct Selling": total("Direct Selling"),
        }
    result = pd.DataFrame(rows)
    title_zone = f"Zona {zone}" if zone != "All Zona" else "All Zona"
    title_promoter = f" — {promoter}" if promoter != "All Promotor" else ""
    title = f"Laporan Rekapitulasi {title_zone}{title_promoter} - Minggu ke {week} - {year}"
    st.markdown(f"#### {title}")
    if os.path.exists("76aksara.png"):
        st.image("76aksara.png", use_container_width=True)
    st.table(result)
    st.markdown("#### 📥 Unduh Rekap Laporan sebagai Gambar")
    fig, ax = plt.subplots(figsize=(18, 12), facecolor="white")
    ax.axis("off")
    table = ax.table(cellText=result.values, rowLabels=result.index, colLabels=result.columns, loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.8)
    png = BytesIO()
    fig.savefig(png, format="png", bbox_inches="tight", dpi=180, facecolor="white")
    plt.close(fig)
    png.seek(0)
    jpg = BytesIO()
    PILImage.open(png).convert("RGB").save(jpg, format="JPEG", quality=95)
    safe_filter = promoter.replace(" ", "_") if promoter != "All Promotor" else "all_promotor"
    d1, d2 = st.columns(2)
    d1.download_button("📷 Download PNG", png.getvalue(), file_name=f"rekap_kanvas_{zone.replace(' ', '_')}_{safe_filter}_minggu{week}_{year}.png", mime="image/png", key="dl_rekap_png")
    d2.download_button("🖼️ Download JPEG", jpg.getvalue(), file_name=f"rekap_kanvas_{zone.replace(' ', '_')}_{safe_filter}_minggu{week}_{year}.jpg", mime="image/jpeg", key="dl_rekap_jpeg")


def log_page(df):
    st.title("📊 Panel Admin & Log Laporan Kanvas (Semua Data)")
    if df.empty:
        st.info("📭 Belum ada data laporan kanvas yang tercatat.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)


def admin_protected_data_actions(df, today):
    st.markdown("---")
    st.subheader("🗑️ Hapus Per Baris, Unduh Laporan, & Hapus Data")

    st.markdown("#### 🗑️ Hapus Data Per Baris")
    delete_id = st.selectbox(
        "Pilih laporan yang akan dihapus:",
        df["ID"].tolist(),
        format_func=lambda value: f"ID #{value} — {df.loc[df['ID'] == value, 'Tanggal'].iloc[0]} — {df.loc[df['ID'] == value, 'Nama Promotor'].iloc[0]}",
        key="delete_single_report_id",
    )
    with st.form("form_hapus_satu_laporan"):
        confirm_single_delete = st.checkbox("Saya yakin ingin menghapus laporan yang dipilih.")
        delete_single = st.form_submit_button("🗑️ Hapus Laporan Terpilih", type="secondary")
    if delete_single:
        if not confirm_single_delete:
            st.error("Centang konfirmasi sebelum menghapus laporan.")
        else:
            with sqlite3.connect(DB_NAME) as conn:
                conn.execute("DELETE FROM kanvas WHERE id = ?", (int(delete_id),))
            st.session_state["notifikasi_sukses"] = f"🗑️ Laporan ID #{delete_id} berhasil dihapus."
            st.rerun()

    st.markdown("#### 📥 Unduh Laporan")
    scope = st.selectbox("Pilih Rentang Data:", ["Semua Data", "Hari Ini"], key="download_scope")
    exported = df[df["Tanggal"] == today] if scope == "Hari Ini" else df.copy()
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        exported.to_excel(writer, index=False, sheet_name="Laporan Kanvas")
    st.download_button(
        f"💾 Download Excel ({scope})",
        output.getvalue(),
        file_name=f"laporan_kanvas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.markdown("#### 🗑️ Hapus Data")
    delete_scope = st.selectbox("Pilih Data yang Dihapus:", ["Hari Ini", "Semua Data"], key="opt_hapus")
    confirm = st.checkbox("Saya memahami data yang dipilih akan dihapus permanen.")
    if st.button("🔥 Hapus Data", type="secondary", disabled=not confirm):
        with sqlite3.connect(DB_NAME) as conn:
            if delete_scope == "Hari Ini":
                conn.execute("DELETE FROM kanvas WHERE tanggal = ?", (today,))
            else:
                conn.execute("DELETE FROM kanvas")
        st.success("🗑️ Data berhasil dihapus.")
        st.rerun()


def management_page(df, today, is_admin=True, locked_promoter=None):
    st.title("✏️ Edit Laporan Kanvas" if not is_admin else "🛠️ Manajemen Data (Edit, Unduh, & Hapus)")
    work_df = df if is_admin else df[df["Nama Promotor"] == locked_promoter]
    if work_df.empty:
        st.info("📭 Belum ada data laporan kanvas yang dapat di-edit.")
        return

    st.markdown("#### ✏️ Pilih laporan yang akan dikoreksi")
    selected_id = st.selectbox(
        "Pilih ID Data yang Ingin Di-edit:",
        work_df["ID"].tolist(),
        format_func=lambda value: (
            f"ID #{value} — {work_df.loc[work_df['ID'] == value, 'Tanggal'].iloc[0]} "
            f"— {work_df.loc[work_df['ID'] == value, 'Nama Promotor'].iloc[0]}"
        ),
    )
    row = work_df[work_df["ID"] == selected_id].iloc[0]
    st.markdown("##### Data sebelumnya")
    st.dataframe(row.to_frame().T, use_container_width=True, hide_index=True)
    st.markdown("##### Form Edit Laporan")
    with st.form("form_edit_kanvas"):
        c1, c2 = st.columns(2)
        with c1:
            raw_date = pd.to_datetime(row["Tanggal"], errors="coerce")
            edit_date = st.date_input("Date", value=raw_date.date() if pd.notna(raw_date) else datetime.now(TZ_WIB).date())
            if is_admin:
                promoters = list(PROMOTOR_ZONA)
                edit_promoter = st.selectbox(
                    "Nama Promotor",
                    promoters,
                    index=promoters.index(row["Nama Promotor"]) if row["Nama Promotor"] in promoters else 0,
                )
            else:
                edit_promoter = locked_promoter
                st.text_input("Nama Promotor", value=edit_promoter, disabled=True)
            brands = ["Djarum 76 Aksara"]
            edit_brand = st.selectbox("Brand", brands, index=brands.index(row["Brand"]) if row["Brand"] in brands else 0)
        with c2:
            st.text_input("Zona (Otomatis)", value=PROMOTOR_ZONA.get(edit_promoter, "-"), disabled=True)
            edit_values = {
                "canvas_plan": st.number_input("Canvas Plan", min_value=0, step=1, value=int(row["Canvas Plan"] or 0)),
                "omset_bungkus": st.number_input("Omset (bungkus)", min_value=0, step=1, value=int(row["Omset (Bungkus)"] or 0)),
            }
        st.markdown("#### 🏪 Rincian Outlet")
        edit_cols = st.columns(3)
        for index, key in enumerate(OUTLET_KEYS):
            with edit_cols[index % 3]:
                edit_values[key] = st.number_input(FIELD_LABELS[key], min_value=0, step=1, value=int(row[FIELD_LABELS[key]] or 0), key=f"edit_{selected_id}_{key}")
        st.markdown("#### 🎁 Rincian Promosi dan Aktivitas")
        promo_cols = st.columns(3)
        for index, key in enumerate(PROMOTION_KEYS):
            with promo_cols[index % 3]:
                edit_values[key] = st.number_input(FIELD_LABELS[key], min_value=0, step=1, value=int(row[FIELD_LABELS[key]] or 0), key=f"edit_{selected_id}_{key}")
        update = st.form_submit_button("💾 Perbarui Data", type="primary")
    if update:
        columns = ["tanggal", "nama_promotor", "zona", "brand", *FIELD_LABELS]
        values = [edit_date.strftime("%Y-%m-%d"), edit_promoter, PROMOTOR_ZONA[edit_promoter], edit_brand, *[int(edit_values[key]) for key in FIELD_LABELS], int(selected_id)]
        with sqlite3.connect(DB_NAME) as conn:
            conn.execute(f"UPDATE kanvas SET {', '.join(f'{column} = ?' for column in columns)} WHERE id = ?", values)
        st.session_state["notifikasi_sukses"] = f"✏️ Data ID #{selected_id} berhasil diperbarui!"
        st.rerun()

    if is_admin:
        admin_protected_data_actions(df, today)


def backup_restore_page(df):
    st.title("☁️ Backup & Restore Google Sheets")
    st.markdown("---")
    st.subheader("📥 Restore Data dari Google Sheets")
    st.write(
        "Menarik ulang seluruh data **Laporan Kanvas** (`DataKanvasAksara`) dan **Survey Konsumen** (`SurveyKonsumen`) "
        "dari Google Sheets ke database lokal aplikasi."
    )
    confirm_restore = st.checkbox(
        "Saya memahami bahwa database lokal saat ini akan ditimpa dengan data terbaru dari Google Sheets.",
        key="confirm_manual_restore",
    )
    if st.button("📥 Restore Sekarang dari Google Sheets", type="primary", disabled=not confirm_restore):
        with st.spinner("Sedang mengambil data dari Google Sheets..."):
            ok, msg = restore_from_google_sheets()
        if ok:
            st.session_state["last_restore_time"] = datetime.now(TZ_WIB).strftime("%Y-%m-%d %H:%M:%S")
            st.session_state["notifikasi_sukses"] = f"✅ {msg}"
            st.rerun()
        else:
            st.error(f"❌ {msg}")

    st.markdown("---")
    st.subheader("📤 Backup Data Lokal ke Google Sheets")
    st.write("Gunakan tombol di bawah ini untuk menimpa seluruh data di sheet **`DataKanvasAksara`** dengan data laporan kanvas lokal.")
    if st.button("🔄 Kirim/Backup Semua Data Kanvas ke Google Sheets", type="secondary"):
        rows_payload = []
        if not df.empty:
            for _, row in df.iterrows():
                item = {
                    "id": int(row["ID"]),
                    "tanggal": str(row["Tanggal"]),
                    "nama_promotor": str(row["Nama Promotor"]),
                    "zona": str(row["Zona"]),
                    "brand": str(row["Brand"]),
                }
                for key, label in FIELD_LABELS.items():
                    item[key] = int(row[label] or 0)
                item["waktu_submit"] = str(row["Waktu Submit"])
                rows_payload.append(item)

        payload = {
            "type": "kanvas_backup",
            "action": "replace_all",
            "rows": rows_payload,
        }
        try:
            response = requests.post(WEBHOOK_URL, json=payload, timeout=25)
            response.raise_for_status()
            res_json = response.json()
            if isinstance(res_json, dict) and res_json.get("status") == "success":
                st.success(f"✅ Berhasil menimpa & mem-backup {len(rows_payload)} data ke sheet DataKanvasAksara!")
            else:
                st.error(f"❌ Backup gagal: {res_json}")
        except requests.RequestException as err:
            st.error(f"❌ Gagal menghubungi Google Sheets: {err}")
        except ValueError:
            st.error("❌ Respons backup dari Google Sheets bukan JSON yang valid.")


init_db()

# Auto-restore setiap kali aplikasi dibuka atau halaman di-refresh
if not st.session_state.get("initial_restore_done", False):
    with st.spinner("Menyinkronkan data terbaru dari Google Sheets..."):
        ok, msg = restore_from_google_sheets()
    st.session_state["initial_restore_status"] = (ok, msg)
    if ok:
        st.session_state["initial_restore_done"] = True
        st.session_state["last_restore_time"] = datetime.now(TZ_WIB).strftime("%Y-%m-%d %H:%M:%S")

now = datetime.now(TZ_WIB)
today = now.strftime("%Y-%m-%d")

if "notifikasi_sukses" in st.session_state:
    st.balloons()
    st.success(st.session_state.pop("notifikasi_sukses"))
if "notifikasi_error" in st.session_state:
    st.error(st.session_state.pop("notifikasi_error"))

# Gerbang Login
auth_role = st.session_state.get("auth_role")
if auth_role not in ("promotor", "admin"):
    login_page()
    st.stop()

is_admin = auth_role == "admin"
logged_promoter = st.session_state.get("auth_promotor")
promotor_module = st.session_state.get("promotor_assigned_module", "kanvas")

# Sidebar User Card & Status Sinkronisasi
if is_admin:
    st.sidebar.markdown("""
    <div class="user-pill">
        <div class="role-tag admin">🔐 Administrator</div>
        <div class="user-name">Admin Pusat</div>
        <div class="user-sub">Akses Penuh • Kanvas & Survey</div>
    </div>
    """, unsafe_allow_html=True)
else:
    zona_user = PROMOTOR_ZONA.get(logged_promoter, "-")
    modul_label = "Survey Konsumen" if promotor_module == "survey" else "Entry Laporan Kanvas"
    st.sidebar.markdown(f"""
    <div class="user-pill">
        <div class="role-tag">🧑‍💼 Promotor</div>
        <div class="user-name">{logged_promoter}</div>
        <div class="user-sub">📍 Zona {zona_user} • {modul_label}</div>
    </div>
    """, unsafe_allow_html=True)

restore_ok, restore_msg = st.session_state.get("initial_restore_status", (False, ""))
if restore_ok:
    st.sidebar.caption(f"🟢 Sync Google Sheets: {st.session_state.get('last_restore_time', '-')}")
elif restore_msg:
    st.sidebar.warning(f"⚠️ Auto-restore gagal: {restore_msg}")

st.sidebar.markdown("---")

# Navigasi berdasarkan Role & Pilihan Login
if is_admin:
    active_module = st.sidebar.radio(
        "Modul Utama:",
        ["📋 Laporan Kanvas", "🗣️ Survey Konsumen"],
        index=0 if st.session_state.get("active_page", "Laporan Kanvas") == "Laporan Kanvas" else 1,
        key="admin_module_switcher",
    )
    st.session_state["active_page"] = "Laporan Kanvas" if "Laporan Kanvas" in active_module else "Survey Konsumen"
    st.sidebar.markdown("---")

    if st.session_state["active_page"] == "Survey Konsumen":
        survey_menu = st.sidebar.radio(
            "Sub-Menu Survey:",
            ["Entry Survey", "Log Entry Survey", "Monitoring Survey"],
            key="survey_navigation_admin",
        )
        menu = "Survey Konsumen"
    else:
        menu = st.sidebar.radio("Sub-Menu Laporan Kanvas:", [
            "Form Entry Laporan Kanvas",
            "Manajemen Data (Edit, Unduh, & Hapus)",
            "Rekapitulasi Harian & Mingguan (Report Table)",
            "Panel Admin & Log Laporan Kanvas (Semua Data)",
            "Backup & Restore Google Sheets",
        ])
else:
    if promotor_module == "survey":
        survey_menu = st.sidebar.radio(
            "Menu Survey Konsumen:",
            ["Entry Survey", "Log Entry Survey"],
            key="survey_navigation_promotor",
        )
        menu = "Survey Konsumen"
    else:
        menu = st.sidebar.radio(
            "Menu Laporan Kanvas:",
            ["Form Entry Laporan Kanvas", "Edit Laporan"],
            key="kanvas_navigation_promotor",
        )

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Keluar / Ganti Akun", key="btn_logout"):
    for key in ("auth_role", "auth_promotor", "promotor_assigned_module", "active_page", "form_preview_data"):
        st.session_state.pop(key, None)
    st.rerun()

# Routing Halaman
if menu == "Form Entry Laporan Kanvas":
    st.markdown("""
    <div class="hero-header">
        <div class="hero-badge">Field Sales Operation • Djarum 76 Aksara</div>
        <h1>📋 Form Entry Laporan Kanvas</h1>
        <p>Sistem Perekaman Data Kanvas, Distribusi Outlet, & Aktivitas Promosi Lapangan.</p>
    </div>
    """, unsafe_allow_html=True)
    report_form(locked_promoter=None if is_admin else logged_promoter)
    st.markdown("---")
    daily_status(load_data(), today)

elif menu in ("Edit Laporan", "Manajemen Data (Edit, Unduh, & Hapus)"):
    management_page(
        load_data(),
        today,
        is_admin=is_admin,
        locked_promoter=None if is_admin else logged_promoter,
    )

elif menu == "Survey Konsumen":
    if survey_menu == "Entry Survey":
        consumer_survey_entry_page(locked_promoter=None if is_admin else logged_promoter)
    elif survey_menu == "Log Entry Survey":
        survey_log_page(is_admin=is_admin, locked_promoter=None if is_admin else logged_promoter)
    elif survey_menu == "Monitoring Survey" and is_admin:
        survey_monitoring_page()

elif menu == "Rekapitulasi Harian & Mingguan (Report Table)" and is_admin:
    recap_page(load_data())

elif menu == "Panel Admin & Log Laporan Kanvas (Semua Data)" and is_admin:
    log_page(load_data())

elif menu == "Backup & Restore Google Sheets" and is_admin:
    backup_restore_page(load_data())
