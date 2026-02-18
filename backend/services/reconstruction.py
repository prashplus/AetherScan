"""
3D Reconstruction Service
Uses Fast3R for real neural 3D reconstruction.

The service is initialised eagerly at startup:
  - Raises RuntimeError immediately if fast3r is not installed.
  - Downloads + loads the pre-trained weights before marking itself ready.
  - Any WebSocket request that arrives before the model is ready gets a
    clear "not ready" error instead of a silent failure.
"""

import torch
import numpy as np
from typing import List, Dict
import logging
import asyncio
from PIL import Image

logger = logging.getLogger(__name__)

MIN_IMAGES_REQUIRED = 2
MAX_IMAGES_RECOMMENDED = 20


def _get_best_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


class ReconstructionService:
    """
    3D Reconstruction Service using Fast3R pre-trained weights.

    Call `await service.initialize()` once at application startup.
    The service will not accept image requests until initialization completes.
    """

    def __init__(self, device: str = _get_best_device()):
        self.device = device
        self.min_images = MIN_IMAGES_REQUIRED
        self.max_images = MAX_IMAGES_RECOMMENDED
        self.model = None
        self.lit_module = None
        self.ready = False  # True only after weights are loaded

        logger.info(f"ReconstructionService created (device={device})")

        # Fail fast if fast3r isn't installed at all
        try:
            import fast3r  # noqa: F401
            logger.info("✅ fast3r package found")
        except ImportError:
            raise RuntimeError(
                "fast3r is not installed.\n"
                "Clone the repo and run: pip install -e ./fast3r"
            )

    def initialize(self):
        """
        Eagerly load the Fast3R pre-trained weights.
        Blocks until the model is fully loaded (downloads if not cached).
        Call this once from the FastAPI startup event.
        """
        if self.ready:
            return

        logger.info("=" * 60)
        logger.info("Loading Fast3R pre-trained weights …")
        logger.info("  Model : jedyang97/Fast3R_ViT_Large_512")
        logger.info("  Device: %s", self.device)
        logger.info("  (First run will download ~1.8 GB — please wait)")
        logger.info("=" * 60)

        from fast3r.models.fast3r import Fast3R
        from fast3r.models.multiview_dust3r_module import MultiViewDUSt3RLitModule

        self.model = Fast3R.from_pretrained("jedyang97/Fast3R_ViT_Large_512")
        self.model = self.model.to(self.device)
        self.model.eval()

        self.lit_module = MultiViewDUSt3RLitModule.load_for_inference(self.model)
        self.lit_module.eval()

        self.ready = True
        logger.info("=" * 60)
        logger.info("✅ Fast3R model ready — accepting reconstruction requests")
        logger.info("=" * 60)

    async def process_images(self, image_paths: List[str]) -> List[Dict]:
        if not self.ready:
            raise RuntimeError(
                "Reconstruction service is not ready yet. "
                "The model may still be downloading — please try again in a moment."
            )

        if len(image_paths) < self.min_images:
            raise ValueError(
                f"Insufficient images: {len(image_paths)} provided, "
                f"minimum {self.min_images} required"
            )

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._run_inference, image_paths)

    def _run_inference(self, image_paths: List[str]) -> List[Dict]:
        """Synchronous Fast3R inference — runs in a thread pool."""
        from fast3r.dust3r.utils.image import load_images
        from fast3r.dust3r.inference_multiview import inference

        logger.info(f"Running Fast3R inference on {len(image_paths)} images …")
        images = load_images(image_paths, size=512, verbose=False)

        with torch.no_grad():
            output_dict = inference(
                images, self.model, torch.device(self.device),
                dtype=torch.float32, verbose=False
            )

        all_points = []
        for view_idx, pred in enumerate(output_dict['preds']):
            pts3d = pred['pts3d_in_other_view'].cpu().numpy()[0]   # (H, W, 3)
            conf  = pred['conf'].cpu().numpy()[0]                   # (H, W)

            img = Image.open(image_paths[view_idx]).convert('RGB')
            img = img.resize((pts3d.shape[1], pts3d.shape[0]))
            colors = np.array(img)

            mask = conf > 1.2
            valid_pts    = pts3d[mask]
            valid_colors = colors[mask]

            if len(valid_pts) > 10000:
                idx = np.random.choice(len(valid_pts), 10000, replace=False)
                valid_pts    = valid_pts[idx]
                valid_colors = valid_colors[idx]

            for p, c in zip(valid_pts, valid_colors):
                all_points.append({
                    "x": float(p[0]), "y": float(p[1]), "z": float(p[2]),
                    "r": int(c[0]),   "g": int(c[1]),   "b": int(c[2])
                })

        logger.info(f"Reconstruction complete — {len(all_points)} points")
        return all_points


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_reconstruction_service: ReconstructionService | None = None


def get_reconstruction_service() -> ReconstructionService:
    global _reconstruction_service
    if _reconstruction_service is None:
        _reconstruction_service = ReconstructionService()
    return _reconstruction_service
