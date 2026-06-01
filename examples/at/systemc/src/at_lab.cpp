// SPDX-License-Identifier: Apache-2.0

#include "at_lab.h"

#include <cstring>
#include <iomanip>
#include <sstream>

namespace at_lab {
namespace {

const char *phase_name(const tlm::tlm_phase &phase)
{
    if (phase == tlm::BEGIN_REQ) {
        return "BEGIN_REQ";
    }
    if (phase == tlm::END_REQ) {
        return "END_REQ";
    }
    if (phase == tlm::BEGIN_RESP) {
        return "BEGIN_RESP";
    }
    if (phase == tlm::END_RESP) {
        return "END_RESP";
    }
    return phase.get_name();
}

const char *command_name(tlm::tlm_command command)
{
    switch (command) {
    case tlm::TLM_READ_COMMAND:
        return "READ";
    case tlm::TLM_WRITE_COMMAND:
        return "WRITE";
    case tlm::TLM_IGNORE_COMMAND:
        return "IGNORE";
    }

    return "UNKNOWN";
}

std::string hex_value(std::uint64_t value, int width)
{
    std::ostringstream out;
    out << "0x" << std::hex << std::nouppercase << std::setw(width)
        << std::setfill('0') << value;
    return out.str();
}

std::uint32_t payload_word(const tlm::tlm_generic_payload &trans)
{
    std::uint32_t value = 0;
    const unsigned char *data = trans.get_data_ptr();

    if (data != nullptr && trans.get_data_length() >= sizeof(value)) {
        std::memcpy(&value, data, sizeof(value));
    }

    return value;
}

unsigned int txn_id(const tlm::tlm_generic_payload &trans)
{
    TxnIdExtension *extension = nullptr;
    trans.get_extension(extension);

    if (extension == nullptr) {
        return 0;
    }

    return extension->id;
}

}  // namespace

TxnIdExtension::TxnIdExtension(unsigned int id)
    : id(id)
{
}

tlm::tlm_extension_base *TxnIdExtension::clone() const
{
    return new TxnIdExtension(id);
}

void TxnIdExtension::copy_from(const tlm::tlm_extension_base &extension)
{
    id = static_cast<const TxnIdExtension &>(extension).id;
}

PhaseTrace::PhaseTrace(const std::string &path)
    : out_(path)
{
    if (!out_) {
        SC_REPORT_FATAL("at_lab", "failed to open phase_trace.csv");
    }

    out_ << "txn_id,component,direction,phase,command,address,data,time_ns,delay_ns,response_status\n";
}

PhaseTrace::~PhaseTrace()
{
    out_.flush();
}

void PhaseTrace::log(const char *component, const char *direction,
                     const tlm::tlm_generic_payload &trans,
                     const tlm::tlm_phase &phase,
                     const sc_core::sc_time &delay)
{
    out_ << txn_id(trans) << ','
         << component << ','
         << direction << ','
         << phase_name(phase) << ','
         << command_name(trans.get_command()) << ','
         << hex_value(trans.get_address(), 16) << ','
         << hex_value(payload_word(trans), 8) << ','
         << std::fixed << std::setprecision(3)
         << sc_core::sc_time_stamp().to_seconds() * 1e9 << ','
         << delay.to_seconds() * 1e9 << ','
         << trans.get_response_string() << '\n';
}

Initiator::Initiator(sc_core::sc_module_name name)
    : sc_core::sc_module(name)
    , socket("socket")
    , peq_(this, &Initiator::handle_bw_phase)
    , request_in_progress_(nullptr)
    , response_seen_(false)
{
    socket.register_nb_transport_bw(this, &Initiator::nb_transport_bw);
    SC_THREAD(run);
}

void Initiator::run()
{
    wait(sc_core::SC_ZERO_TIME);

    std::uint32_t write_data = 0x1234abcd;
    send_transaction(tlm::TLM_WRITE_COMMAND, 0x0, write_data, 1);

    std::uint32_t read_data = 0;
    send_transaction(tlm::TLM_READ_COMMAND, 0x0, read_data, 2);

    if (read_data != write_data) {
        SC_REPORT_FATAL("at_lab", "READ did not return the value written by WRITE");
    }

    sc_core::sc_stop();
}

void Initiator::send_transaction(tlm::tlm_command command, std::uint64_t address,
                                 std::uint32_t &data, unsigned int txn_id)
{
    tlm::tlm_generic_payload trans;
    TxnIdExtension txn_id_extension(txn_id);

    trans.set_extension(&txn_id_extension);
    trans.set_command(command);
    trans.set_address(address);
    trans.set_data_ptr(reinterpret_cast<unsigned char *>(&data));
    trans.set_data_length(sizeof(data));
    trans.set_streaming_width(sizeof(data));
    trans.set_byte_enable_ptr(nullptr);
    trans.set_byte_enable_length(0);
    trans.set_dmi_allowed(false);
    trans.set_response_status(tlm::TLM_INCOMPLETE_RESPONSE);

    tlm::tlm_phase phase = tlm::BEGIN_REQ;
    sc_core::sc_time delay = sc_core::SC_ZERO_TIME;

    request_in_progress_ = &trans;
    response_seen_ = false;

    tlm::tlm_sync_enum status = socket->nb_transport_fw(trans, phase, delay);
    if (status == tlm::TLM_UPDATED) {
        peq_.notify(trans, phase, delay);
    } else if (status == tlm::TLM_COMPLETED) {
        request_in_progress_ = nullptr;
        response_seen_ = true;
        check_response(trans);
    }

    if (!response_seen_) {
        wait(response_done_);
    }

    trans.clear_extension<TxnIdExtension>();
}

tlm::tlm_sync_enum Initiator::nb_transport_bw(tlm::tlm_generic_payload &trans,
                                              tlm::tlm_phase &phase,
                                              sc_core::sc_time &delay)
{
    peq_.notify(trans, phase, delay);
    return tlm::TLM_ACCEPTED;
}

void Initiator::handle_bw_phase(tlm::tlm_generic_payload &trans,
                                const tlm::tlm_phase &phase)
{
    if (phase == tlm::END_REQ) {
        if (&trans == request_in_progress_) {
            request_in_progress_ = nullptr;
        }
        return;
    }

    if (phase != tlm::BEGIN_RESP) {
        SC_REPORT_FATAL("at_lab", "initiator received an unexpected AT phase");
    }

    if (&trans == request_in_progress_) {
        request_in_progress_ = nullptr;
    }

    check_response(trans);

    tlm::tlm_phase end_phase = tlm::END_RESP;
    sc_core::sc_time delay = sc_core::SC_ZERO_TIME;
    socket->nb_transport_fw(trans, end_phase, delay);

    response_seen_ = true;
    response_done_.notify(sc_core::SC_ZERO_TIME);
}

void Initiator::check_response(const tlm::tlm_generic_payload &trans) const
{
    if (trans.is_response_error()) {
        SC_REPORT_FATAL("at_lab", trans.get_response_string().c_str());
    }
}

SimpleAtBus::SimpleAtBus(sc_core::sc_module_name name, PhaseTrace &trace)
    : sc_core::sc_module(name)
    , upstream_socket("upstream_socket")
    , downstream_socket("downstream_socket")
    , trace_(trace)
{
    upstream_socket.register_nb_transport_fw(this, &SimpleAtBus::nb_transport_fw);
    downstream_socket.register_nb_transport_bw(this, &SimpleAtBus::nb_transport_bw);
}

tlm::tlm_sync_enum SimpleAtBus::nb_transport_fw(tlm::tlm_generic_payload &trans,
                                                tlm::tlm_phase &phase,
                                                sc_core::sc_time &delay)
{
    trace_.log("bus", "FW", trans, phase, delay);
    return downstream_socket->nb_transport_fw(trans, phase, delay);
}

tlm::tlm_sync_enum SimpleAtBus::nb_transport_bw(tlm::tlm_generic_payload &trans,
                                                tlm::tlm_phase &phase,
                                                sc_core::sc_time &delay)
{
    trace_.log("bus", "BW", trans, phase, delay);
    return upstream_socket->nb_transport_bw(trans, phase, delay);
}

Target::Target(sc_core::sc_module_name name)
    : sc_core::sc_module(name)
    , socket("socket")
    , pending_request_(nullptr)
    , response_in_progress_(nullptr)
    , word_(0)
{
    socket.register_nb_transport_fw(this, &Target::nb_transport_fw);
    SC_THREAD(process_requests);
}

tlm::tlm_sync_enum Target::nb_transport_fw(tlm::tlm_generic_payload &trans,
                                           tlm::tlm_phase &phase,
                                           sc_core::sc_time &delay)
{
    if (phase == tlm::BEGIN_REQ) {
        if (pending_request_ != nullptr) {
            trans.set_response_status(tlm::TLM_GENERIC_ERROR_RESPONSE);
            return tlm::TLM_COMPLETED;
        }

        pending_request_ = &trans;
        request_event_.notify(delay);
        return tlm::TLM_ACCEPTED;
    }

    if (phase == tlm::END_RESP) {
        if (response_in_progress_ != &trans) {
            SC_REPORT_FATAL("at_lab", "target received END_RESP for an unknown transaction");
        }

        response_in_progress_ = nullptr;
        pending_request_ = nullptr;
        end_response_event_.notify(delay);
        return tlm::TLM_ACCEPTED;
    }

    SC_REPORT_FATAL("at_lab", "target received an unexpected AT phase");
    return tlm::TLM_ACCEPTED;
}

void Target::process_requests()
{
    while (true) {
        wait(request_event_);
        tlm::tlm_generic_payload *trans = pending_request_;

        wait(sc_core::sc_time(1, sc_core::SC_NS));
        tlm::tlm_phase phase = tlm::END_REQ;
        sc_core::sc_time delay = sc_core::SC_ZERO_TIME;
        socket->nb_transport_bw(*trans, phase, delay);

        wait(sc_core::sc_time(4, sc_core::SC_NS));
        execute(*trans);

        response_in_progress_ = trans;
        phase = tlm::BEGIN_RESP;
        delay = sc_core::SC_ZERO_TIME;
        socket->nb_transport_bw(*trans, phase, delay);

        wait(end_response_event_);
    }
}

void Target::execute(tlm::tlm_generic_payload &trans)
{
    if (trans.get_address() != 0 || trans.get_data_length() != sizeof(word_) ||
        trans.get_byte_enable_ptr() != nullptr ||
        trans.get_streaming_width() < sizeof(word_)) {
        trans.set_response_status(tlm::TLM_GENERIC_ERROR_RESPONSE);
        return;
    }

    if (trans.is_write()) {
        std::memcpy(&word_, trans.get_data_ptr(), sizeof(word_));
    } else if (trans.is_read()) {
        std::memcpy(trans.get_data_ptr(), &word_, sizeof(word_));
    } else {
        trans.set_response_status(tlm::TLM_COMMAND_ERROR_RESPONSE);
        return;
    }

    trans.set_response_status(tlm::TLM_OK_RESPONSE);
}

Top::Top(sc_core::sc_module_name name, PhaseTrace &trace)
    : sc_core::sc_module(name)
    , initiator_("initiator")
    , bus_("bus", trace)
    , target_("target")
{
    initiator_.socket.bind(bus_.upstream_socket);
    bus_.downstream_socket.bind(target_.socket);
}

}  // namespace at_lab
