# EntryKanvas

Aplikasi Streamlit untuk pencatatan laporan kanvas promotor, status entry harian, ekspor Excel, dan rekap mingguan.

## Menjalankan aplikasi

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
source .venv/bin/activate
pip install -r requirements.txt
streamlit run EntryKanvas.py
```

Database SQLite disimpan di `laporan_kanvas.db` secara default. Pada hosting, atur `KANVAS_DB_PATH` ke lokasi penyimpanan persisten yang dapat ditulis; disk sementara dapat menghilangkan data saat aplikasi dimulai ulang. Untuk penggunaan serentak/produksi, gunakan database terkelola dan backup terjadwal.

## Konfigurasi rahasia

Jangan simpan password atau URL webhook privat di kode maupun commit. Di Streamlit, masukkan konfigurasi melalui **App settings → Secrets** (atau `.streamlit/secrets.toml` lokal yang tidak di-commit):

```toml
ADMIN_PASSWORD = "gunakan-password-kuat-dan-unik"
WEBHOOK_URL = "https://alamat-web-app-google-apps-script/exec"
```

Tanpa `ADMIN_PASSWORD`, area admin tetap terkunci. Tanpa `WEBHOOK_URL`, penyimpanan lokal tetap berfungsi, tetapi backup Google Sheets tidak dikirim. Lindungi endpoint Apps Script dengan kontrol akses yang sesuai, gunakan HTTPS, dan uji pemulihan backup secara berkala.

## Catatan data

Status publik hanya menampilkan jumlah laporan hari ini, bukan daftar nama promotor yang sudah/belum entry. Jangan gunakan SQLite pada filesystem ephemeral sebagai satu-satunya salinan data penting.
