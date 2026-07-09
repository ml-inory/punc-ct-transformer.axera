#!/bin/bash
# Pulsar2 compilation script for sherpa-punct-ct-transformer
# 
# Prerequisites:
#   - Docker with pulsar2:6.0 image
#   - model.onnx in current directory
#   - calibrtar_data.tar.gz in current directory
#   - pulsar2_config.json in current directory
#
# Output: compile/model.axmodel

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Verify prerequisites
if [ ! -f "export/model.onnx" ]; then
    echo "ERROR: export/model.onnx not found. Run:"
    echo "  python export_onnx.py --input model.onnx"
    exit 1
fi

if [ ! -f "pulsar2_config.json" ]; then
    echo "ERROR: pulsar2_config.json not found."
    exit 1
fi

if [ ! -f "export/calib_data.tar.gz" ]; then
    echo "WARNING: calib_data.tar.gz not found. Quantization may fail."
    echo "Generate calibration data with numpy (10 Chinese text samples, int32 token IDs)."
    exit 1
fi

# Check Docker
if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker is not running or not accessible."
    echo "Install Docker and ensure current user is in the docker group:"
    echo "  sudo usermod -aG docker \$USER"
    echo "Then log out and back in."
    exit 1
fi

# Check Pulsar2 image
if ! docker image inspect pulsar2:6.0 > /dev/null 2>&1; then
    echo "ERROR: pulsar2:6.0 Docker image not found."
    echo ""
    echo "Download and import the image from HuggingFace:"
    echo "  wget https://hf-mirror.com/AXERA-TECH/Pulsar2/resolve/main/pulsar2_6.0.tar.gz"
    echo "  docker load -i pulsar2_6.0.tar.gz"
    exit 1
fi

# Clean previous build
rm -rf compile/work compile/model.axmodel
mkdir -p compile

# Run Pulsar2 build
echo "Starting Pulsar2 compilation..."
echo "Target: AX650, NPU3"
echo "Model: sherpa-punct-ct-transformer"
echo ""

docker run --rm \
    -v "$(pwd):/ws" \
    -w /ws \
    pulsar2:6.0 \
    -c "pulsar2 build --config /ws/pulsar2_config.json 2>&1 | tee compile/compile.log"

# Check result
if [ -f "compile/model.axmodel" ]; then
    size=$(du -h compile/model.axmodel | cut -f1)
    echo ""
    echo "=== COMPILATION SUCCESS ==="
    echo "AXMODEL: compile/model.axmodel (${size})"
else
    echo ""
    echo "=== COMPILATION FAILED ==="
    echo "Check compile/compile.log for details."
    echo "Common issues:"
    echo "  - Ensure ONNX is static shape (all dims are fixed integers)"
    echo "  - Ensure calibration data matches input config"
    echo "  - Check disk space (at least 1GB free)"
    exit 1
fi
