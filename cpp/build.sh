#!/bin/bash
# Cross-compile sherpa-punct C++ SDK for AX650 (aarch64).
#
# Usage:
#   cd cpp && ./build.sh              # auto-download toolchain + BSP
#   CROSS_PREFIX=/path/to/bin/...-    # use specific cross-compiler
#   BSP_ROOT=/path/to/sdk ./build.sh  # use existing BSP SDK
#
# Output: build/demo

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

TOOLCHAIN_URL="https://developer.arm.com/-/media/Files/downloads/gnu-a/9.2-2019.12/binrel/gcc-arm-9.2-2019.12-x86_64-aarch64-none-linux-gnu.tar.xz"
BSP_URL="https://hf-mirror.com/AXERA-TECH/AX650-Community-Hub/resolve/main/sdk/edge-computing-AX650_SDK_V3.10.2/02.%20SDK/AX650_SDK_V3.10.2/AX650_SDK_V3.10.2_20260513151335.tgz"

# ── Resolve cross-compiler (CROSS_PREFIX) ─────────────────────────

resolve_cross_prefix() {
    local name="aarch64-none-linux-gnu-g++"

    [ -n "${CROSS_PREFIX:-}" ] && return 0

    if command -v "$name" &>/dev/null; then
        echo "$(dirname "$(command -v "$name")")/aarch64-none-linux-gnu-"
        return 0
    fi

    for dir in \
        "$SCRIPT_DIR/toolchain" \
        "$HOME/gcc-arm-9.2-2019.12-x86_64-aarch64-none-linux-gnu" \
        /opt/gcc-arm-9.2-2019.12-x86_64-aarch64-none-linux-gnu; do
        if [ -f "$dir/bin/$name" ]; then
            echo "$dir/bin/aarch64-none-linux-gnu-"
            return 0
        fi
    done

    local tc="$SCRIPT_DIR/toolchain"
    echo "Downloading ARM GNU toolchain..."
    mkdir -p "$tc"
    wget -q --show-progress "$TOOLCHAIN_URL" -O "$SCRIPT_DIR/toolchain.tar.xz"
    tar xf "$SCRIPT_DIR/toolchain.tar.xz" --strip-components=1 -C "$tc"
    rm -f "$SCRIPT_DIR/toolchain.tar.xz"
    echo "$tc/bin/aarch64-none-linux-gnu-"
}

CROSS_PREFIX="$(resolve_cross_prefix)"

# ── Resolve BSP_ROOT (headers + NPU libs) ─────────────────────────

resolve_bsp_root() {
    [ -n "${BSP_ROOT:-}" ] && return 0

    local bsp="$SCRIPT_DIR/ax650_sdk"
    if [ -d "$bsp/msp/out/include" ]; then
        return 0  # already cached, caller prints the path
    fi

    echo "BSP SDK not cached, downloading (one-time)..."
    rm -rf "$bsp"
    mkdir -p "$bsp"
    wget -q --show-progress "$BSP_URL" -O "$SCRIPT_DIR/ax650_sdk.tgz"
    tar xzf "$SCRIPT_DIR/ax650_sdk.tgz" --strip-components=1 -C "$bsp"
    rm -f "$SCRIPT_DIR/ax650_sdk.tgz"
}

resolve_bsp_root
BSP_ROOT="${BSP_ROOT:-$SCRIPT_DIR/ax650_sdk}"

# ── Resolve AX_RUNTIME_ROOT ──────────────────────────────────────

if [ -n "${AX_RUNTIME_ROOT:-}" ]; then
    true
elif [ -d "$BSP_ROOT/ax_engine" ]; then
    AX_RUNTIME_ROOT="$BSP_ROOT/ax_engine"
else
    AX_RUNTIME_ROOT="$BSP_ROOT/msp/out"
fi

echo "CROSS_PREFIX:     $CROSS_PREFIX"
if [ -d "$BSP_ROOT/msp/out/include" ]; then
    echo "BSP_ROOT:         $BSP_ROOT (cached)"
else
    echo "BSP_ROOT:         $BSP_ROOT"
fi
echo "AX_RUNTIME_ROOT:  $AX_RUNTIME_ROOT"
echo ""

# ── Build ─────────────────────────────────────────────────────────
export CROSS_PREFIX BSP_ROOT AX_RUNTIME_ROOT

rm -rf build
mkdir build && cd build

cmake .. \
    -DCMAKE_TOOLCHAIN_FILE=../toolchain-aarch64.cmake \
    -DCMAKE_BUILD_TYPE=Release

make -j"$(nproc)"

echo ""
echo "=== BUILD SUCCESS ==="
echo "Binary: $(pwd)/demo"
echo ""
echo "Deploy to board:"
echo "  scp demo root@<board>:/tmp/"
echo "  ssh root@<board> 'cd /tmp && LD_LIBRARY_PATH=/soc/lib ./demo /path/to/model.axmodel /path/to/tokens.json'"
