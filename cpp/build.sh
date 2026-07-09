#!/bin/bash
# Cross-compile sherpa-punct C++ SDK for AX650 (aarch64).
#
# Usage:
#   cd cpp && ./build.sh              # auto-download BSP if needed
#   BSP_ROOT=/path/to/sdk ./build.sh  # use existing SDK
#
# Output: build/demo

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

BSP_URL="https://hf-mirror.com/AXERA-TECH/AX650-Community-Hub/resolve/main/sdk/edge-computing-AX650_SDK_V3.10.2/02.%20SDK/AX650_SDK_V3.10.2/AX650_SDK_V3.10.2_20260513151335.tgz"
BSP_DIR="$SCRIPT_DIR/ax650_sdk"

# ── Resolve BSP_ROOT ──────────────────────────────────────────────

if [ -n "${BSP_ROOT:-}" ]; then
    # User-specified path
    true
elif [ -d "$BSP_DIR" ] && [ -f "$BSP_DIR/toolchain/bin/aarch64-none-linux-gnu-g++" ]; then
    BSP_ROOT="$BSP_DIR"
else
    # Download BSP SDK
    echo "BSP SDK not found, downloading to $BSP_DIR ..."
    mkdir -p "$BSP_DIR"
    wget -q --show-progress "$BSP_URL" -O "$SCRIPT_DIR/ax650_sdk.tgz"
    tar xzf "$SCRIPT_DIR/ax650_sdk.tgz" --strip-components=1 -C "$BSP_DIR"
    rm -f "$SCRIPT_DIR/ax650_sdk.tgz"
    BSP_ROOT="$BSP_DIR"
fi

# ── Resolve AX_RUNTIME_ROOT ──────────────────────────────────────

if [ -n "${AX_RUNTIME_ROOT:-}" ]; then
    true
elif [ -d "$BSP_ROOT/ax_engine" ]; then
    AX_RUNTIME_ROOT="$BSP_ROOT/ax_engine"
else
    AX_RUNTIME_ROOT="$BSP_ROOT"
fi

# Validate
if [ ! -f "$BSP_ROOT/toolchain/bin/aarch64-none-linux-gnu-g++" ]; then
    echo "ERROR: Cross-compiler not found at $BSP_ROOT/toolchain/bin/"
    exit 1
fi

echo "BSP_ROOT:        $BSP_ROOT"
echo "AX_RUNTIME_ROOT: $AX_RUNTIME_ROOT"
echo ""

# ── Build ─────────────────────────────────────────────────────────

rm -rf build
mkdir build && cd build

cmake .. \
    -DCMAKE_TOOLCHAIN_FILE=../toolchain-aarch64.cmake \
    -DBSP_ROOT="$BSP_ROOT" \
    -DAX_RUNTIME_ROOT="$AX_RUNTIME_ROOT" \
    -DCMAKE_BUILD_TYPE=Release

make -j"$(nproc)"

echo ""
echo "=== BUILD SUCCESS ==="
echo "Binary: $(pwd)/demo"
echo ""
echo "Deploy to board:"
echo "  scp demo root@<board>:/tmp/"
echo "  ssh root@<board> 'cd /tmp && LD_LIBRARY_PATH=/soc/lib ./demo /path/to/model.axmodel /path/to/tokens.json'"
