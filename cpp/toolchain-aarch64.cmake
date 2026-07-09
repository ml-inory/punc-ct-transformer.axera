# Cross-compilation toolchain for AX650 (ARM aarch64).
#
# Environment variables:
#   CROSS_PREFIX     — path prefix to aarch64-none-linux-gnu- tools
#   BSP_ROOT         — AX650 BSP SDK root (optional, for msp headers)
#   AX_RUNTIME_ROOT  — aarch64 AX runtime libs (board /soc or BSP ax_engine)

# Cross-compiler prefix
if(NOT DEFINED CROSS_PREFIX)
    if(DEFINED ENV{CROSS_PREFIX})
        set(CROSS_PREFIX "$ENV{CROSS_PREFIX}")
    elseif(DEFINED ENV{BSP_ROOT})
        set(CROSS_PREFIX "$ENV{BSP_ROOT}/toolchain/bin/aarch64-none-linux-gnu-")
    else()
        message(FATAL_ERROR "Set CROSS_PREFIX env var to cross-compiler path")
    endif()
endif()

# BSP headers (optional)
if(NOT DEFINED BSP_ROOT AND DEFINED ENV{BSP_ROOT})
    set(BSP_ROOT "$ENV{BSP_ROOT}")
endif()
if(DEFINED BSP_ROOT)
    include_directories(${BSP_ROOT}/msp/out/include)
endif()

# AX runtime libs
if(NOT DEFINED AX_RUNTIME_ROOT AND DEFINED ENV{AX_RUNTIME_ROOT})
    set(AX_RUNTIME_ROOT "$ENV{AX_RUNTIME_ROOT}")
endif()

set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR aarch64)

set(CMAKE_C_COMPILER   ${CROSS_PREFIX}gcc)
set(CMAKE_CXX_COMPILER ${CROSS_PREFIX}g++)

set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)

if(DEFINED AX_RUNTIME_ROOT)
    link_directories(${AX_RUNTIME_ROOT}/lib)
endif()

# Library search path for cross-linker
if(DEFINED AX_RUNTIME_ROOT)
    list(APPEND CMAKE_SYSTEM_LIBRARY_PATH "${AX_RUNTIME_ROOT}/lib")
endif()
set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -L${AX_RUNTIME_ROOT}/lib")
