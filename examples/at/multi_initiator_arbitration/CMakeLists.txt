cmake_minimum_required(VERSION 3.18.4)

project(project_at2_multi_initiator_arbitration LANGUAGES CXX)

set(EXAMPLE_NAME project_at2_multi_initiator_arbitration)

add_executable(${EXAMPLE_NAME}
  main.cpp
)

target_compile_features(${EXAMPLE_NAME} PRIVATE cxx_std_17)

set(PROJECT_AT2_SYSTEMC_LIBRARY "")

if(DEFINED USER_SYSTEMC_LIB_DIR)
  set(PROJECT_AT2_EXPLICIT_SYSTEMC_LIBRARY
    "${USER_SYSTEMC_LIB_DIR}/libsystemc.so"
  )

  if(EXISTS "${PROJECT_AT2_EXPLICIT_SYSTEMC_LIBRARY}")
    set(PROJECT_AT2_SYSTEMC_LIBRARY "${PROJECT_AT2_EXPLICIT_SYSTEMC_LIBRARY}")
  else()
    message(STATUS
      "Project AT-2 did not find ${PROJECT_AT2_EXPLICIT_SYSTEMC_LIBRARY}; "
      "searching only USER_SYSTEMC_LIB_DIR=${USER_SYSTEMC_LIB_DIR}"
    )
    foreach(PROJECT_AT2_LOCAL_SYSTEMC_NAME
        libsystemc.dylib
        libsystemc.a
        libsystemc.so
    )
      if(NOT PROJECT_AT2_SYSTEMC_LIBRARY
          AND EXISTS "${USER_SYSTEMC_LIB_DIR}/${PROJECT_AT2_LOCAL_SYSTEMC_NAME}")
        set(PROJECT_AT2_SYSTEMC_LIBRARY
          "${USER_SYSTEMC_LIB_DIR}/${PROJECT_AT2_LOCAL_SYSTEMC_NAME}"
        )
      endif()
    endforeach()
    if(NOT PROJECT_AT2_SYSTEMC_LIBRARY)
      find_library(PROJECT_AT2_SYSTEMC_LIBRARY
        NAMES systemc libsystemc
        PATHS "${USER_SYSTEMC_LIB_DIR}"
        NO_DEFAULT_PATH
      )
    endif()
  endif()
else()
  message(WARNING
    "No USER_SYSTEMC_LIB_DIR specified for Project AT-2 - attempting to use "
    "the parent SystemC target or a system-wide SystemC installation."
  )
  if(TARGET systemc)
    get_target_property(PROJECT_AT2_SYSTEMC_LIBRARY systemc IMPORTED_LOCATION)
  endif()
  if(NOT PROJECT_AT2_SYSTEMC_LIBRARY)
    find_library(PROJECT_AT2_SYSTEMC_LIBRARY NAMES systemc libsystemc)
  endif()
endif()

if(NOT PROJECT_AT2_SYSTEMC_LIBRARY OR PROJECT_AT2_SYSTEMC_LIBRARY MATCHES "-NOTFOUND$")
  message(FATAL_ERROR
    "SystemC library not found for ${EXAMPLE_NAME}; set USER_SYSTEMC_LIB_DIR"
  )
endif()

target_link_libraries(${EXAMPLE_NAME} PRIVATE "${PROJECT_AT2_SYSTEMC_LIBRARY}")

if(DEFINED USER_SYSTEMC_INCLUDE_DIR)
  target_include_directories(${EXAMPLE_NAME} PRIVATE "${USER_SYSTEMC_INCLUDE_DIR}")
elseif(TARGET systemc)
  get_target_property(PROJECT_AT2_SYSTEMC_INCLUDE_DIRS
    systemc INTERFACE_INCLUDE_DIRECTORIES
  )
  if(PROJECT_AT2_SYSTEMC_INCLUDE_DIRS)
    target_include_directories(${EXAMPLE_NAME} PRIVATE
      "${PROJECT_AT2_SYSTEMC_INCLUDE_DIRS}"
    )
  endif()
else()
  message(WARNING
    "No USER_SYSTEMC_INCLUDE_DIR specified for Project AT-2 - headers will "
    "only be included from standard locations."
  )
endif()

include(../../../cmake/msvc.cmake)

if(MSVC)
  target_compile_options(${EXAMPLE_NAME} PRIVATE /W4)
else()
  target_compile_options(${EXAMPLE_NAME} PRIVATE -Wall -Wextra -Wpedantic)
endif()
