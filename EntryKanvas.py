from datetime import datetime
from io import BytesIO
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
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycby_YGCckSCAKhEOxlOMvhD0_dNUn4OM-lOyYLRzbE7aUzhnK5v9BU6ywVf6n1v-U7Y/exec"
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

st.set_page_config(
    page_title="Form Entry Laporan Kanvas", page_icon="📋", layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown("""
<style>
.stApp { background-color: #f8fafc; }
h1, h2, h3 { color: #0f172a; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
.stButton>button { border-radius: 8px; font-weight: 600; width: 100%; }
div[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; border: 1px solid #e2e8f0; }
</style>
""", unsafe_allow_html=True)


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
        columns = {row[1] for row in conn.execute("PRAGMA table_info(kanvas)")}
        if "pic" in columns and "nama_promotor" not in columns:
            conn.execute("ALTER TABLE kanvas RENAME COLUMN pic TO nama_promotor")
            columns.remove("pic")
            columns.add("nama_promotor")
        additions = {
            "nama_promotor": "TEXT", "zona": "TEXT",
            **{name: "INTEGER DEFAULT 0" for name in FIELD_LABELS if name not in ("canvas_plan", "omset_bungkus")},
        }
        for name, kind in additions.items():
            if name not in columns:
                conn.execute(f"ALTER TABLE kanvas ADD COLUMN {name} {kind}")


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


def save_report(data):
    columns = ["tanggal", "nama_promotor", "zona", "brand", *FIELD_LABELS, "waktu_submit"]
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute(
            f"INSERT INTO kanvas ({', '.join(columns)}) VALUES ({', '.join('?' for _ in columns)})",
            [data[key] for key in columns],
        )
    try:
        requests.post(WEBHOOK_URL, json=data, timeout=10).raise_for_status()
    except requests.RequestException:
        pass


def report_form():
    st.subheader("📝 Masukkan Data Laporan Baru")
    with st.form("form_laporan_kanvas"):
        c1, c2 = st.columns(2)
        with c1:
            tanggal = st.date_input("Date", value=datetime.now(TZ_WIB).date())
            promotor = st.selectbox("Nama Promotor", list(PROMOTOR_ZONA))
            brand = st.selectbox("Brand", ["Djarum 76 Aksara"])
        with c2:
            st.text_input("Zona (Otomatis)", value=PROMOTOR_ZONA[promotor], disabled=True)
            canvas_plan = st.number_input("Canvas Plan", min_value=0, step=1, value=0)
            omset = st.number_input("Omset (bungkus)", min_value=0, step=1, value=0)
        st.markdown("#### 📊 Rincian Outlet")
        keys = [key for key in FIELD_LABELS if key not in ("canvas_plan", "omset_bungkus")]
        vals = {}
        cols = st.columns(3)
        for i, key in enumerate(keys):
            with cols[i % 3]:
                vals[key] = st.number_input(FIELD_LABELS[key], min_value=0, step=1, value=0, key=f"new_{key}")
        b1, b2 = st.columns(2)
        with b1:
            preview = st.form_submit_button("👁️ Lihat Preview", type="secondary")
        with b2:
            submit = st.form_submit_button("🚀 Langsung Kirim", type="primary")
    if preview or submit:
        report = {
            "tanggal": tanggal.strftime("%Y-%m-%d"), "nama_promotor": promotor,
            "zona": PROMOTOR_ZONA[promotor], "brand": brand,
            "canvas_plan": int(canvas_plan), "omset_bungkus": int(omset),
            **{key: int(value) for key, value in vals.items()},
            "waktu_submit": datetime.now(TZ_WIB).strftime("%Y-%m-%d %H:%M:%S"),
        }
        if preview:
            st.session_state["form_preview_data"] = report
        else:
            save_report(report)
            st.session_state["notifikasi_sukses"] = "🎉 Data laporan kanvas berhasil dikirim ke database!"
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
                st.session_state["notifikasi_sukses"] = "🎉 Data laporan kanvas berhasil disimpan ke database!"
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
            st.dataframe(pd.DataFrame([{"Nama Promotor": p, "Zona": PROMOTOR_ZONA.get(p, "-")} for p in entered]), use_container_width=True, hide_index=True)
        else:
            st.info("📭 Belum ada promotor yang melakukan entry laporan pada hari ini.")
    with no:
        missing = [{"Nama Promotor": p, "Zona": z} for p, z in PROMOTOR_ZONA.items() if p not in entered]
        if missing:
            st.warning(f"⚠️ Terdapat **{len(missing)}** promotor yang belum melakukan entry laporan hari ini.")
            st.dataframe(pd.DataFrame(missing), use_container_width=True, hide_index=True)
        else:
            st.success("🎉 Seluruh promotor telah melakukan entry laporan hari ini.")


def require_admin():
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False
    if st.session_state.admin_authenticated:
        return True
    st.info("⚠️ Area Admin dilindungi password. Silakan masukkan password untuk membuka.")
    with st.form("form_password_admin"):
        password = st.text_input("Password Admin:", type="password")
        login = st.form_submit_button("🔓 Buka Area Admin", type="primary")
    if login:
        if password == ADMIN_PASSWORD:
            st.session_state.admin_authenticated = True
            st.rerun()
        st.error("❌ Password salah!")
    return False


def admin_header():
    c1, c2 = st.columns([3, 1])
    c1.info("🔓 Area Admin & Rekap Terbuka")
    if c2.button("🔒 Kunci Kembali"):
        st.session_state.admin_authenticated = False
        st.rerun()


def recap_page(df):
    st.title("📈 Rekapitulasi Harian & Mingguan (Report Table)")
    if df.empty:
        st.info("📭 Belum ada data untuk direkap.")
        return
    work = df.copy()
    work["Tanggal_DT"] = pd.to_datetime(work["Tanggal"], errors="coerce")
    zones = ["All Zona"] + sorted(set(PROMOTOR_ZONA.values()))
    c1, c2, c3 = st.columns(3)
    zone = c1.selectbox("Pilih Zona", zones, key="rekap_zona")
    if zone != "All Zona":
        work = work[work["Zona"] == zone]
    years = sorted(work["Tanggal_DT"].dropna().dt.year.unique(), reverse=True)
    if not years:
        st.info("�� Belum ada tanggal laporan yang valid.")
        return
    year = c2.selectbox("Pilih Tahun", years, key="rekap_thn")
    year_data = work[work["Tanggal_DT"].dt.year == year]
    weeks = sorted(year_data["Tanggal_DT"].dt.isocalendar().week.dropna().unique(), reverse=True)
    if not weeks:
        st.info("📭 Tidak ada data pada tahun yang dipilih.")
        return
    week = c3.selectbox("Pilih Minggu ke- (Week)", weeks, key="rekap_mg")
    week_data = year_data[year_data["Tanggal_DT"].dt.isocalendar().week == week].copy()
    weekdays = {0: "Senin", 1: "Selasa", 2: "Rabu", 3: "Kamis", 4: "Jumat"}
    week_data["Nama Hari"] = week_data["Tanggal_DT"].dt.weekday.map(weekdays)
    rows = {}
    for day in weekdays.values():
        day_df = week_data[week_data["Nama Hari"] == day]
        if day_df.empty:
            rows[day] = {"Tanggal": "-", "Total Armada": 0, "Call": 0, "Beli Ada": 0,
                "Beli Ks Tambah": 0, "Beli Ks Baru": 0, "TBA Aktif": 0, "TBA Pasif": 0,
                "Kosong": 0, "Total Omset": 0, "Average Dropsize": 0.0,
                "% Availability Sebelum": "0.0%", "% Availability Sesudah": "0.0%",
                "EC": 0, "% EC": "0.0%", "% Repeat": "0.0%", "% OOS": "0.0%",
                "% Outlet Ecer": "0.0%", "Total Sampling": 0, "Kontak Konsumen": 0,
                "Laku Direct Selling": 0}
            continue
        val = lambda col: day_df[col].fillna(0).sum()
        beli, ks_tb, ks_b = val("Outlet Beli Ada"), val("Outlet Ks Tb"), val("Outlet Ks B")
        tba_a, tba_p, kosong = val("Outlet TB Ada A"), val("Outlet TB Ada P"), val("Outlet TB Ks")
        call = beli + ks_tb + ks_b + tba_a + tba_p + kosong
        total_beli = beli + ks_tb + ks_b
        avail_before = (beli + tba_a + tba_p) / call * 100 if call else 0
        avail_after = (beli + ks_tb + ks_b + tba_a + tba_p) / call * 100 if call else 0
        rows[day] = {
            "Tanggal": day_df["Tanggal"].iloc[0] and datetime.strptime(day_df["Tanggal"].iloc[0], "%Y-%m-%d").strftime("%d/%m/%Y"),
            "Total Armada": day_df["Nama Promotor"].nunique(), "Call": call,
            "Beli Ada": beli, "Beli Ks Tambah": ks_tb, "Beli Ks Baru": ks_b,
            "TBA Aktif": tba_a, "TBA Pasif": tba_p, "Kosong": kosong,
            "Total Omset": val("Omset (Bungkus)"),
            "Average Dropsize": round(val("Omset (Bungkus)") / total_beli, 1) if total_beli else 0.0,
            "% Availability Sebelum": f"{round(avail_before, 1)}%",
            "% Availability Sesudah": f"{round(avail_after, 1)}%", "EC": total_beli,
            "% EC": f"{round(total_beli / call * 100, 1) if call else 0.0}%",
            "% Repeat": f"{round((beli + ks_tb) / (beli + ks_tb + tba_a + tba_p) * 100, 1) if beli + ks_tb + tba_a + tba_p else 0.0}%",
            "% OOS": f"{round(ks_tb / call * 100, 1) if call else 0.0}%",
            "% Outlet Ecer": f"{round(val('Outlet Buka Ecer') / call * 100, 1) if call else 0.0}%",
            "Total Sampling": val("Jumlah Rokok Sampling"),
            "Kontak Konsumen": val("Jumlah Konsumen Trial"),
            "Laku Direct Selling": val("Direct Selling"),
        }
    result = pd.DataFrame(rows)
    title_zone = f"Zona {zone}" if zone != "All Zona" else "All Zona"
    title = f"Laporan Rekapitulasi {title_zone} - Minggu ke {week} - {year}"
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
    pimg = PILImage.open(png).convert("RGB")
    jpg = BytesIO()
    pimg.save(jpg, format="JPEG", quality=95)
    d1, d2 = st.columns(2)
    d1.download_button("📷 Download PNG", png.getvalue(), file_name=f"rekap_kanvas_{zone.replace(' ', '_')}_minggu{week}_{year}.png", mime="image/png", key="dl_rekap_png")
    d2.download_button("🖼️ Download JPEG", jpg.getvalue(), file_name=f"rekap_kanvas_{zone.replace(' ', '_')}_minggu{week}_{year}.jpg", mime="image/jpeg", key="dl_rekap_jpeg")


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
    st.markdown("#### ✏️ Edit Entry Data (Koreksi Kesalahan Input)")
    selected_id = st.selectbox("Pilih ID Data yang Ingin Di-edit:", df["ID"].tolist())
    row = df[df["ID"] == selected_id].iloc[0]
    with st.form("form_edit_kanvas"):
        st.markdown(f"#### Edit Data ID #{selected_id}")
        c1, c2 = st.columns(2)
        with c1:
            edit_date = st.date_input("Tanggal", value=pd.to_datetime(row["Tanggal"]).date())
            promoters = list(PROMOTOR_ZONA)
            edit_promoter = st.selectbox("Nama Promotor", promoters, index=promoters.index(row["Nama Promotor"]) if row["Nama Promotor"] in promoters else 0)
            brands = ["Djarum 76 Aksara"]
            edit_brand = st.selectbox("Brand", brands, index=brands.index(row["Brand"]) if row["Brand"] in brands else 0)
        with c2:
            st.text_input("Zona (Otomatis)", value=PROMOTOR_ZONA.get(edit_promoter, "-"), disabled=True)
            edit_values = {}
            for key, label in FIELD_LABELS.items():
                edit_values[key] = st.number_input(label, min_value=0, step=1, value=int(row[label] or 0), key=f"edit_{selected_id}_{key}")
        update = st.form_submit_button("💾 Perbarui Data", type="primary")
    if update:
        columns = ["tanggal", "nama_promotor", "zona", "brand", *FIELD_LABELS]
        values = [edit_date.strftime("%Y-%m-%d"), edit_promoter, PROMOTOR_ZONA[edit_promoter], edit_brand, *[int(edit_values[k]) for k in FIELD_LABELS], int(selected_id)]
        with sqlite3.connect(DB_NAME) as conn:
            conn.execute(f"UPDATE kanvas SET {', '.join(f'{col} = ?' for col in columns)} WHERE id = ?", values)
        st.session_state["notifikasi_sukses"] = f"✏️ Data ID #{selected_id} berhasil diperbarui!"
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


def backup_page(df):
    st.title("☁️ Backup Data ke Google Sheets")
    st.write("Gunakan tombol di bawah ini untuk sinkronisasi atau backup ulang seluruh data lokal ke Google Sheets.")
    if st.button("🔄 Kirim/Backup Semua Data ke Google Sheets", type="primary"):
        if df.empty:
            st.info("📭 Belum ada data di database lokal untuk di-backup.")
            return
        progress = st.progress(0)
        succeeded = 0
        for index, row in df.iterrows():
            payload = {
                "id": int(row["ID"]), "tanggal": str(row["Tanggal"]),
                "nama_promotor": str(row["Nama Promotor"]), "zona": str(row["Zona"]),
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
        st.success(f"✅ Berhasil mem-backup {succeeded} dari {len(df)} data ke Google Sheets!")


init_db()
now = datetime.now(TZ_WIB)
today = now.strftime("%Y-%m-%d")
if "notifikasi_sukses" in st.session_state:
    st.balloons()
    st.success(st.session_state.pop("notifikasi_sukses"))

st.sidebar.title("📋 Laporan Kanvas")
menu = st.sidebar.radio("Navigasi", [
    "Form Entry & Status", "Rekapitulasi Harian & Mingguan",
    "Panel Admin & Log Laporan", "Manajemen Data",
    "Backup Data ke Google Sheets",
])
st.markdown("<h2 style='text-align: center;'>📋 Form Entry Laporan Kanvas</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #64748b;'>Sistem Perekaman Data Kanvas Lapangan</p>", unsafe_allow_html=True)

if menu == "Form Entry & Status":
    report_form()
    st.markdown("---")
    daily_status(load_data(), today)
elif menu == "Rekapitulasi Harian & Mingguan":
    if require_admin():
        admin_header()
        recap_page(load_data())
elif menu == "Panel Admin & Log Laporan":
    if require_admin():
        admin_header()
        log_page(load_data())
elif menu == "Manajemen Data":
    if require_admin():
        admin_header()
        management_page(load_data(), today)
elif menu == "Backup Data ke Google Sheets":
    if require_admin():
        admin_header()
        backup_page(load_data())
