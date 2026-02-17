# Quick Start Guide - After Build Completes

## Current Status
🔄 **Docker build in progress** - Installing Fast3R and dependencies (~3-4 GB)

## Once Build Completes

### 1. Start the Containers
```bash
cd d:\Github\AetherScan
docker-compose up
```

### 2. Wait for Model Download (First Time Only)
When you upload images for the first time, you'll see in the logs:
```
Loading Fast3R model from Hugging Face...
Downloading model... (~2 GB)
✅ Fast3R model loaded successfully!
```

### 3. Test with Images
- Upload 3-5 images of an object from different angles
- Watch the backend logs for:
  ```
  Running Fast3R inference...
  Extracting point clouds...
  Extracted X points from Y views
  ```

## How to Tell It's Working

### ❌ Demo Mode (Old Behavior)
- Backend logs: "Got 1000 points"
- Point cloud: Random sphere shape
- Not related to your images

### ✅ Fast3R Mode (New Behavior)
- Backend logs: "Loading Fast3R model...", "Running Fast3R inference..."
- Point cloud: Actual 3D reconstruction of your uploaded images
- Point count varies based on images (typically 10,000-100,000 points)

## Monitoring the Build

To check build progress:
```bash
docker-compose logs backend --follow
```

## Troubleshooting

### Build Taking Too Long
- This is normal! ~3-4 GB of downloads
- Check your internet connection
- Be patient, it's a one-time process

### Build Fails
- Check Docker has enough disk space (need ~10 GB free)
- Check internet connection
- Try: `docker-compose build --no-cache backend`

### After Build, Still Getting Demo Points
1. Make sure you stopped old containers: `docker-compose down`
2. Rebuild: `docker-compose build backend`
3. Start fresh: `docker-compose up`
4. Check logs: `docker-compose logs backend`

## Expected Timeline

1. ✅ Code changes made (DONE)
2. 🔄 Docker build (IN PROGRESS - 10-30 min)
3. ⏳ Start containers (1 min)
4. ⏳ First image upload triggers model download (2-5 min)
5. ⏳ Subsequent uploads use cached model (instant)
6. ✅ Real 3D reconstruction working!

## Next Steps

Once the build completes, I'll help you:
1. Start the containers
2. Test with sample images
3. Verify Fast3R is working
4. Troubleshoot any issues

---

**Current build status**: Check with `docker-compose logs backend --tail=20`
