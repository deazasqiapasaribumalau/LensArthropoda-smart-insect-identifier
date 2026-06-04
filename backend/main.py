# from fastapi import FastAPI, UploadFile, File, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from ml_service import InsectClassifier
# from gemini_service import GeminiExpert
# import os
# from dotenv import load_dotenv

# # Memuat environment variable dari file .env
# load_dotenv()

# # Inisialisasi aplikasi FastAPI
# app = FastAPI(title="")

# # Konfigurasi CORS agar frontend dapat mengakses API
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"], 
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Inisialisasi kebutuhan model klasifikasi
# classifier = InsectClassifier(
#     model_path=""
# )

# # Inisialisasi layanan Gemini AI
# gemini_expert = # dapatkan API Key

# @app.post("/analyze")
# async def analyze_image(file: UploadFile = File(...)):

#     # Validasi apakah file yang diunggah berupa gambar
#     if not file.content_type.startswith("image/"):
#         raise HTTPException(status_code=400, detail="File harus berupa gambar")
    
#     try:
        
#         # Membaca file gambar
#         image_bytes = 

#         # Prediksi jenis serangga menggunakan model ML
#         predictions = 
        
#         # Mengambil hasil prediksi terbaik
#         top_prediction = 
        
#         # Mengambil informasi detail dari Gemini AI
#         try:
#             ai_insight = gemini_expert.get_insect_info(top_prediction)
#         except Exception as gemini_error:
#             print(f"Peringatan Gemini API: {gemini_error}")
#             # Contoh template pesan ketika Gemini gagal memberikan response
#             ai_insight = (
#                 f"Sistem lokal kami berhasil mengidentifikasi serangga ini sebagai {top_prediction}. "
#                 "Namun, layanan AI Explorer (Gemini) saat ini sedang mengalami lonjakan permintaan (High Demand) dari server pusat Google.\n\n"
#                 "Silakan klik tombol analisis lagi dalam beberapa saat untuk memuat fakta unik dan detail famili serangga ini."
#             )
        
#         # Mengembalikan hasil prediksi dan insight AI
#         return {
#             "predictions": predictions,
#             "top_prediction": top_prediction,
#             "ai_insight": ai_insight
#         }
        
#     # Menangani error umum pada server
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

"""
main.py
Entry point FastAPI backend untuk Smart Insect Identifier.
- POST /predict  : Upload gambar → prediksi + AI insights
- GET  /health   : Health check
- GET  /classes  : Daftar kelas serangga
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from gemini_service import GeminiService
from ml_service import InsectClassifier

# ─────────────────────────────────────────────
# Logging setup
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Load .env
# ─────────────────────────────────────────────
load_dotenv()

# ─────────────────────────────────────────────
# Global service instances
# ─────────────────────────────────────────────
ml_service: Optional[InsectClassifier] = None
gemini_service: Optional[GeminiService] = None


# ─────────────────────────────────────────────
# Lifespan (startup & shutdown)
# ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inisialisasi services saat startup."""
    global ml_service, gemini_service

    logger.info("Starting up services...")

    # Load ML model
    try:
        ml_service = InsectClassifier(artifacts_dir="artifacts")
        logger.info(f"ML service ready. Classes: {ml_service.num_classes}")
    except FileNotFoundError as e:
        logger.error(f"ML model tidak ditemukan: {e}")
        logger.warning("Pastikan model sudah ada di folder artifacts/")
        # App tetap jalan, endpoint akan return 503 jika model belum ada

    # Init Gemini
    api_key = os.getenv("GEMINI_API_KEY", "")
    gemini_service = GeminiService(api_key=api_key)
    if gemini_service.is_available():
        logger.info("Gemini service ready.")
    else:
        logger.warning("Gemini service tidak tersedia (cek GEMINI_API_KEY di .env).")

    yield

    logger.info("Shutting down...")


