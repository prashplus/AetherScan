from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import torch
import asyncio
import json
import logging
from typing import List
import sys
import base64
from pathlib import Path
import tempfile
import os
from services.reconstruction import get_reconstruction_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AetherScan Backend",
    description="GPU-accelerated 3D reconstruction API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state for GPU/accelerator check
GPU_AVAILABLE = False
GPU_INFO = {}

def get_best_device() -> str:
    """Return the best available torch device: cuda > mps > cpu"""
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


@app.on_event("startup")
async def startup_event():
    """Detect accelerator and eagerly load the Fast3R model."""
    global GPU_AVAILABLE, GPU_INFO

    device = get_best_device()

    if device == "cuda":
        GPU_AVAILABLE = True
        GPU_INFO = {
            "available": True,
            "backend": "cuda",
            "device_count": torch.cuda.device_count(),
            "device_name": torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else None,
            "cuda_version": torch.version.cuda,
            "pytorch_version": torch.__version__,
        }
        logger.info(f"✅ CUDA GPU available: {GPU_INFO['device_name']}")
    elif device == "mps":
        GPU_AVAILABLE = True
        GPU_INFO = {
            "available": True,
            "backend": "mps",
            "device_name": "Apple Silicon GPU (MPS)",
            "pytorch_version": torch.__version__,
        }
        logger.info("✅ Apple Silicon MPS GPU available")
    else:
        GPU_AVAILABLE = False
        GPU_INFO = {
            "available": False,
            "backend": "cpu",
            "message": "No GPU detected. Running in CPU mode.",
        }
        logger.warning("⚠️  No GPU detected. Running in CPU mode.")

    # Eagerly load Fast3R — blocks until weights are downloaded + loaded.
    # The server is technically accepting connections at this point but
    # reconstruction requests will get a "not ready" error until this finishes.
    logger.info("Initialising reconstruction service …")
    loop = asyncio.get_event_loop()
    try:
        service = get_reconstruction_service()
        await loop.run_in_executor(None, service.initialize)
    except Exception as e:
        logger.error(f"❌ Failed to initialise reconstruction service: {e}")
        raise


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AetherScan Backend API",
        "version": "1.0.0",
        "gpu_available": GPU_AVAILABLE
    }


@app.get("/health")
async def health_check():
    """Health check endpoint with GPU and model status"""
    service = get_reconstruction_service()
    return {
        "status": "healthy",
        "gpu": GPU_INFO,
        "model_ready": service.ready,
    }


@app.get("/status")
async def status():
    """
    Lightweight readiness probe.
    Returns 200 + ready=true once the Fast3R model is fully loaded.
    Returns 503 + ready=false while the model is still loading.
    """
    service = get_reconstruction_service()
    if service.ready:
        return JSONResponse(
            status_code=200,
            content={"ready": True, "message": "Model loaded and ready"}
        )
    return JSONResponse(
        status_code=503,
        content={"ready": False, "message": "Model is still loading — please wait"}
    )


