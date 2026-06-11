cmake_minimum_required(VERSION 3.18.4)

project(project_at1_four_phase_memory_timing LANGUAGES CXX)

set(EXAMPLE_NAME project_at1_four_phase_memory_timing)

add_executable(${EXAMPLE_NAME}
  main.cpp
)

target_compile_features(${EXAMPLE_NAME} PRIVATE cxx_std_17)

if(DEFINED USER_SYSTEMC_INCLUDE_DIR)
  target_include_directories(${EXAMPLE_NAME}
    PRIVATE
      "${USER_SYSTEMC_INCLUDE_DIR}"
  )
else()
  message(WARNING "No USER_SYSTEMC_INCLUDE_DIR specified - headers will only be included from standard locations.")
endif()

if(DEFINED USER_SYSTEMC_LIB_DIR AND EXISTS "${USER_SYSTEMC_LIB_DIR}/libsystemc.so")
  set(PROJECT_AT1_SYSTEMC_LIBRARY "${USER_SYSTEMC_LIB_DIR}/libsystemc.so")
elseif(DEFINED USER_SYSTEMC_LIB_DIR)
  message(FATAL_ERROR "SystemC library not found at ${USER_SYSTEMC_LIB_DIR}/libsystemc.so")
else()
  find_library(PROJECT_AT1_SYSTEMC_LIBRARY NAMES systemc libsystemc)
endif()

if(NOT PROJECT_AT1_SYSTEMC_LIBRARY OR PROJECT_AT1_SYSTEMC_LIBRARY MATCHES "-NOTFOUND$")
  message(FATAL_ERROR "SystemC library not found for ${EXAMPLE_NAME}; set USER_SYSTEMC_LIB_DIR")
endif()

message(STATUS "Project AT-1 linking SystemC library: ${PROJECT_AT1_SYSTEMC_LIBRARY}")

target_link_libraries(${EXAMPLE_NAME}
  PRIVATE
    "${PROJECT_AT1_SYSTEMC_LIBRARY}"
)

if(DEFINED USER_SYSTEMC_LIB_DIR)
  set_target_properties(${EXAMPLE_NAME}
    PROPERTIES
      BUILD_RPATH "${USER_SYSTEMC_LIB_DIR}"
      INSTALL_RPATH "${USER_SYSTEMC_LIB_DIR}"
  )
endif()

include(../../../cmake/msvc.cmake)

if(MSVC)
  target_compile_options(${EXAMPLE_NAME} PRIVATE /W4)
else()
  target_compile_options(${EXAMPLE_NAME} PRIVATE -Wall -Wextra -Wpedantic)
endif()
