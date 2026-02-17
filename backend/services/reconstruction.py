"""
3D Reconstruction Service
Hybrid implementation: Uses Fast3R if available, falls back to image-based generation
"""

import torch
import numpy as np
from typing import List, Dict, Optional
import logging
from pathlib import Path
import asyncio
from PIL import Image
import os

logger = logging.getLogger(__name__)

# Configuration
MIN_IMAGES_REQUIRED = 2
MAX_IMAGES_RECOMMENDED = 20

class ReconstructionService:
    """
    Hybrid 3D Reconstruction Service
    
    Attempts to use Fast3R for true 3D reconstruction.
    If Fast3R is not available (installation issues) or fails,
    falls back to image-based point cloud generation.
    """
    
    def __init__(self, device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        self.device = device
        self.min_images = MIN_IMAGES_REQUIRED
        self.max_images = MAX_IMAGES_RECOMMENDED
        self.model = None
        self.lit_module = None
        self.model_loaded = False
        self.fast3r_available = False
        
        logger.info(f"Reconstruction service initialized on {device}")
        
        # Check if Fast3R is available
        try:
            import fast3r
            self.fast3r_available = True
            logger.info("✅ Fast3R package found - Real user 3D reconstruction enabled")
        except ImportError:
            self.fast3r_available = False
            logger.warning("⚠️ Fast3R not found - Using image-based fallback")

    def _load_model(self):
        """Lazy load Fast3R model"""
        if self.model_loaded or not self.fast3r_available:
            return
            
        try:
            logger.info("Loading Fast3R model from Hugging Face...")
            from fast3r.models.fast3r import Fast3R
            from fast3r.models.multiview_dust3r_module import MultiViewDUSt3RLitModule
            
            # Load the pre-trained model from Hugging Face
            self.model = Fast3R.from_pretrained("jedyang97/Fast3R_ViT_Large_512")
            self.model = self.model.to(self.device)
            self.model.eval()
            
            # Create wrapper for pose estimation
            self.lit_module = MultiViewDUSt3RLitModule.load_for_inference(self.model)
            self.lit_module.eval()
            
            self.model_loaded = True
            logger.info("✅ Fast3R model loaded successfully!")
            
        except Exception as e:
            logger.error(f"Failed to load Fast3R: {e}")
            self.fast3r_available = False  # Disable for this session
            
    async def process_images(self, image_paths: List[str]) -> List[Dict[str, float]]:
        """Process images using best available method"""
        
        if len(image_paths) < self.min_images:
            raise ValueError(f"Insufficient images: {len(image_paths)} provided, minimum {self.min_images} required")
            
        if self.fast3r_available:
            try:
                # 1. Try Fast3R Reconstruction
                return await self._process_with_fast3r(image_paths)
            except Exception as e:
                logger.error(f"Fast3R failed: {e}")
                logger.warning("Falling back to image-based generation")
                # Fall through to fallback
        
        # 2. Fallback: Image-based 3D visualization
        return await self._process_with_heuristic(image_paths)

    async def _process_with_fast3r(self, image_paths: List[str]) -> List[Dict[str, float]]:
        """Run actual Fast3R reconstruction"""
        self._load_model()
        
        if not self.model_loaded:
            raise RuntimeError("Model failed to load")
            
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._run_fast3r_inference, image_paths)

    def _run_fast3r_inference(self, image_paths: List[str]) -> List[Dict[str, float]]:
        """Synchronous Fast3R inference"""
        from fast3r.dust3r.utils.image import load_images
        from fast3r.dust3r.inference_multiview import inference
        from fast3r.models.multiview_dust3r_module import MultiViewDUSt3RLitModule
        
        logger.info(f"Running Fast3R on {len(image_paths)} images...")
        images = load_images(image_paths, size=512, verbose=False)
        
        with torch.no_grad():
            output_dict, _ = inference(
                images, self.model, self.device, 
                dtype=torch.float32, verbose=False
            )
            
        # Estimate poses (if needed for export, but we just need points now)
        # We can extract points directly from the predictions
        
        all_points = []
        for view_idx, pred in enumerate(output_dict['preds']):
            pts3d = pred['pts3d_in_other_view'].cpu().numpy()[0] # [H, W, 3]
            conf = pred['conf'].cpu().numpy()[0] # [H, W]
            
            # Get colors from original image
            img = Image.open(image_paths[view_idx]).convert('RGB')
            img = img.resize((pts3d.shape[1], pts3d.shape[0]))
            colors = np.array(img)
            
            # Filter by confidence
            mask = conf > 1.2  # Threshold
            
            valid_pts = pts3d[mask]
            valid_colors = colors[mask]
            
            # Subsample if too many
            if len(valid_pts) > 10000:
                idx = np.random.choice(len(valid_pts), 10000, replace=False)
                valid_pts = valid_pts[idx]
                valid_colors = valid_colors[idx]
                
            for p, c in zip(valid_pts, valid_colors):
                all_points.append({
                    "x": float(p[0]), "y": float(p[1]), "z": float(p[2]),
                    "r": int(c[0]), "g": int(c[1]), "b": int(c[2])
                })
                
        return all_points

    async def _process_with_heuristic(self, image_paths: List[str]) -> List[Dict[str, float]]:
        """Fallback: Generate points from images (what caused 'separate clouds')"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._generate_points_from_images, image_paths)

    def _generate_points_from_images(self, image_paths: List[str]) -> List[Dict[str, float]]:
        """Heuristic generation (Visualizer only)"""
        all_points = []
        target_points = 50000 
        points_per_image = max(2000, target_points // len(image_paths))
        
        for idx, img_path in enumerate(image_paths):
            try:
                img = Image.open(img_path).convert('RGB')
                img = img.resize((128, 128))
                img_array = np.array(img)
                h, w, _ = img_array.shape
                
                for _ in range(points_per_image):
                    y, x = np.random.randint(0, h), np.random.randint(0, w)
                    r, g, b = img_array[y, x]
                    
                    # Arrange in circle
                    angle = (idx / len(image_paths)) * 2 * np.pi
                    radius = 2.0
                    
                    # Simple heuristic mapping
                    px = radius * np.cos(angle) + (x/w - 0.5) * np.cos(angle)
                    py = (y/h - 0.5) * 2.0
                    pz = radius * np.sin(angle) + (x/w - 0.5) * np.sin(angle)
                    
                    all_points.append({
                        "x": float(px), "y": float(py), "z": float(pz),
                        "r": int(r), "g": int(g), "b": int(b)
                    })
            except: pass
            
        return all_points

# Singleton
_reconstruction_service = None

def get_reconstruction_service() -> ReconstructionService:
    global _reconstruction_service
    if _reconstruction_service is None:
        _reconstruction_service = ReconstructionService()
    return _reconstruction_service
