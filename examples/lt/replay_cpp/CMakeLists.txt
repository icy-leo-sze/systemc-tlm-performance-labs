cmake_minimum_required(VERSION 3.16)

project(lt_replay_cpp LANGUAGES CXX)

add_executable(replay_cpp
  src/main.cpp
  src/cli.cpp
  src/csv_reader.cpp
  src/trace_validator.cpp
  src/replay_model.cpp
  src/metrics.cpp
  src/csv_writer.cpp
)

target_compile_features(replay_cpp PRIVATE cxx_std_17)
target_include_directories(replay_cpp PRIVATE include)

if(MSVC)
  target_compile_options(replay_cpp PRIVATE /W4)
else()
  target_compile_options(replay_cpp PRIVATE -Wall -Wextra -Wpedantic)
endif()
