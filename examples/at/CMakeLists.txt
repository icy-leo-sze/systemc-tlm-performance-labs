cmake_minimum_required(VERSION 3.18.4)

project(renode_systemc_at_example)

if(NOT DEFINED CMAKE_CXX_STANDARD)
    set(CMAKE_CXX_STANDARD 17)
endif()

set(EXAMPLE_NAME at)

file(GLOB_RECURSE systemc_sources systemc/src/*.cpp)

add_executable(${EXAMPLE_NAME} ${systemc_sources})

target_include_directories(${EXAMPLE_NAME} PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/systemc/include
)

include(../../cmake/systemc.cmake)
include(../../cmake/msvc.cmake)

add_subdirectory(four_phase_memory_timing)
add_subdirectory(multi_initiator_arbitration)
