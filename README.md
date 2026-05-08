# 🔍 Smart Insect Identifier & AI Insights

Aplikasi ini adalah sistem identifikasi serangga berbasis AI yang menggabungkan kekuatan **Computer Vision** (PyTorch) untuk klasifikasi spesies dan **Generative AI** (Google Gemini 3 Flash) untuk memberikan wawasan mendalam seperti taksonomi, habitat, dan fakta unik secara real-time.

## ✨ Fitur Utama

*   **Identifikasi Akurat**: Menggunakan model Deep Learning yang dioptimalkan untuk klasifikasi spesies serangga.
*   **AI Thinking & Grounding**: Terintegrasi dengan Gemini 2.5 Flash Lite untuk mendapatkan informasi medis/biologis yang akurat.
*   **UI Modern & Minimalis**: Antarmuka berbasis web yang elegan dengan *glassmorphism* dan dukungan penuh *Markdown rendering*.
*   **Robust Backend**: Dibangun dengan FastAPI yang mendukung *asynchronous processing* dan sistem *error handling* (Graceful Degradation).
*   **Cross-Platform Ready**: Model dapat dijalankan di lingkungan CPU maupun GPU.

## 🛠️ Tech Stack

### Backend
*   **Framework**: FastAPI (Python)
*   **ML Engine**: PyTorch (TorchScript)
*   **LLM SDK**: Google GenAI SDK (`google-genai`)
*   **Image Processing**: Pillow

### Frontend
*   **Framework**: Next.js 14+ (TypeScript)
*   **Styling**: Tailwind CSS & Tailwind Typography
*   **Markdown**: React Markdown

## 🚀 Persiapan & Instalasi

### 1. Prasyarat
*   Python 3.10+
*   Node.js 18+
*   Google AI Studio API Key ([Dapatkan di sini](https://aistudio.google.com/))

### 2. Setup Backend
1. Masuk ke direktori backend:
   ```bash
   cd backend
   ```

2. Buat virtual environment dan aktifkan:
   ```bash
   python -m venv env
   # Windows: env\Scripts\activate | Mac/Linux: source env/bin/activate
   ```


3. Instal dependensi:
   ```bash
   pip install -r requirements.txt
   ```


4. Buat file `.env` di dalam folder `backend/` dan masukkan API Key Anda:
   ```env
   GEMINI_API_KEY=YOUR_API_KEY_HERE
   ```


5. Pastikan model berada di folder `artifacts/`.


### 3. Setup Frontend

1. Masuk ke direktori frontend:
   ```bash
   cd frontend
  
   ```

2. Instal dependensi:
   ```bash
   npm install
   ```

## 🏃 Menjalankan Aplikasi

1. **Jalankan Backend**:
```bash
# Di dalam folder backend
uvicorn main:app --reload

```

API akan berjalan di `http://127.0.0.1:8000`


2. **Jalankan Frontend**:
```bash
# Di dalam folder frontend
npm run dev
```

Buka `http://localhost:3000` di browser Anda.


## 📁 Struktur Proyek

```text
insect-analyzer/
├── backend/
│   ├── artifacts/           # Model
│   ├── main.py              # Entry point FastAPI
│   ├── ml_service.py        # Logika Inference PyTorch
│   ├── gemini_service.py    # Integrasi SDK Gemini
│   └── .env                 # API Keys (Secret)
└── frontend/
    ├── app/                 # Next.js App Router
    ├── components/          # Reusable UI Components
    ├── tailwind.config.ts   # Konfigurasi Styling
    └── package.json
```
