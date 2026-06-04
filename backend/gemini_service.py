# import os
# from google import genai
# from google.genai import types

# # Kelas untuk menangani permintaan informasi menggunakan Gemini AI
# class GeminiExpert:
#     def __init__(self, api_key: str):
#         self.client =

#     def get_insect_info(self, insect_name: str) -> str:
#         prompt = f"""
#         Berdasarkan hasil identifikasi gambar, serangga ini adalah "{insect_name}".
#         Tolong berikan informasi detail dengan format yang rapi dan menarik:
#         - Nama Ilmiah:
#         - Nama Umum:
#         - Spesies:
#         - Genus:
#         - Famili:
#         - Habitat:
#         - Fun Fact: (Berikan 1 atau 2 fakta unik yang jarang diketahui)
        
#         Berikan jawaban langsung tanpa basa-basi pengantar.
#         """
        
#         # Menyiapkan konten input untuk model AI
#         contents =
                
#         # Konfigurasi proses generasi AI
#         generate_content_config = 
        
#         # Menghasilkan respons secara streaming
#         untuk chunk in self.klien.models.generate_content_stream(
#             model="gemini-2.5-flash-lite", # Model version yang digunakan
#             contents=,config=,
#         ):
#             # Menggabungkan setiap potongan teks respons
#             if text := cuk.ext:


#         # Mengembalikan hasil akhir respons AI   
#         return 

"""
gemini_service.py
Integrasi Google Gemini 2.5 Flash Lite dengan ThinkingConfig dan opsional GoogleSearch.
Mendukung fallback graceful jika API sedang limit/503.
"""

import logging
import os
from typing import Optional

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Prompt template
# ─────────────────────────────────────────────
INSECT_PROMPT_TEMPLATE = """
Kamu adalah seorang entomologis ahli dan naturalis berpengalaman. 
Model computer vision telah mengidentifikasi serangga dalam gambar sebagai: **{insect_name}** dengan keyakinan {confidence:.1%}.

Berikan informasi mendalam dan menarik tentang serangga ini dalam format berikut (gunakan Markdown):

## 🔬 Identifikasi
**Nama Umum:** [nama populer dalam Bahasa Indonesia]
**Nama Ilmiah:** [nama latin/ilmiah jika diketahui]

## 🌿 Taksonomi
- **Genus:** ...
- **Famili:** ...
- **Ordo:** ...
- **Kelas:** Insecta

## 🏡 Habitat & Persebaran
[Jelaskan di mana serangga ini biasanya ditemukan, termasuk di Indonesia jika relevan]

## 🍽️ Perilaku & Makanan
[Jelaskan pola makan, perilaku unik, dan cara hidup serangga ini]

## ⚠️ Peran Ekologis
[Jelaskan perannya dalam ekosistem: polinator, dekomposer, hama, predator, dll.]

## ✨ Fun Facts
[3-4 fakta menarik dan unik yang jarang diketahui tentang serangga ini]

Gunakan bahasa Indonesia yang mudah dipahami namun tetap informatif dan akurat secara ilmiah.
""".strip()


# ─────────────────────────────────────────────
# Service class
# ─────────────────────────────────────────────
class GeminiService:
    """
    Wrapper untuk Google Gemini 2.5 Flash Lite.
    Menggunakan ThinkingConfig + opsional GoogleSearch grounding.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY tidak diset. Gemini tidak akan berfungsi.")
            self._client = None
        else:
            try:
                self._client = genai.Client(api_key=self.api_key)
                logger.info("Gemini client initialized.")
            except Exception as e:
                logger.error(f"Gagal init Gemini client: {e}")
                self._client = None

        self.model_id = "gemini-2.5-flash-lite"

    # ------------------------------------------------------------------

    def _build_config(self, use_search: bool = False) -> types.GenerateContentConfig:
        """Bangun GenerateContentConfig dengan ThinkingConfig dan opsional GoogleSearch."""
        tools = []
        if use_search:
            tools.append(types.Tool(google_search=types.GoogleSearch()))

        config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                thinking_budget=512,          # token budget untuk thinking
                include_thoughts=False,       # Jangan sertakan inner thoughts di output
            ),
            tools=tools if tools else None,
            temperature=0.7,
            max_output_tokens=2048,
        )
        return config

    # ------------------------------------------------------------------

    async def get_insect_info(
        self,
        insect_name: str,
        confidence: float,
        use_search: bool = True,
    ) -> str:
        """
        Dapatkan informasi mendalam tentang serangga dari Gemini.

        Args:
            insect_name : Nama serangga hasil prediksi model.
            confidence  : Nilai kepercayaan prediksi (0–1).
            use_search  : Aktifkan GoogleSearch grounding (default True).

        Returns:
            String Markdown berisi informasi serangga.

        Raises:
            RuntimeError: Jika Gemini tidak tersedia atau API error.
        """
        if self._client is None:
            raise RuntimeError("Gemini client tidak tersedia (API key tidak diset).")

        prompt = INSECT_PROMPT_TEMPLATE.format(
            insect_name=insect_name,
            confidence=confidence,
        )

        config = self._build_config(use_search=use_search)

        try:
            response = self._client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=config,
            )
            return response.text

        except Exception as e:
            err_str = str(e).lower()
            if "503" in err_str or "unavailable" in err_str or "overloaded" in err_str:
                raise RuntimeError("503: Gemini API sedang sibuk/overloaded.")
            if "429" in err_str or "quota" in err_str or "rate" in err_str:
                raise RuntimeError("429: Gemini API rate limit tercapai.")
            if "400" in err_str or "invalid" in err_str:
                raise RuntimeError(f"400: Permintaan tidak valid ke Gemini: {e}")
            raise RuntimeError(f"Gemini error: {e}")

    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        return self._client is not None

