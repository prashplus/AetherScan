from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import torch
import asyncio
import json
import logging
from typing import List
import sys

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

# Global state for GPU check
GPU_AVAILABLE = False
GPU_INFO = {}


@app.on_event("startup")
async def startup_event():
    """Check GPU availability on startup"""
    global GPU_AVAILABLE, GPU_INFO
    
    GPU_AVAILABLE = torch.cuda.is_available()
    
    if GPU_AVAILABLE:
        GPU_INFO = {
            "available": True,
            "device_count": torch.cuda.device_count(),
            "device_name": torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else None,
            "cuda_version": torch.version.cuda,
            "pytorch_version": torch.__version__,
        }
        logger.info(f"✅ GPU is available: {GPU_INFO['device_name']}")
        logger.info(f"   CUDA Version: {GPU_INFO['cuda_version']}")
        logger.info(f"   PyTorch Version: {GPU_INFO['pytorch_version']}")
    else:
        GPU_INFO = {
            "available": False,
            "message": "No GPU detected. Running in CPU mode."
        }
        logger.warning("⚠️  GPU is NOT available. Running in CPU mode.")
        logger.warning("   Please ensure NVIDIA drivers and CUDA are properly installed.")


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
    """Health check endpoint with GPU status"""
    return {
        "status": "healthy",
        "gpu": GPU_INFO
    }


@app.websocket("/ws/reconstruct")
async def websocket_reconstruct(websocket: WebSocket):
    """
    WebSocket endpoint for real-time 3D reconstruction
    Receives image data and streams back point cloud chunks
    """
    await websocket.accept()
    logger.info("WebSocket connection established")
    
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
                logger.info(f"Client uploaded {message.get('count', 0)} images")
                
                # TODO: Implement Fast3R reconstruction here
                # For now, send demo point cloud data
                await send_demo_points(websocket)
                
                # Send completion signal
                await websocket.send_json({
                    "type": "reconstruction_complete",
                    "total_points": 1000
                })
                
            elif message_type == "image_data":
                # Receive image data chunk
                image_data = message.get("data")
                logger.info(f"Received image data chunk: {len(image_data)} bytes")
                
                # TODO: Process image with Fast3R
                # For now, acknowledge receipt
                await websocket.send_json({
                    "type": "image_received",
                    "status": "processing"
                })
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason=str(e))


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
