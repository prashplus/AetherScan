# AetherScan - Development Guide

This document provides guidance for developers working on AetherScan.

## Fast3R Integration

The backend currently uses a placeholder reconstruction service. To integrate Fast3R:

### Installation

1. **Clone Fast3R repository**:
   ```bash
   cd backend
   git clone <fast3r-repo-url>
   ```

2. **Install dependencies**:
   ```bash
   pip install -r fast3r/requirements.txt
   ```

3. **Update `backend/services/reconstruction.py`**:
   - Import Fast3R model
   - Load the model in `__init__`
   - Implement `process_images` with actual Fast3R inference
   - Process point cloud output and convert to frontend format

### Expected Integration Points

```python
# In reconstruction.py
from fast3r import Fast3RModel  # Replace with actual import

class ReconstructionService:
    def __init__(self, device="cuda"):
        self.device = device
        self.model = Fast3RModel.load_pretrained()  # Replace with actual loading
        self.model.to(self.device)
        self.model.eval()
    
    async def process_images(self, images: List[np.ndarray]) -> List[Dict[str, float]]:
        # Run Fast3R inference
        with torch.no_grad():
            result = self.model(images)
        
        # Convert to point cloud format
        points = self._convert_to_points(result)
        return points
```

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
