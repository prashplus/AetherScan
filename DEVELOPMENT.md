# AetherScan - Development Guide

This document provides guidance for developers working on AetherScan.

## Fast3R Integration

✅ **Fast3R is now fully integrated!** See [FAST3R_INTEGRATION.md](FAST3R_INTEGRATION.md) for complete documentation.

### Quick Start

The backend now uses Facebook Research's Fast3R model for real 3D reconstruction:

1. **First run**: Model automatically downloads from Hugging Face (~2GB)
2. **Upload images**: 2-10 images of the same object from different angles
3. **Reconstruction**: Fast3R processes images and generates point cloud
4. **Real-time streaming**: Points stream to frontend as they're generated

### Model Details

- **Model**: `jedyang97/Fast3R_ViT_Large_512` (from Hugging Face)
- **Architecture**: Vision Transformer (ViT) Large
- **Input**: 512x512 images
- **Output**: Colored 3D point clouds with camera poses

### Implementation

The integration is in:
- `backend/services/reconstruction.py` - Fast3R inference pipeline
- `backend/main.py` - Image handling and WebSocket streaming
- `backend/requirements.txt` - Fast3R dependencies

### Fallback Behavior

If Fast3R fails to load (no internet, no GPU, etc.), the system automatically falls back to demo point clouds so the UI remains functional.

## Development Workflow

### Starting Development Servers

**Option 1: Docker (Recommended)**
```bash
docker-compose up
```

**Option 2: Local Development**

Backend:
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

### Testing GPU Access

```bash
# Inside Docker container
docker-compose exec backend python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"

# Local
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

## Architecture Notes

### Point Streaming Performance

The `usePointStream` hook is optimized for 1M+ points:

1. **No React Re-renders**: Points stored in refs, not state
2. **GPU Buffer Updates**: Direct BufferAttribute updates
3. **Batch Processing**: Receives point chunks via WebSocket
4. **Dynamic Draw Range**: Only renders visible points

### WebSocket Message Format

All WebSocket messages follow this structure:

```typescript
{
  type: 'ping' | 'pong' | 'points' | 'image_data' | 'upload_complete' | 'image_received' | 'reconstruction_complete',
  data?: any,
  status?: string,
  total_points?: number
}
```

## Troubleshooting

### Frontend can't connect to backend
- Check `NEXT_PUBLIC_BACKEND_WS` environment variable
- Verify backend is running on port 8000
- Check Docker network configuration

### GPU not detected
- Verify NVIDIA drivers installed
- Check `nvidia-smi` output
- Ensure Docker has GPU access (nvidia-container-toolkit)

### Point cloud not rendering
- Check browser console for errors
- Verify WebSocket connection (Network tab)
- Check point data format in messages

## Production Deployment

### Backend
1. Update `backend/Dockerfile` for production build
2. Set up environment variables
3. Configure CORS origins
4. Enable HTTPS for WebSocket (WSS)

### Frontend
1. Build Next.js for production: `npm run build`
2. Update environment variables for production backend URL
3. Deploy to Vercel/Netlify or use Docker

## Performance Tips

1. **Batch Point Updates**: Send points in batches (10-100 points) to reduce message overhead
2. **Point Cloud LOD**: Consider implementing level-of-detail for very large point clouds
3. **WebSocket Compression**: Enable compression for large data transfers
4. **GPU Memory**: Monitor CUDA memory usage for large reconstructions
