# EntryKanvas

Aplikasi Streamlit untuk pencatatan laporan kanvas promotor, survey konsumen, status entry harian, ekspor Excel, dan rekap mingguan. Survey konsumen menyediakan log Excel dan monitoring komentar positif/negatif per aspek; laporan kanvas dapat dikoreksi atau dihapus satu per satu melalui menu Manajemen Data.

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

Untuk backup Survey Konsumen dan penghapusan yang ikut tersinkron, salin `GoogleAppsScript.gs` ke project Apps Script yang terhubung ke spreadsheet, lalu deploy versi web app terbaru pada URL webhook yang sama. Script mempertahankan tab `DataKanvas` dan menyimpan survey secara idempotent berdasarkan ID di tab `SurveyKonsumen`.

## Catatan data

Status publik hanya menampilkan jumlah laporan hari ini, bukan daftar nama promotor yang sudah/belum entry. Jangan gunakan SQLite pada filesystem ephemeral sebagai satu-satunya salinan data penting.
