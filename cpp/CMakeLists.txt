cmake_minimum_required(VERSION 3.14)
project(sherpa_punct_sdk LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# AX Engine runtime (set AX_RUNTIME_ROOT to BSP SDK or board sysroot)
if(DEFINED AX_RUNTIME_ROOT)
    message(STATUS "AX_RUNTIME_ROOT: ${AX_RUNTIME_ROOT}")
    include_directories(${AX_RUNTIME_ROOT}/include)
    link_directories(${AX_RUNTIME_ROOT}/lib)
endif()

# Library — uses native AX_ENGINE API (ax_engine_type.h, ax_engine_api.h, ax_sys_api.h)
add_library(sherpa_punct STATIC
    src/punctuation_runner.cpp
)
target_include_directories(sherpa_punct PUBLIC include)

if(DEFINED AX_RUNTIME_ROOT)
    target_link_libraries(sherpa_punct PUBLIC ax_engine ax_sys pthread dl)
endif()

# Demo
add_executable(demo examples/demo.cpp)
target_link_libraries(demo sherpa_punct)
