cmake_minimum_required(VERSION 3.16)

project(project_e_banked_memory_controller LANGUAGES CXX)

add_executable(banked_memory_controller
  src/main.cpp
  src/banked_memory_model.cpp
  src/cli.cpp
  src/csv.cpp
)

target_compile_features(banked_memory_controller PRIVATE cxx_std_17)
target_include_directories(banked_memory_controller PRIVATE include)

if(MSVC)
  target_compile_options(banked_memory_controller PRIVATE /W4)
else()
  target_compile_options(banked_memory_controller PRIVATE -Wall -Wextra -Wpedantic)
endif()
