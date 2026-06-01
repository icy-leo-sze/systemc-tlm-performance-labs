// SPDX-License-Identifier: Apache-2.0

#ifndef EXAMPLES_AT_SYSTEMC_INCLUDE_AT_LAB_H_
#define EXAMPLES_AT_SYSTEMC_INCLUDE_AT_LAB_H_

#include <cstdint>
#include <fstream>
#include <string>

#include "systemc"
#include "tlm.h"
#include "tlm_utils/peq_with_cb_and_phase.h"
#include "tlm_utils/simple_initiator_socket.h"
#include "tlm_utils/simple_target_socket.h"

namespace at_lab {

class TxnIdExtension : public tlm::tlm_extension<TxnIdExtension> {
public:
    explicit TxnIdExtension(unsigned int id = 0);

    tlm::tlm_extension_base *clone() const override;
    void copy_from(const tlm::tlm_extension_base &extension) override;

    unsigned int id;
};

class PhaseTrace {
public:
    explicit PhaseTrace(const std::string &path);
    ~PhaseTrace();

    void log(const char *component, const char *direction,
             const tlm::tlm_generic_payload &trans,
             const tlm::tlm_phase &phase,
             const sc_core::sc_time &delay);

private:
    std::ofstream out_;
};

class Initiator : public sc_core::sc_module {
public:
    tlm_utils::simple_initiator_socket<Initiator> socket;

    explicit Initiator(sc_core::sc_module_name name);

private:
    void run();
    void send_transaction(tlm::tlm_command command, std::uint64_t address,
                          std::uint32_t &data, unsigned int txn_id);
    tlm::tlm_sync_enum nb_transport_bw(tlm::tlm_generic_payload &trans,
                                       tlm::tlm_phase &phase,
                                       sc_core::sc_time &delay);
    void handle_bw_phase(tlm::tlm_generic_payload &trans,
                         const tlm::tlm_phase &phase);
    void check_response(const tlm::tlm_generic_payload &trans) const;

    tlm_utils::peq_with_cb_and_phase<Initiator> peq_;
    sc_core::sc_event response_done_;
    tlm::tlm_generic_payload *request_in_progress_;
    bool response_seen_;

    SC_HAS_PROCESS(Initiator);
};

class SimpleAtBus : public sc_core::sc_module {
public:
    tlm_utils::simple_target_socket<SimpleAtBus> upstream_socket;
    tlm_utils::simple_initiator_socket<SimpleAtBus> downstream_socket;

    SimpleAtBus(sc_core::sc_module_name name, PhaseTrace &trace);

private:
    tlm::tlm_sync_enum nb_transport_fw(tlm::tlm_generic_payload &trans,
                                       tlm::tlm_phase &phase,
                                       sc_core::sc_time &delay);
    tlm::tlm_sync_enum nb_transport_bw(tlm::tlm_generic_payload &trans,
                                       tlm::tlm_phase &phase,
                                       sc_core::sc_time &delay);

    PhaseTrace &trace_;
};

class Target : public sc_core::sc_module {
public:
    tlm_utils::simple_target_socket<Target> socket;

    explicit Target(sc_core::sc_module_name name);

private:
    tlm::tlm_sync_enum nb_transport_fw(tlm::tlm_generic_payload &trans,
                                       tlm::tlm_phase &phase,
                                       sc_core::sc_time &delay);
    void process_requests();
    void execute(tlm::tlm_generic_payload &trans);

    sc_core::sc_event request_event_;
    sc_core::sc_event end_response_event_;
    tlm::tlm_generic_payload *pending_request_;
    tlm::tlm_generic_payload *response_in_progress_;
    std::uint32_t word_;

    SC_HAS_PROCESS(Target);
};

class Top : public sc_core::sc_module {
public:
    Top(sc_core::sc_module_name name, PhaseTrace &trace);

private:
    Initiator initiator_;
    SimpleAtBus bus_;
    Target target_;
};

}  // namespace at_lab

#endif  // EXAMPLES_AT_SYSTEMC_INCLUDE_AT_LAB_H_
