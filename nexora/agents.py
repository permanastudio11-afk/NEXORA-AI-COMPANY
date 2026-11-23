
AGENTS = [
    ("ceo", "AI CEO", "Koordinasi strategi dan pembagian pekerjaan"),
    ("research", "Research Agent", "Riset dan pengumpulan informasi"),
    ("content", "Content Agent", "Ide, kalender, dan naskah konten"),
    ("marketing", "Marketing Agent", "Strategi pemasaran dan kampanye"),
    ("sales", "Sales Agent", "Alur prospek dan strategi penjualan"),
    ("finance", "Finance Agent", "Anggaran dan laporan keuangan"),
    ("hr", "HR Agent", "Peran, kompetensi, dan kebutuhan tim"),
    ("project", "Project Manager", "Rencana, prioritas, dan tenggat"),
    ("admin", "Admin Agent", "Dokumentasi dan laporan operasional"),
    ("business", "Business Analyst", "Analisis model bisnis dan KPI"),
    ("design", "UI/UX Agent", "Brief desain dan pengalaman pengguna"),
    ("developer", "Developer Agent", "Spesifikasi teknis dan backlog"),
    ("video", "Video Agent", "Konsep video dan storyboard"),
]

def run_agent(agent_key: str, task: str) -> str:
    """Deterministic demo output. No external actions or AI API calls."""
    name = dict((k, n) for k, n, _ in AGENTS).get(agent_key, agent_key)
    clean = " ".join(task.split())
    templates = {
        "ceo": f"Tujuan diterima: {clean}\nPrioritas: definisikan hasil, pecah pekerjaan, tinjau risiko, lalu rangkum keputusan.",
        "research": f"Rencana riset untuk: {clean}\n1) Tentukan pertanyaan. 2) Kumpulkan sumber tepercaya. 3) Catat tanggal dan bukti. 4) Tandai hal yang belum terverifikasi.",
        "content": f"Brief konten: {clean}\nFormat: hook pembuka, 3 poin utama, contoh, CTA. Periksa fakta dan hak penggunaan materi sebelum publikasi.",
        "marketing": f"Rencana pemasaran: {clean}\nSegmentasi audiens, proposisi nilai, kanal, pesan, eksperimen kecil, dan metrik konversi.",
        "sales": f"Rencana sales: {clean}\nPetakan prospek, kebutuhan, kualifikasi, tindak lanjut, dan indikator pipeline. Jangan mengirim pesan otomatis tanpa izin.",
        "finance": f"Catatan finance: {clean}\nBuat asumsi biaya, proyeksi pendapatan, arus kas, dan skenario konservatif. Angka belum diverifikasi sampai data dimasukkan.",
        "hr": f"Rencana HR: {clean}\nIdentifikasi peran, tanggung jawab, kompetensi, kapasitas, dan kebutuhan pelatihan.",
        "project": f"Rencana proyek: {clean}\nTahap: definisi → persiapan → pelaksanaan → QA → evaluasi. Tetapkan pemilik dan tenggat setiap tugas.",
        "admin": f"Dokumentasi: {clean}\nCatat keputusan, pemilik tugas, status, tanggal, dan tindak lanjut.",
        "business": f"Analisis bisnis: {clean}\nPeriksa pelanggan, masalah, solusi, model pendapatan, biaya, pesaing, risiko, dan KPI.",
        "design": f"Brief UI/UX: {clean}\nTentukan pengguna, alur utama, struktur layar, komponen, aksesibilitas, dan kriteria penerimaan.",
        "developer": f"Backlog teknis: {clean}\nBuat user story, acceptance criteria, dependensi, pengujian, dan rencana rilis. Jangan deploy tanpa persetujuan.",
        "video": f"Konsep video: {clean}\nSusun hook 0–3 detik, adegan, narasi, teks layar, CTA, rasio, dan daftar aset berlisensi.",
    }
    return templates.get(agent_key, f"{name} menerima tugas: {clean}")