@app.websocket("/ws/reconstruct")
async def websocket_reconstruct(websocket: WebSocket):
    """
    WebSocket endpoint for real-time 3D reconstruction
    Receives image data and streams back point cloud chunks
    """
    await websocket.accept()
    logger.info("WebSocket connection established")
    
    # Store uploaded images for this session
    session_images = []
    temp_dir = None
    
    try:
        while True:
            # Receive data from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            message_type = message.get("type")
            
            if message_type == "ping":
                # Respond to ping
                await websocket.send_json({"type": "pong"})
                
            elif message_type == "upload_complete":
                # Client finished uploading images
                image_count = message.get('count', 0)
                logger.info(f"Client uploaded {image_count} images")
                
                if len(session_images) == 0:
                    logger.warning("No images received, sending demo points")
                    await send_demo_points(websocket)
                else:
                    # Run Fast3R reconstruction
                    logger.info(f"Starting reconstruction with {len(session_images)} images")
                    await run_reconstruction(websocket, session_images)
                
                # Clean up temp files
                if temp_dir and os.path.exists(temp_dir):
                    import shutil
                    shutil.rmtree(temp_dir)
                    logger.info("Cleaned up temporary files")
                
            elif message_type == "image_data":
                # Receive image data chunk
                image_data = message.get("data")
                filename = message.get("filename", f"image_{len(session_images)}.jpg")
                
                logger.info(f"Received image: {filename}")
                
                try:
                    # Create temp directory if needed
                    if temp_dir is None:
                        temp_dir = tempfile.mkdtemp(prefix="aetherscan_")
                        logger.info(f"Created temp directory: {temp_dir}")
                    
                    # Decode base64 image data
                    # Format: "data:image/jpeg;base64,/9j/4AAQ..."
                    if ";base64," in image_data:
                        image_data = image_data.split(";base64,")[1]
                    
                    image_bytes = base64.b64decode(image_data)
                    
                    # Save to temp file
                    temp_path = os.path.join(temp_dir, filename)
                    with open(temp_path, "wb") as f:
                        f.write(image_bytes)
                    
                    # Resolve real path to avoid macOS symlink issues
                    # (/var/folders/... vs /private/var/folders/...)
                    session_images.append(os.path.realpath(temp_path))
                    logger.info(f"Saved image to {temp_path} ({len(image_bytes)} bytes)")
                    
                    # Acknowledge receipt
                    await websocket.send_json({
                        "type": "image_received",
                        "status": "saved",
                        "filename": filename
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to save image: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Failed to save image: {str(e)}"
                    })
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        import traceback
        traceback.print_exc()
        await websocket.close(code=1011, reason=str(e))
    finally:
        # Clean up on disconnect
        if temp_dir and os.path.exists(temp_dir):
            import shutil
            try:
                shutil.rmtree(temp_dir)
                logger.info("Cleaned up temporary files on disconnect")
            except Exception as e:
                logger.error(f"Failed to clean up temp dir: {e}")


async def run_reconstruction(websocket: WebSocket, image_paths: List[str]):
    """
    Run Fast3R reconstruction and stream points to client
    """
    try:
        # Get reconstruction service
        service = get_reconstruction_service()
        
        # Process images
        logger.info("Running Fast3R reconstruction...")
        points = await service.process_images(image_paths)
        
        logger.info(f"Reconstruction complete. Got {len(points)} points")
        
        # Stream points in chunks
        chunk_size = 100
        for i in range(0, len(points), chunk_size):
            chunk = points[i:i+chunk_size]
            await websocket.send_json({
                "type": "points",
                "data": chunk
            })
            # Small delay to avoid overwhelming the client
            await asyncio.sleep(0.01)
        
        # Send completion signal
        await websocket.send_json({
            "type": "reconstruction_complete",
            "total_points": len(points)
        })
        
    except Exception as e:
        logger.error(f"Reconstruction failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Send error to client — do NOT fall back to demo points
        await websocket.send_json({
            "type": "error",
            "message": f"Reconstruction failed: {str(e)}"
        })


async def send_demo_points(websocket: WebSocket):
    """
    Send demo point cloud data to test the streaming pipeline
    """
    import random
    
    # Generate 1000 random points for demo
    for i in range(100):
        points = []
        for _ in range(10):  # Send 10 points per chunk
            point = {
                "x": random.uniform(-1.0, 1.0),
                "y": random.uniform(-1.0, 1.0),
                "z": random.uniform(-1.0, 1.0),
                "r": random.randint(0, 255),
                "g": random.randint(0, 255),
                "b": random.randint(0, 255),
            }
            points.append(point)
        
        await websocket.send_json({
            "type": "points",
            "data": points
        })
        
        # Small delay to simulate processing time
        await asyncio.sleep(0.01)
    
    # Send completion
    await websocket.send_json({
        "type": "reconstruction_complete",
        "total_points": 1000
    })


@app.post("/export/ply")
async def export_ply(points: List[dict]):
    """
    Export point cloud data as PLY file
    """
    from utils.ply_exporter import export_to_ply
    
    try:
        ply_content = export_to_ply(points)
        return JSONResponse(
            content={"ply": ply_content},
            headers={
                "Content-Disposition": "attachment; filename=pointcloud.ply"
            }
        )
    except Exception as e:
        logger.error(f"PLY export error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
