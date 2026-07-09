#!/bin/bash
# Cross-compile sherpa-punct C++ SDK for AX650 (aarch64).
#
# Prerequisites:
#   - CMake >= 3.14
#   - AX650 BSP SDK (set BSP_ROOT or place under cpp/ax650_sdk/)
#
# Usage:
#   cd cpp
#   BSP_ROOT=/path/to/AX650_SDK ./build.sh
#   # Or place SDK at cpp/ax650_sdk and just run:
#   ./build.sh
#
# Output: build/demo

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Resolve BSP_ROOT
BSP_ROOT="${BSP_ROOT:-$SCRIPT_DIR/ax650_sdk}"
AX_RUNTIME_ROOT="${AX_RUNTIME_ROOT:-$BSP_ROOT/ax_engine}"

if [ ! -d "$BSP_ROOT" ]; then
    echo "ERROR: BSP SDK not found at $BSP_ROOT"
    echo ""
    echo "Download AX650 BSP SDK:"
    echo "  wget <BSP_URL> -O ax650_sdk.tgz"
    echo "  tar xzf ax650_sdk.tgz -C $SCRIPT_DIR"
    echo "  mv $SCRIPT_DIR/AX650_SDK_* $SCRIPT_DIR/ax650_sdk"
    echo ""
    echo "Or set BSP_ROOT environment variable:"
    echo "  BSP_ROOT=/path/to/AX650_SDK ./build.sh"
    exit 1
fi

if [ ! -f "$BSP_ROOT/toolchain/bin/aarch64-none-linux-gnu-g++" ]; then
    echo "ERROR: Cross-compiler not found at $BSP_ROOT/toolchain/bin/"
    exit 1
fi

echo "BSP_ROOT:        $BSP_ROOT"
echo "AX_RUNTIME_ROOT: $AX_RUNTIME_ROOT"
echo ""

# Build
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
