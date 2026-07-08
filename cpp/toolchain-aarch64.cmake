# Cross-compilation toolchain for AX650 (ARM aarch64)
# Requires:
#   - BSP_ROOT: path to AX650 BSP SDK (for headers)
#   - AX_RUNTIME_ROOT: path to aarch64 AX runtime libs (e.g., board /soc/lib)

if(NOT DEFINED BSP_ROOT)
    set(BSP_ROOT "$ENV{BSP_ROOT}" CACHE PATH "AX650 BSP SDK root directory")
endif()
if(NOT BSP_ROOT)
    message(FATAL_ERROR "Set BSP_ROOT to AX650 BSP SDK path or -DBSP_ROOT=<path>")
endif()

if(NOT DEFINED AX_RUNTIME_ROOT)
    set(AX_RUNTIME_ROOT "$ENV{AX_RUNTIME_ROOT}" CACHE PATH "Aarch64 AX runtime libs directory")
endif()

set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR aarch64)

# Cross-compiler from BSP
set(CROSS_PREFIX ${BSP_ROOT}/toolchain/bin/aarch64-none-linux-gnu-)
set(CMAKE_C_COMPILER   ${CROSS_PREFIX}gcc)
set(CMAKE_CXX_COMPILER ${CROSS_PREFIX}g++)

set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)

# Include dirs from BSP msp/out
include_directories(${BSP_ROOT}/msp/out/include)

# AX runtime libs (from board or pre-extracted)
if(AX_RUNTIME_ROOT)
    link_directories(${AX_RUNTIME_ROOT})
    set(AX_RUNTIME_ROOT ${AX_RUNTIME_ROOT})
endif()
