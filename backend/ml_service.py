# import json
# #import torch
# import io
# from PIL import Image
# import torchvision.transforms as transforms

# # Kelas untuk klasifikasi gambar
# class InsectClassifier:
#     def __init__(self, model_path):



#     def predict(self, image_bytes, top_k=1):

#         return predictions

"""
ml_service.py
Kelas untuk memuat model TorchScript dan melakukan inference gambar serangga.
Konsisten dengan konfigurasi training di notebook.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

import torch
import torch.nn.functional as F
from PIL import Image
import io
import timm
from torchvision import transforms

logger = logging.getLogger(__name__)


class InsectClassifier:
    """
    Service klasifikasi serangga menggunakan model TorchScript.
    Support CPU & GPU. Load sekali, pakai berkali-kali (singleton-friendly).
    """

    def __init__(self, artifacts_dir: str = "artifacts"):
        self.artifacts_dir = Path(artifacts_dir)
        self.model = None
        self.metadata: Dict = {}
        self.transform = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._load()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self):
        """Muat model dan metadata dari folder artifacts."""
        meta_path = self.artifacts_dir / "metadata.json"
        alt_meta_path = self.artifacts_dir / "model_metadata.json"
        if meta_path.exists():
            metadata_file = meta_path
        elif alt_meta_path.exists():
            metadata_file = alt_meta_path
        else:
            raise FileNotFoundError(
                f"metadata.json atau model_metadata.json tidak ditemukan di {self.artifacts_dir}. "
                "Pastikan kamu sudah menyalin model hasil training ke folder artifacts/."
            )

        with open(metadata_file) as f:
            self.metadata = json.load(f)

        img_size: int = self.metadata.get("img_size", 224)
        mean: List = self.metadata.get("imagenet_mean", [0.485, 0.456, 0.406])
        std: List  = self.metadata.get("imagenet_std",  [0.229, 0.224, 0.225])

        # Transform — sama persis dengan val_test_transform saat training
        self.transform = transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=mean, std=std),
        ])

        # Prioritas: TorchScript (.pt) → state dict
        ts_path = self.artifacts_dir / "insect_model.pt"
        alt_ts_path = self.artifacts_dir / "model_torchscript.pt"
        sd_path = self.artifacts_dir / "insect_model_state.pt"

        model_fmt: str = self.metadata.get("model_format", "torchscript")

        if ts_path.exists() and model_fmt == "torchscript":
            selected_ts_path = ts_path
        elif alt_ts_path.exists() and model_fmt == "torchscript":
            selected_ts_path = alt_ts_path
        else:
            selected_ts_path = None

        if selected_ts_path is not None:
            logger.info(f"Loading TorchScript model from {selected_ts_path}")
            self.model = torch.jit.load(str(selected_ts_path), map_location=self.device)
        elif sd_path.exists():
            logger.info(f"Loading state dict from {sd_path}")
            model_name  = self.metadata.get("model_name", "efficientnet_b3")
            num_classes = self.metadata.get("num_classes", len(self.metadata["class_names"]))
            self.model = timm.create_model(model_name, pretrained=False, num_classes=num_classes)
            state = torch.load(str(sd_path), map_location=self.device)
            self.model.load_state_dict(state)
            self.model = self.model.to(self.device)
        else:
            raise FileNotFoundError(
                "Tidak ada file model ditemukan di artifacts/. "
                "Expected: insect_model.pt, model_torchscript.pt, atau insect_model_state.pt"
            )

        self.model.eval()
        logger.info(f"Model loaded. Device: {self.device} | Classes: {self.metadata['num_classes']}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def predict(self, image_bytes: bytes, top_k: int = 3) -> Dict:
        """
        Melakukan inference pada gambar.

        Args:
            image_bytes: Raw bytes gambar (JPEG/PNG).
            top_k: Jumlah prediksi teratas yang dikembalikan.

        Returns:
            Dict berisi:
                - predicted_class (str): nama kelas terprediksi
                - confidence (float): nilai kepercayaan (0–1)
                - top_k (list): [{class, confidence}, ...]
        """
        class_names: List[str] = self.metadata["class_names"]

        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as e:
            raise ValueError(f"Gagal membuka gambar: {e}")

        # Preprocessing
        tensor = self.transform(image).unsqueeze(0).to(self.device)  # [1, C, H, W]

        with torch.no_grad():
            logits = self.model(tensor)                          # [1, num_classes]
            probs  = F.softmax(logits, dim=1)[0]                # [num_classes]

        # Top-k
        top_k_actual = min(top_k, len(class_names))
        top_values, top_indices = torch.topk(probs, top_k_actual)

        top_results = [
            {
                "class"     : class_names[idx.item()],
                "confidence": round(val.item(), 6),
            }
            for val, idx in zip(top_values, top_indices)
        ]

        return {
            "predicted_class": top_results[0]["class"],
            "confidence"     : top_results[0]["confidence"],
            "top_k"          : top_results,
        }

    @property
    def class_names(self) -> List[str]:
        return self.metadata.get("class_names", [])

    @property
    def num_classes(self) -> int:
        return self.metadata.get("num_classes", 0)
