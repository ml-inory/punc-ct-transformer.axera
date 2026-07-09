#!/bin/bash
# Cross-compile sherpa-punct C++ SDK for AX650 (aarch64).
#
# Prerequisites:
#   - CMake >= 3.14
#   - AX650 BSP SDK (auto-discovered or set via BSP_ROOT)
#
# BSP_ROOT resolution order:
#   1. $BSP_ROOT environment variable
#   2. cpp/ax650_sdk/ (symlink or renamed)
#   3. First AX650_SDK_* directory found under cpp/
#   4. First AX650_SDK_* under $HOME/
#   5. First AX650_SDK_* under /opt/
#
# Usage:
#   cd cpp && ./build.sh              # auto-discover
#   BSP_ROOT=/path/to/sdk ./build.sh  # explicit override
#
# Output: build/demo

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Resolve BSP_ROOT ──────────────────────────────────────────────

_find_bsp() {
    local dir="$1"
    [ -d "$dir" ] && [ -f "$dir/toolchain/bin/aarch64-none-linux-gnu-g++" ] && echo "$dir" && return 0
    return 1
}

resolve_bsp_root() {
    # 1. Explicit env var
    [ -n "${BSP_ROOT:-}" ] && { echo "$BSP_ROOT"; return 0; }

    # 2. cpp/ax650_sdk (symlink convention)
    _find_bsp "$SCRIPT_DIR/ax650_sdk" && return 0

    # 3. First AX650_SDK_* under cpp/
    for d in "$SCRIPT_DIR"/AX650_SDK_*; do
        _find_bsp "$d" && return 0
    done

    # 4. First AX650_SDK_* under $HOME
    for d in "$HOME"/AX650_SDK_*; do
        _find_bsp "$d" && return 0
    done

    # 5. First AX650_SDK_* under /opt
    for d in /opt/AX650_SDK_*; do
        _find_bsp "$d" && return 0
    done

    return 1
}

# ── Resolve AX_RUNTIME_ROOT ──────────────────────────────────────

resolve_ax_runtime() {
    local bsp="$1"

    # 1. Explicit env var
    [ -n "${AX_RUNTIME_ROOT:-}" ] && { echo "$AX_RUNTIME_ROOT"; return 0; }

    # 2. ax_engine/ inside BSP (standard layout)
    [ -d "$bsp/ax_engine" ] && { echo "$bsp/ax_engine"; return 0; }

    # 3. Check if BSP itself has include/ and lib/ (e.g., scp'd board /soc/)
    [ -d "$bsp/include" ] && [ -d "$bsp/lib" ] && { echo "$bsp"; return 0; }

    return 1
}

# ── Main ──────────────────────────────────────────────────────────

BSP_ROOT="$(resolve_bsp_root)"
if [ -z "$BSP_ROOT" ]; then
    echo "ERROR: AX650 BSP SDK not found."
    echo ""
    echo "Auto-search paths checked:"
    echo "  - cpp/ax650_sdk/"
    echo "  - cpp/AX650_SDK_*/"
    echo "  - \$HOME/AX650_SDK_*/"
    echo "  - /opt/AX650_SDK_*/"
    echo ""
    echo "Download BSP SDK or set BSP_ROOT:"
    echo "  BSP_ROOT=/path/to/AX650_SDK ./build.sh"
    exit 1
fi

AX_RUNTIME_ROOT="$(resolve_ax_runtime "$BSP_ROOT")"
if [ -z "$AX_RUNTIME_ROOT" ]; then
    echo "ERROR: AX runtime (ax_engine) not found."
    echo "  BSP_ROOT: $BSP_ROOT"
    echo "  Checked: \$BSP_ROOT/ax_engine, \$BSP_ROOT/{include,lib}"
    echo ""
    echo "Set AX_RUNTIME_ROOT manually:"
    echo "  AX_RUNTIME_ROOT=/path/to/ax_engine ./build.sh"
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
