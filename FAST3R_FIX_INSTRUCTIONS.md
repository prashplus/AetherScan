# Fast3R Installation Fix - Final Working Solution

## Problem
The build failed with `ERROR: Directory '.' is not installable`.
Reason: Both `DUSt3R` and `Fast3R` are research repositories that lack standard Python packaging files (`setup.py` / `pyproject.toml`). They cannot be installed with `pip install .`.

## Solution Implemented
I have switched to a **Source Installation Strategy** which is correct for research code:

1. **Recursive Clone**: We now clone `Fast3R` (which includes `DUSt3R` and `CroCo` as submodules) into a permanent location: `/opt/fast3r`.
2. **PYTHONPATH**: We add `/opt/fast3r` to the system's `PYTHONPATH`. This allows Python to import `fast3r` and `dust3r` directly from the source folder without needing them to be installed as packages.
3. **Devel Base Image**: We are using `nvidia/cuda:12.1.1-devel-ubuntu22.04` to ensure any CUDA extensions can be compiled if needed.

## Next Steps

1. **Rebuild**:
   ```bash
   docker-compose build --no-cache backend
   ```
   *(This should now succeed as we aren't forcing pip to install un-installable directories).*

2. **Restart**:
   ```bash
   docker-compose up -d
   ```

3. **Test**:
   Upload your banana images. The system will look for `fast3r` in `/opt/fast3r` and should find it successfully.
