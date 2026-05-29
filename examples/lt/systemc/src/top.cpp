/*****************************************************************************

  Licensed to Accellera Systems Initiative Inc. (Accellera) under one or
  more contributor license agreements.  See the NOTICE file distributed
  with this work for additional information regarding copyright ownership.
  Accellera licenses this file to you under the Apache License, Version 2.0
  (the "License"); you may not use this file except in compliance with the
  License.  You may obtain a copy of the License at

    http:

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
  implied.  See the License for the specific language governing
  permissions and limitations under the License.

 *****************************************************************************/
#include "top.h"

#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <string>
#include <system_error>

namespace {
typedef std::map<std::string, std::string> config_map;

std::string trim(const std::string& value) {
  const std::string whitespace = " \t\r\n";
  const std::string::size_type begin = value.find_first_not_of(whitespace);
  if (begin == std::string::npos) {
    return "";
  }

  const std::string::size_type end = value.find_last_not_of(whitespace);
  return value.substr(begin, end - begin + 1);
}

std::filesystem::path workloadConfigPath() {
  std::error_code error;
  std::filesystem::path executablePath =
      std::filesystem::read_symlink("/proc/self/exe", error);
  if (error) {
    return std::filesystem::path();
  }

  return executablePath.parent_path().parent_path() / "results" /
         "workload_config.env";
}

config_map readWorkloadConfigFile() {
  config_map values;
  const std::filesystem::path path = workloadConfigPath();
  if (path.empty()) {
    return values;
  }

  std::error_code error;
  if (!std::filesystem::exists(path, error) || error) {
    return values;
  }

  std::ifstream config(path);
  if (!config) {
    std::cerr << "[workload_config] failed to open " << path << std::endl;
    return values;
  }

  std::string line;
  while (std::getline(config, line)) {
    const std::string stripped = trim(line);
    if (stripped.empty() || stripped[0] == '#') {
      continue;
    }

    const std::string::size_type separator = stripped.find('=');
    if (separator == std::string::npos) {
      continue;
    }

    values[trim(stripped.substr(0, separator))] =
        trim(stripped.substr(separator + 1));
  }

  std::cerr << "[workload_config] loaded " << path << std::endl;
  return values;
}

const config_map& workloadConfigValues() {
  static const config_map values = readWorkloadConfigFile();
  return values;
}

std::string workloadSetting(const char *name) {
  const char *environmentValue = std::getenv(name);
  if (environmentValue != nullptr && *environmentValue != '\0') {
    return environmentValue;
  }

  const config_map& values = workloadConfigValues();
  const config_map::const_iterator it = values.find(name);
  if (it == values.end()) {
    return "";
  }

  return it->second;
}

unsigned int envUnsigned(const char *name, unsigned int fallback) {
  const std::string value = workloadSetting(name);
  if (value.empty()) {
    return fallback;
  }

  char *end = nullptr;
  unsigned long parsed = std::strtoul(value.c_str(), &end, 0);
  if (end == value.c_str()) {
    return fallback;
  }

  return static_cast<unsigned int>(parsed);
}

bool envBool(const char *name, bool fallback) {
  const std::string value = workloadSetting(name);
  if (value.empty()) {
    return fallback;
  }

  if (value == "0" || value == "false" || value == "FALSE" ||
      value == "no" || value == "NO" || value == "off" || value == "OFF") {
    return false;
  }

  return true;
}

traffic_generator::target_pattern envTargetPattern(
    traffic_generator::target_pattern fallback) {
  const std::string value = workloadSetting("LT_TARGET_PATTERN");
  if (value.empty()) {
    return fallback;
  }

  if (value == "target201") {
    return traffic_generator::target_pattern::target201_only;
  }
  if (value == "target202") {
    return traffic_generator::target_pattern::target202_only;
  }
  if (value == "both" || value == "current_default") {
    return traffic_generator::target_pattern::current_default;
  }

  return fallback;
}

const char* traceTargetPatternName(traffic_generator::target_pattern pattern) {
  switch (pattern) {
    case traffic_generator::target_pattern::target201_only:
      return "target201_only";
    case traffic_generator::target_pattern::target202_only:
      return "target202_only";
    case traffic_generator::target_pattern::alternate_201_202:
      return "alternate_201_202";
    case traffic_generator::target_pattern::current_default:
      return "current_default";
  }

  return "unknown";
}

struct workload_settings {
  unsigned int transaction_count;
  unsigned int address_stride;
  traffic_generator::target_pattern target_pattern_mode;
  bool enable_initiator_101;
  bool enable_initiator_102;
};

const workload_settings& getWorkloadSettings() {
  static const workload_settings settings = {
      envUnsigned("LT_BURST_COUNT", 64),
      envUnsigned("LT_ADDRESS_STRIDE", 4),
      envTargetPattern(traffic_generator::target_pattern::current_default),
      envBool("LT_ENABLE_INITIATOR_101", true),
      envBool("LT_ENABLE_INITIATOR_102", true),
  };

  return settings;
}

traffic_generator::workload_config make_workload_config(
    unsigned int initiator_id, sc_core::sc_time initiator_start_offset) {
  const workload_settings& settings = getWorkloadSettings();
  traffic_generator::workload_config config;
  config.transaction_count = settings.transaction_count;
  config.address_stride = settings.address_stride;
  config.target_pattern_mode = settings.target_pattern_mode;
  config.read_write_mode_setting =
      traffic_generator::read_write_mode::write_then_read;
  config.initiator_start_offset = initiator_start_offset;

  if (initiator_id == 101 && !settings.enable_initiator_101) {
    config.transaction_count = 0;
  }
  if (initiator_id == 102 && !settings.enable_initiator_102) {
    config.transaction_count = 0;
  }

  return config;
}
} // namespace

top::top(sc_core::sc_module_name name, const char *address, const char *port)
    : sc_core::sc_module(name), m_bus("m_bus"),
      m_at_and_lt_target_1("m_at_and_lt_target_1", 201, "memory_socket_1",
                           4 * 1024, 4, sc_core::sc_time(20, sc_core::SC_NS),
                           sc_core::sc_time(100, sc_core::SC_NS),
                           sc_core::sc_time(60, sc_core::SC_NS)),
      m_lt_target_2("m_lt_target_2", 202, "memory_socket_2", 4 * 1024, 4,
                    sc_core::sc_time(10, sc_core::SC_NS),
                    sc_core::sc_time(50, sc_core::SC_NS),
                    sc_core::sc_time(30, sc_core::SC_NS)),
      m_initiator_1("m_initiator_1", 101, 0x0000000000000000,
                    0x0000000010000000,
                    make_workload_config(101, sc_core::SC_ZERO_TIME)),
      m_initiator_2("m_initiator_2", 102, 0x0000000000000000,
                    0x0000000010000000,
                    make_workload_config(102, sc_core::SC_ZERO_TIME)),
      m_renode_bridge("m_renode_bridge", address, port) {
  const workload_settings& settings = getWorkloadSettings();
  m_bus.setWorkloadTraceConfig(settings.transaction_count,
                               settings.address_stride,
                               traceTargetPatternName(settings.target_pattern_mode),
                               settings.enable_initiator_101,
                               settings.enable_initiator_102);

  m_initiator_1.top_initiator_socket(m_bus.target_socket[0]);
  m_initiator_2.top_initiator_socket(m_bus.target_socket[1]);

  m_renode_bridge.initiator_socket(m_bus.target_socket[2]);

  m_bus.initiator_socket[0](m_at_and_lt_target_1.m_memory_socket);
  m_bus.initiator_socket[1](m_lt_target_2.m_memory_socket);
}
