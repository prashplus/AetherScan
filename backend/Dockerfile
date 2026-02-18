FROM nvidia/cuda:12.1.1-devel-ubuntu22.04

# Set working directory
WORKDIR /app

# Prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

# Install Python 3.12 and system dependencies
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    git \
    wget \
    curl \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Create symbolic links for python
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1

# Install pip for Python 3.12
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12

# Copy requirements first for better caching
COPY requirements.txt .

# Install upgrade pip first
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install all Python dependencies (web framework, numerics, PyTorch CUDA, ML libs)
# --extra-index-url ensures torch/torchvision resolve to CUDA 12.1 wheels from the PyTorch index
RUN pip install --no-cache-dir \
    --extra-index-url https://download.pytorch.org/whl/cu121 \
    -r requirements.txt

# Install Fast3R (Recursively to get DUSt3R and CroCo)
# Cloned to /opt/fast3r and added to PYTHONPATH; installed via pip -e to avoid
# re-installing its Python deps (already satisfied by requirements.txt above).
RUN git clone --recursive https://github.com/facebookresearch/fast3r.git /opt/fast3r

# Set PYTHONPATH so python can find fast3r and its submodules
ENV PYTHONPATH="${PYTHONPATH}:/opt/fast3r"

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
