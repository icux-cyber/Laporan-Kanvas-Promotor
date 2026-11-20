from datetime import datetime
from io import BytesIO
import json
import os
import sqlite3

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import pytz
import requests
import streamlit as st
from PIL import Image as PILImage


TZ_WIB = pytz.timezone("Asia/Jakarta")
DB_NAME = "laporan_kanvas.db"
BRAND_DATA_FILE = "Merk_Rokok_All_Pabrikan_&_Nama_Karyawan.json"
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxQo1RhqgAoGrZFmwzobcLfOxnR7S_g7kj0S2RHTS4czCm1fA3HqvHdebcinBLlYq8/exec"
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
]
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

st.set_page_config(page_title="Form Entry Laporan Kanvas", page_icon="📋", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
.stApp { background-color: #f8fafc; }
h1, h2, h3 { color: #0f172a; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
.stButton>button { border-radius: 8px; font-weight: 600; width: 100%; }
div[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; border: 1px solid #e2e8f0; }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_bumo_options():
    if not os.path.exists(BRAND_DATA_FILE):
        return ["", "Lainnya"]
    try:
        with open(BRAND_DATA_FILE, "r", encoding="utf-8") as file:
            payload = json.load(file)
    except (OSError, json.JSONDecodeError):
        return ["", "Lainnya"]

    raw_brands = payload.get("daftar_merk_rokok", []) if isinstance(payload, dict) else []
    unique_brands = [""]
    seen = {""}
    for item in raw_brands:
        if isinstance(item, str):
            cleaned = item.strip()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                unique_brands.append(cleaned)
    if "Lainnya" not in seen:
        unique_brands.append("Lainnya")
    return unique_brands


def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS kanvas (
            id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, nama_promotor TEXT,
            zona TEXT, brand TEXT, canvas_plan INTEGER, outlet_beli_ada INTEGER,
            outlet_ks_tb INTEGER, outlet_ks_b INTEGER, outlet_tb_ada_a INTEGER,
            outlet_tb_ada_p INTEGER, outlet_tb_ks INTEGER, omset_bungkus INTEGER,
            promsus_10_1 INTEGER DEFAULT 0, promsus_3_1 INTEGER DEFAULT 0,
            promsus_2_1 INTEGER DEFAULT 0, promsus_1_1 INTEGER DEFAULT 0,
            promsus_n_mie_instan INTEGER DEFAULT 0, outlet_buka_ecer INTEGER DEFAULT 0,
            jumlah_rokok_sampling INTEGER DEFAULT 0, jumlah_konsumen_trial INTEGER DEFAULT 0,
            direct_selling INTEGER DEFAULT 0, waktu_submit TEXT
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS survey_konsumen (
            id INTEGER PRIMARY KEY AUTOINCREMENT, waktu_survey TEXT NOT NULL,
            nama_promotor TEXT NOT NULL, sektor_survey TEXT, nama_konsumen TEXT,
            range_usia_konsumen TEXT, pekerjaan_konsumen TEXT,
            bumo_rokok_konsumen TEXT, tahu_76_aksara TEXT, sumber_info_76_aksara TEXT,
            komentar_positif TEXT, komentar_negatif TEXT
        )""")
        survey_columns = {row[1] for row in conn.execute("PRAGMA table_info(survey_konsumen)")}
        for extra_col in ("tahu_76_aksara", "sumber_info_76_aksara"):
            if extra_col not in survey_columns:
                conn.execute(f"ALTER TABLE survey_konsumen ADD COLUMN {extra_col} TEXT")
                survey_columns.add(extra_col)
        legacy_comments = {
            "komentar_positif_lainnya": "komentar_positif",
            "komentar_negatif_lainnya": "komentar_negatif",
        }
        for column in SURVEY_FEEDBACK_FIELDS.values():
            if column not in survey_columns:
                conn.execute(f"ALTER TABLE survey_konsumen ADD COLUMN {column} TEXT")
                survey_columns.add(column)
                legacy_column = legacy_comments.get(column)
                if legacy_column and legacy_column in survey_columns:
                    conn.execute(
                        f"""UPDATE survey_konsumen SET {column} = {legacy_column}
                        WHERE {legacy_column} IS NOT NULL AND TRIM({legacy_column}) != ''"""
                    )
        columns = {row[1] for row in conn.execute("PRAGMA table_info(kanvas)")}
        if "pic" in columns and "nama_promotor" not in columns:
            conn.execute("ALTER TABLE kanvas RENAME COLUMN pic TO nama_promotor")
            columns.remove("pic")
            columns.add("nama_promotor")
        additions = {"nama_promotor": "TEXT", "zona": "TEXT"}
        additions.update({name: "INTEGER DEFAULT 0" for name in FIELD_LABELS if name not in ("canvas_plan", "omset_bungkus")})
        for name, kind in additions.items():
            if name not in columns:
                conn.execute(f"ALTER TABLE kanvas ADD COLUMN {name} {kind}")


def _safe_int(value, default=0):
    try:
        if value is None or str(value).strip() == "":
            return default
        return int(float(value))
    except (ValueError, TypeError):
        return default


def restore_from_google_sheets():
    """Mengambil seluruh data DataKanvasAksara & SurveyKonsumen dari Google Sheets dan menimpa database lokal."""
    try:
        response = requests.get(
            WEBHOOK_URL,
            params={"action": "restore", "_ts": int(datetime.now(TZ_WIB).timestamp())},
            timeout=25,
        )
        response.raise_for_status()
    except requests.RequestException as err:
        return False, f"Gagal menghubungi Google Sheets: {err}"

    raw_text = response.text or ""
    try:
        payload = response.json()
    except ValueError:
        return False, f"Respons bukan JSON (HTTP {response.status_code}): {raw_text[:250]}"

    if not isinstance(payload, dict):
        return False, f"Format JSON tidak berupa object: {raw_text[:250]}"

    if payload.get("status") != "success":
        msg = payload.get("message", "Gagal mengambil data dari Google Sheets.")
        return False, f"{msg} | Payload: {str(payload)[:250]}"

    if "kanvas" not in payload or "survey_konsumen" not in payload:
        return False, f"Key 'kanvas'/'survey_konsumen' tidak ada. Key yang diterima: {list(payload.keys())}"

    kanvas_rows = payload.get("kanvas") or []
    survey_rows = payload.get("survey_konsumen") or []

    kanvas_cols = ["id", "tanggal", "nama_promotor", "zona", "brand", *FIELD_LABELS.keys(), "waktu_submit"]
    survey_cols = [
        "id", "waktu_survey", "nama_promotor", "sektor_survey", "nama_konsumen",
        "range_usia_konsumen", "pekerjaan_konsumen", "bumo_rokok_konsumen",
        "tahu_76_aksara", "sumber_info_76_aksara",
        *SURVEY_FEEDBACK_FIELDS.values(),
    ]

    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("DELETE FROM kanvas")
        conn.execute("DELETE FROM sqlite_sequence WHERE name='kanvas'")
        for idx, row in enumerate(kanvas_rows, start=1):
            if not isinstance(row, dict):
                continue
            if not str(row.get("tanggal", "")).strip() and not str(row.get("nama_promotor", "")).strip():
                continue
            row_id = _safe_int(row.get("id"), default=idx)
            values = [
                row_id,
                str(row.get("tanggal", "")).strip(),
                str(row.get("nama_promotor", "")).strip(),
                str(row.get("zona", "")).strip(),
                str(row.get("brand", "")).strip(),
                *[_safe_int(row.get(k), 0) for k in FIELD_LABELS.keys()],
                str(row.get("waktu_submit", "")).strip(),
            ]
            conn.execute(
                f"INSERT OR REPLACE INTO kanvas ({', '.join(kanvas_cols)}) VALUES ({', '.join('?' for _ in kanvas_cols)})",
                values,
            )

        conn.execute("DELETE FROM survey_konsumen")
        conn.execute("DELETE FROM sqlite_sequence WHERE name='survey_konsumen'")
        for idx, row in enumerate(survey_rows, start=1):
            if not isinstance(row, dict):
                continue
            if not str(row.get("waktu_survey", "")).strip() and not str(row.get("nama_konsumen", "")).strip():
                continue
            row_id = _safe_int(row.get("id"), default=idx)
            values = [
                row_id,
                str(row.get("waktu_survey", "")).strip(),
                str(row.get("nama_promotor", "")).strip(),
                str(row.get("sektor_survey", "")).strip(),
                str(row.get("nama_konsumen", "")).strip(),
                str(row.get("range_usia_konsumen", "")).strip(),
                str(row.get("pekerjaan_konsumen", "")).strip(),
                str(row.get("bumo_rokok_konsumen", "")).strip(),
                str(row.get("tahu_76_aksara", "")).strip(),
                str(row.get("sumber_info_76_aksara", "")).strip(),
                *[str(row.get(col, "") or "").strip() for col in SURVEY_FEEDBACK_FIELDS.values()],
            ]
            conn.execute(
                f"INSERT OR REPLACE INTO survey_konsumen ({', '.join(survey_cols)}) VALUES ({', '.join('?' for _ in survey_cols)})",
                values,
            )

    return True, f"Berhasil restore {len(kanvas_rows)} data kanvas (DataKanvasAksara) & {len(survey_rows)} data survey dari Google Sheets."
    
def load_data():
    with sqlite3.connect(DB_NAME) as conn:
        return pd.read_sql_query("""SELECT id AS ID, tanggal AS Tanggal,
            nama_promotor AS [Nama Promotor], zona AS Zona, brand AS Brand,
            canvas_plan AS [Canvas Plan], outlet_beli_ada AS [Outlet Beli Ada],
            outlet_ks_tb AS [Outlet Ks Tb], outlet_ks_b AS [Outlet Ks B],
            outlet_tb_ada_a AS [Outlet TB Ada A], outlet_tb_ada_p AS [Outlet TB Ada P],
            outlet_tb_ks AS [Outlet TB Ks], omset_bungkus AS [Omset (Bungkus)],
            promsus_10_1 AS [Promsus 10+1], promsus_3_1 AS [Promsus 3+1],
            promsus_2_1 AS [Promsus 2+1], promsus_1_1 AS [Promsus 1+1],
            promsus_n_mie_instan AS [N+ Mie Instan], outlet_buka_ecer AS [Outlet Buka Ecer],
            jumlah_rokok_sampling AS [Jumlah Rokok Sampling],
            jumlah_konsumen_trial AS [Jumlah Konsumen Trial],
            direct_selling AS [Direct Selling], waktu_submit AS [Waktu Submit]
            FROM kanvas ORDER BY waktu_submit DESC""", conn)


def load_survey_data():
    with sqlite3.connect(DB_NAME) as conn:
        feedback_columns = ", ".join(
            f"{column} AS [{label}]" for label, column in SURVEY_FEEDBACK_FIELDS.items()
        )
        return pd.read_sql_query(f"""SELECT id AS ID, waktu_survey AS [Waktu Survey],
            nama_promotor AS [Nama Promotor], sektor_survey AS [Sektor Survey],
            nama_konsumen AS [Nama Konsumen], range_usia_konsumen AS [Range Umur Konsumen],
            pekerjaan_konsumen AS [Pekerjaan Konsumen],
            bumo_rokok_konsumen AS [BUMO Rokok Konsumen],
            tahu_76_aksara AS [Mengetahui Djarum 76 Aksara],
            sumber_info_76_aksara AS [Sumber Info Djarum 76 Aksara],
            {feedback_columns}
            FROM survey_konsumen ORDER BY waktu_survey DESC""", conn)


def save_report(data):
    columns = ["tanggal", "nama_promotor", "zona", "brand", *FIELD_LABELS, "waktu_submit"]
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.execute(
            f"INSERT INTO kanvas ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})",
            [data[key] for key in columns],
        )
        data_with_id = {"id": int(cursor.lastrowid), **data}
    try:
        requests.post(WEBHOOK_URL, json=data_with_id, timeout=10).raise_for_status()
    except requests.RequestException:
        pass


def sync_survey_to_sheets(action, survey):
    payload = {"type": "survey_konsumen", "action": action}
    if action == "upsert":
        payload.update(survey)
    elif action == "delete":
        payload["id"] = int(survey)
    else:
        raise ValueError(f"Aksi sinkronisasi survey tidak dikenal: {action}")

    try:
        capability_response = requests.get(WEBHOOK_URL, timeout=10)
    except requests.RequestException as error:
        raise RuntimeError("Tidak dapat memeriksa dukungan survey pada webhook Google Sheets.") from error
    if not capability_response.ok:
        raise RuntimeError(
            f"Pemeriksaan webhook Google Sheets merespons HTTP {capability_response.status_code}."
        )
    try:
        capability = capability_response.json()
    except ValueError as error:
        raise RuntimeError(
            "Webhook belum mendukung sinkronisasi survey. Deploy GoogleAppsScript.gs terlebih dahulu."
        ) from error
    if not isinstance(capability, dict) or capability.get("survey_sync_version") != 1:
        raise RuntimeError(
            "Webhook belum mendukung sinkronisasi survey. Deploy GoogleAppsScript.gs terlebih dahulu."
        )

    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
    except requests.RequestException as error:
        raise RuntimeError("Tidak dapat menghubungi webhook Google Sheets.") from error
    if not response.ok:
        raise RuntimeError(f"Webhook Google Sheets merespons HTTP {response.status_code}.")
    try:
        result = response.json()
    except ValueError as error:
        raise RuntimeError("Respons webhook Google Sheets bukan JSON yang valid.") from error
    if not isinstance(result, dict) or result.get("status") != "success":
        message = result.get("message", "Permintaan survey ditolak.") if isinstance(result, dict) else "Respons webhook tidak valid."
        raise RuntimeError(message)
    if result.get("type") != "survey_konsumen" or result.get("action") != action:
        raise RuntimeError("Respons webhook tidak mengonfirmasi sinkronisasi survey yang diminta.")


def report_form():
    st.subheader("📝 Masukkan Data Laporan Baru")
    version = st.session_state.get("entry_form_version", 0)
    with st.form("form_laporan_kanvas"):
        c1, c2 = st.columns(2)
        with c1:
            date_value = st.date_input("Date", value=datetime.now(TZ_WIB).date(), key=f"entry_date_{version}")
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


def consumer_survey_entry_page():
    st.title("📝 Entry Survey Konsumen")
    version = st.session_state.get("survey_form_version", 0)
    bumo_options = load_bumo_options()

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

    with st.form(f"form_survey_konsumen_{version}"):
        positive_comments = {}
        negative_comments = {}
        positive_column, negative_column = st.columns(2)
        with positive_column:
            st.markdown("#### Komentar Positif dari Rokok yang Dicoba")
            for aspect in SURVEY_ASPECTS:
                label = f"Komentar Positif - {aspect}"
                key = SURVEY_FEEDBACK_FIELDS[label]
                positive_comments[key] = st.text_area(
                    label, key=f"survey_{key}_{version}",
                )
        with negative_column:
            st.markdown("#### Komentar Negatif dari Rokok yang Dicoba")
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
            *SURVEY_FEEDBACK_FIELDS.values(),
        ]
        values = [
            datetime.now(TZ_WIB).strftime("%Y-%m-%d %H:%M:%S"),
            nama_promotor, sektor_survey.strip(), nama_konsumen.strip(),
            range_usia, pekerjaan.strip(), bumo,
            tahu_76_aksara, sumber_info_str,
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


def survey_log_page():
    st.title("📋 Log Entry Survey Konsumen")
    survey_df = load_survey_data()
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


def survey_monitoring_page():
    st.title("📊 Monitoring Survey Konsumen")
    survey_df = load_survey_data()
    if survey_df.empty:
        st.info("📭 Belum ada data survey untuk dimonitor.")
        return

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

    positions = range(len(SURVEY_ASPECTS))
    width = 0.36
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar([position - width / 2 for position in positions], positive_counts, width, label="Positif")
    ax.bar([position + width / 2 for position in positions], negative_counts, width, label="Negatif")
    ax.set_xticks(list(positions))
    ax.set_xticklabels(SURVEY_ASPECTS)
    ax.set_ylabel("Jumlah komentar")
    ax.set_title("Komentar per Aspek Rokok")
    ax.legend()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

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

    age_fig, age_ax = plt.subplots(figsize=(8, 6))
    age_ax.pie(
        age_counts.values,
        labels=age_counts.index,
        autopct="%1.1f%%",
        startangle=90,
    )
    age_ax.set_title("Sebaran Range Umur Konsumen")
    age_ax.axis("equal")
    st.pyplot(age_fig)
    plt.close(age_fig)


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


def management_page(df, today):
    st.title("🛠️ Manajemen Data (Edit, Unduh, & Hapus)")
    if df.empty:
        st.info("📭 Belum ada data laporan kanvas yang tercatat.")
        return
    st.markdown("#### ✏️ Pilih laporan yang akan dikoreksi")
    selected_id = st.selectbox("Pilih ID Data yang Ingin Di-edit:", df["ID"].tolist(), format_func=lambda value: f"ID #{value} — {df.loc[df['ID'] == value, 'Tanggal'].iloc[0]} — {df.loc[df['ID'] == value, 'Nama Promotor'].iloc[0]}")
    row = df[df["ID"] == selected_id].iloc[0]
    st.markdown("##### Data sebelumnya")
    st.dataframe(row.to_frame().T, use_container_width=True, hide_index=True)
    st.markdown("##### Form Edit Laporan")
    with st.form("form_edit_kanvas"):
        c1, c2 = st.columns(2)
        with c1:
            raw_date = pd.to_datetime(row["Tanggal"], errors="coerce")
            edit_date = st.date_input("Date", value=raw_date.date() if pd.notna(raw_date) else datetime.now(TZ_WIB).date())
            promoters = list(PROMOTOR_ZONA)
            edit_promoter = st.selectbox("Nama Promotor", promoters, index=promoters.index(row["Nama Promotor"]) if row["Nama Promotor"] in promoters else 0)
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
    st.download_button(f"💾 Download Excel ({scope})", output.getvalue(), file_name=f"laporan_kanvas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
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


def backup_restore_page(df):
    st.title("☁️ Backup & Restore Google Sheets")
    if "backup_authenticated" not in st.session_state:
        st.session_state["backup_authenticated"] = False
    if not st.session_state["backup_authenticated"]:
        with st.form("backup_login"):
            password = st.text_input("Password Admin:", type="password")
            login = st.form_submit_button("🔓 Buka Menu Backup & Restore", type="primary")
        if login:
            if password == ADMIN_PASSWORD:
                st.session_state["backup_authenticated"] = True
                st.rerun()
            st.error("❌ Password salah!")
        return

    if st.button("🔒 Kunci Menu Backup & Restore"):
        st.session_state["backup_authenticated"] = False
        st.rerun()

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
    st.write("Gunakan tombol di bawah ini untuk mengirim ulang seluruh data Laporan Kanvas lokal ke sheet **`DataKanvasAksara`**.")
    if st.button("🔄 Kirim/Backup Semua Data Kanvas ke Google Sheets", type="secondary"):
        if df.empty:
            st.info("📭 Belum ada data di database lokal untuk di-backup.")
            return
        progress = st.progress(0)
        succeeded = 0
        for index, row in df.iterrows():
            payload = {
                "id": int(row["ID"]),
                "tanggal": str(row["Tanggal"]),
                "nama_promotor": str(row["Nama Promotor"]),
                "zona": str(row["Zona"]),
                "brand": str(row["Brand"]),
            }
            for key, label in FIELD_LABELS.items():
                payload[key] = int(row[label] or 0)
            payload["waktu_submit"] = str(row["Waktu Submit"])
            try:
                response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
                if response.status_code == 200:
                    succeeded += 1
            except requests.RequestException:
                pass
            progress.progress((index + 1) / len(df))
        st.success(f"✅ Berhasil mem-backup {succeeded} dari {len(df)} data ke sheet DataKanvasAksara!")


init_db()

# Auto-restore setiap kali aplikasi dibuka atau halaman di-refresh
if "initial_restore_done" not in st.session_state:
    with st.spinner("Menyinkronkan data terbaru dari Google Sheets..."):
        ok, msg = restore_from_google_sheets()
    st.session_state["initial_restore_done"] = True
    st.session_state["initial_restore_status"] = (ok, msg)
    if ok:
        st.session_state["last_restore_time"] = datetime.now(TZ_WIB).strftime("%Y-%m-%d %H:%M:%S")

now = datetime.now(TZ_WIB)
today = now.strftime("%Y-%m-%d")

if "notifikasi_sukses" in st.session_state:
    st.balloons()
    st.success(st.session_state.pop("notifikasi_sukses"))
if "notifikasi_error" in st.session_state:
    st.error(st.session_state.pop("notifikasi_error"))

# Status sinkronisasi otomatis di sidebar
restore_ok, restore_msg = st.session_state.get("initial_restore_status", (False, ""))
if restore_ok:
    st.sidebar.caption(f"🟢 Sync Google Sheets: {st.session_state.get('last_restore_time', '-')}")
elif restore_msg:
    st.sidebar.warning(f"⚠️ Auto-restore gagal: {restore_msg}")

if st.session_state.get("active_page", "Laporan Kanvas") == "Survey Konsumen":
    st.sidebar.title("🗣️ Survey Konsumen")
    survey_menu = st.sidebar.radio(
        "Menu Survey",
        ["Entry Survey", "Log Entry Survey", "Monitoring Survey"],
        key="survey_navigation",
    )
    st.sidebar.markdown("---")
    if st.sidebar.button("← Kembali ke Laporan Kanvas", key="back_to_kanvas"):
        st.session_state["active_page"] = "Laporan Kanvas"
        st.rerun()
    menu = "Survey Konsumen"
else:
    st.sidebar.title("📋 Laporan Kanvas")
    menu = st.sidebar.radio("Navigasi", [
        "Form Entry Laporan Kanvas",
        "Manajemen Data (Edit, Unduh, & Hapus)",
        "Rekapitulasi Harian & Mingguan (Report Table)",
        "Panel Admin & Log Laporan Kanvas (Semua Data)",
        "Backup & Restore Google Sheets",
    ])
    st.sidebar.markdown("---")
    if st.sidebar.button("🗣️ Survey Konsumen", key="open_consumer_survey"):
        st.session_state["active_page"] = "Survey Konsumen"
        st.rerun()

if menu == "Form Entry Laporan Kanvas":
    st.markdown("<h2 style='text-align: center;'>📋 Form Entry Laporan Kanvas</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748b;'>Sistem Perekaman Data Kanvas Lapangan</p>", unsafe_allow_html=True)

if menu == "Form Entry Laporan Kanvas":
    report_form()
    st.markdown("---")
    daily_status(load_data(), today)
elif menu == "Survey Konsumen":
    if survey_menu == "Entry Survey":
        consumer_survey_entry_page()
    elif survey_menu == "Log Entry Survey":
        survey_log_page()
    elif survey_menu == "Monitoring Survey":
        survey_monitoring_page()
elif menu == "Manajemen Data (Edit, Unduh, & Hapus)":
    management_page(load_data(), today)
elif menu == "Rekapitulasi Harian & Mingguan (Report Table)":
    recap_page(load_data())
elif menu == "Panel Admin & Log Laporan Kanvas (Semua Data)":
    log_page(load_data())
elif menu == "Backup & Restore Google Sheets":
    backup_restore_page(load_data())
