
# NEXORA AI COMPANY — Starter v1

Dashboard multi-agent untuk menjalankan workflow DEMO lokal. Bahasa UI Indonesia.

## Yang tersedia
- Command Center: kirim instruksi ke AI CEO.
- 12 departemen spesialis + AI CEO.
- Orkestrasi lokal berbasis template DEMO.
- Database SQLite untuk tugas, hasil agent, dan activity log.
- Workflow webhook n8n DEMO (belum memanggil backend).
- Dockerfile untuk deployment container.

## Batas penting
Versi ini **bukan sistem AI otonom produksi**. Mode DEMO tidak memanggil LLM, tidak browsing, tidak mengirim WhatsApp/email, tidak memposting ke media sosial, tidak melakukan transaksi, dan tidak mengakses akun eksternal. Hasil agent adalah template untuk menguji dashboard dan alur kerja.
Tindakan eksternal yang berdampak harus memiliki integrasi resmi, autentikasi aman, batas penggunaan, dan persetujuan. Jangan menaruh API key di kode atau repository publik.

## Instalasi Windows
1. Instal Python 3.11+ dari python.org dan centang Add Python to PATH.
2. Ekstrak ZIP.
3. Buka CMD di folder `NEXORA_AI_COMPANY`.
4. Jalankan:
   ```bash
   python -m venv .venv
   .venv\\Scripts\\activate
   pip install -r requirements.txt
   streamlit run app.py
   ```
5. Buka URL lokal yang ditampilkan terminal.

## Instalasi Termux Android
1. Pasang Termux dari F-Droid atau GitHub resmi.
2. Jalankan:
   ```bash
   pkg update && pkg upgrade -y
   pkg install python unzip -y
   ```
3. Ekstrak ZIP ke folder home, lalu masuk ke folder proyek.
4. Jalankan:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   streamlit run app.py --server.address 127.0.0.1
   ```
5. Buka `http://127.0.0.1:8501` di browser Android.
Catatan: Android dapat menghentikan proses latar belakang; bukan pilihan ideal untuk uptime 24/7.

## Cloud gratis
Pilihan awal: deploy repository GitHub ke Streamlit Community Cloud. Ikuti panduan resmi Streamlit Community Cloud. Set main file path ke `app.py` dan Python sesuai dukungan platform.
**Penting:** penyimpanan SQLite pada filesystem cloud gratis dapat bersifat sementara/ter-reset. Untuk data persisten, tambahkan database managed seperti Supabase setelah mengatur kredensial sebagai Secrets. Starter ini belum mengimplementasikan konektor Supabase.
Gratis tidak menjamin uptime, kuota AI, domain khusus, atau penyimpanan persisten.

## Menjalankan dengan Docker
```bash
docker build -t nexora-ai-company .
docker run --rm -p 8501:8501 -v nexora_data:/app/data nexora-ai-company
```

## Database
SQLite dibuat otomatis pada `data/nexora.db` dengan tabel:
- tasks
- agent_runs
- activity_logs

## n8n
Impor `workflows/nexora_webhook_demo.json` ke n8n. Workflow hanya menerima webhook dan mengembalikan respons DEMO; belum terhubung ke aplikasi.

## Konfigurasi
Salin `.env.example` menjadi `.env` jika ingin mengubah `DATABASE_PATH`. Streamlit tidak otomatis memuat `.env` tanpa python-dotenv; untuk konfigurasi sederhana gunakan environment variable platform atau sesuaikan deployment.

## Roadmap
1. Tambah autentikasi dashboard.
2. Ganti template agent dengan LLM provider yang dipilih.
3. Tambah pencarian web dengan sumber dan sitasi.
4. Tambah antrean background dan retry.
5. Tambah database cloud persisten.
6. Integrasi kanal eksternal satu per satu dengan approval dan audit log.