# ─────────────────────────────────────────────
# FastAPI app
# ─────────────────────────────────────────────
app = FastAPI(
    title="Smart Insect Identifier API",
    description="REST API untuk identifikasi serangga dengan Computer Vision + Gemini AI Insights",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — izinkan frontend dev server (localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# Pydantic Response Models
# ─────────────────────────────────────────────
class TopKPrediction(BaseModel):
    class_name: str
    confidence: float


class PredictionResponse(BaseModel):
    predicted_class: str
    confidence: float
    top_k: list[TopKPrediction]
    ai_insights: Optional[str] = None
    ai_available: bool = False
    fallback_message: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    ml_model_loaded: bool
    gemini_available: bool
    num_classes: int


class ClassesResponse(BaseModel):
    classes: list[str]
    num_classes: int


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["Utility"])
def health_check():
    """Cek status semua service."""
    return HealthResponse(
        status="ok",
        ml_model_loaded=ml_service is not None,
        gemini_available=gemini_service is not None and gemini_service.is_available(),
        num_classes=ml_service.num_classes if ml_service else 0,
    )


@app.get("/classes", response_model=ClassesResponse, tags=["Utility"])
def get_classes():
    """Kembalikan daftar semua kelas serangga yang didukung model."""
    if ml_service is None:
        raise HTTPException(status_code=503, detail="Model belum dimuat.")
    return ClassesResponse(
        classes=ml_service.class_names,
        num_classes=ml_service.num_classes,
    )


@app.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict(file: UploadFile = File(..., description="Gambar serangga (JPG/PNG)")):
    """
    Upload gambar serangga → dapatkan:
    - Prediksi kelas dari model ML
    - AI Insights dari Google Gemini (taksonomi, habitat, fun facts)

    Fallback: jika Gemini sedang limit/error, tetap kembalikan hasil prediksi ML.
    """
    # ── Validasi ML model ──────────────────────────────────────────────
    if ml_service is None:
        raise HTTPException(
            status_code=503,
            detail="Model ML belum siap. Pastikan file model ada di artifacts/."
        )

    # ── Validasi file type ─────────────────────────────────────────────
    if file.content_type not in ("image/jpeg", "image/png", "image/jpg", "image/webp"):
        raise HTTPException(
            status_code=422,
            detail=f"Tipe file tidak didukung: {file.content_type}. Gunakan JPEG atau PNG."
        )

    # ── Baca bytes ─────────────────────────────────────────────────────
    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=422, detail="File gambar kosong.")

    # ── Inference ML ───────────────────────────────────────────────────
    try:
        ml_result = ml_service.predict(image_bytes, top_k=3)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Gambar tidak valid: {e}")
    except Exception as e:
        logger.error(f"ML inference error: {e}")
        raise HTTPException(status_code=500, detail="Terjadi error saat inference.")

    predicted_class = ml_result["predicted_class"]
    confidence      = ml_result["confidence"]
    top_k_results   = [
        TopKPrediction(class_name=item["class"], confidence=item["confidence"])
        for item in ml_result["top_k"]
    ]

    # ── Gemini AI Insights ─────────────────────────────────────────────
    ai_insights      = None
    ai_available     = False
    fallback_message = None

    if gemini_service and gemini_service.is_available():
        try:
            ai_insights  = await gemini_service.get_insect_info(
                insect_name=predicted_class,
                confidence=confidence,
                use_search=True,
            )
            ai_available = True
            logger.info(f"Gemini insights retrieved for: {predicted_class}")
        except RuntimeError as e:
            err = str(e)
            logger.warning(f"Gemini tidak tersedia: {err}")
            if "503" in err:
                fallback_message = (
                    "Informasi detail AI sedang tidak tersedia saat ini "
                    "(Gemini API sedang sibuk). Silakan coba lagi beberapa saat."
                )
            elif "429" in err:
                fallback_message = (
                    "Informasi detail AI sedang tidak tersedia (rate limit). "
                    "Silakan coba lagi sebentar."
                )
            else:
                fallback_message = f"Gemini tidak dapat memberikan informasi saat ini: {err}"
        except Exception as e:
            logger.error(f"Unexpected Gemini error: {e}")
            fallback_message = "Layanan AI Insights sedang tidak tersedia."
    else:
        fallback_message = "Gemini API tidak dikonfigurasi (GEMINI_API_KEY belum diset)."

    return PredictionResponse(
        predicted_class=predicted_class,
        confidence=confidence,
        top_k=top_k_results,
        ai_insights=ai_insights,
        ai_available=ai_available,
        fallback_message=fallback_message,
    )


# ─────────────────────────────────────────────
# Dev runner (opsional, untuk debug lokal)
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
