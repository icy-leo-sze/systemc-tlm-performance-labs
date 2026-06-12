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

add_executable(project_at4_cache_mshr_pressure
    project_at4_cache_mshr_pressure.cpp
)

target_compile_features(project_at4_cache_mshr_pressure PRIVATE cxx_std_17)

if(DEFINED USER_SYSTEMC_INCLUDE_DIR)
    target_include_directories(project_at4_cache_mshr_pressure PRIVATE
        ${USER_SYSTEMC_INCLUDE_DIR}
    )
endif()

set(PROJECT_AT4_SYSTEMC_LIBRARY "")

if(DEFINED USER_SYSTEMC_LIB_DIR)
    set(PROJECT_AT4_EXPLICIT_SYSTEMC_LIBRARY
        "${USER_SYSTEMC_LIB_DIR}/libsystemc.so"
    )

    if(EXISTS "${PROJECT_AT4_EXPLICIT_SYSTEMC_LIBRARY}")
        set(PROJECT_AT4_SYSTEMC_LIBRARY "${PROJECT_AT4_EXPLICIT_SYSTEMC_LIBRARY}")
    else()
        find_library(PROJECT_AT4_SYSTEMC_LIBRARY
            NAMES systemc libsystemc
            PATHS "${USER_SYSTEMC_LIB_DIR}"
            NO_DEFAULT_PATH
        )
    endif()
endif()

if(NOT PROJECT_AT4_SYSTEMC_LIBRARY)
    find_library(PROJECT_AT4_SYSTEMC_LIBRARY NAMES systemc libsystemc)
endif()

if(NOT PROJECT_AT4_SYSTEMC_LIBRARY OR PROJECT_AT4_SYSTEMC_LIBRARY MATCHES "-NOTFOUND$")
    message(FATAL_ERROR "Project AT-4 SystemC library not found")
endif()

message(STATUS "Project AT-4 linking SystemC library: ${PROJECT_AT4_SYSTEMC_LIBRARY}")

target_link_libraries(project_at4_cache_mshr_pressure PRIVATE
    "${PROJECT_AT4_SYSTEMC_LIBRARY}"
)

add_executable(project_at5_backpressure_qos_collapse
    project_at5_backpressure_qos_collapse.cpp
)

target_compile_features(project_at5_backpressure_qos_collapse PRIVATE cxx_std_17)

if(DEFINED USER_SYSTEMC_INCLUDE_DIR)
    target_include_directories(project_at5_backpressure_qos_collapse PRIVATE
        ${USER_SYSTEMC_INCLUDE_DIR}
    )
endif()

set(PROJECT_AT5_SYSTEMC_LIBRARY "")

if(DEFINED USER_SYSTEMC_LIB_DIR)
    set(PROJECT_AT5_EXPLICIT_SYSTEMC_LIBRARY
        "${USER_SYSTEMC_LIB_DIR}/libsystemc.so"
    )

    if(EXISTS "${PROJECT_AT5_EXPLICIT_SYSTEMC_LIBRARY}")
        set(PROJECT_AT5_SYSTEMC_LIBRARY "${PROJECT_AT5_EXPLICIT_SYSTEMC_LIBRARY}")
    else()
        find_library(PROJECT_AT5_SYSTEMC_LIBRARY
            NAMES systemc libsystemc
            PATHS "${USER_SYSTEMC_LIB_DIR}"
            NO_DEFAULT_PATH
        )
    endif()
endif()

if(NOT PROJECT_AT5_SYSTEMC_LIBRARY)
    find_library(PROJECT_AT5_SYSTEMC_LIBRARY NAMES systemc libsystemc)
endif()

if(NOT PROJECT_AT5_SYSTEMC_LIBRARY OR PROJECT_AT5_SYSTEMC_LIBRARY MATCHES "-NOTFOUND$")
    message(FATAL_ERROR "Project AT-5 SystemC library not found")
endif()

message(STATUS "Project AT-5 linking SystemC library: ${PROJECT_AT5_SYSTEMC_LIBRARY}")

target_link_libraries(project_at5_backpressure_qos_collapse PRIVATE
    "${PROJECT_AT5_SYSTEMC_LIBRARY}"
)

add_subdirectory(four_phase_memory_timing)
add_subdirectory(multi_initiator_arbitration)
add_subdirectory(qos_sensitivity_sla)
