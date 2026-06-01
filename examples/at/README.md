# Minimal AT smoke lab

This directory is a small, original TLM-2.0 approximately-timed smoke lab. The local
`references/doulos_at_example/` tree was used only as a protocol-shape reference:
it is not redistributed here, and this example does not copy Doulos source blocks.

`examples/lt` remains the stable loosely-timed performance workflow baseline.
This `examples/at` lab is the first step on a future AT timing refinement path.
It is not a cycle-accurate model, and it is not a real AXI, CHI, or NoC timing
model. Its only goal is to validate the TLM-2.0 AT four-phase flow and produce a
phase trace that makes that flow visible.

The lab contains:

- one initiator
- one pass-through AT bus
- one target
- one WRITE followed by one READ
- CSV tracing of the four base-protocol phases

The target stores a single 32-bit word at address `0x0`. The initiator writes
`0x1234abcd` with transaction id 1, reads the word back with transaction id 2,
sends `END_RESP`, and stops the simulation.

## Phase Flow

For each transaction:

1. Initiator sends `BEGIN_REQ` on the forward path.
2. Bus forwards `BEGIN_REQ` to the target.
3. Target accepts the request and sends `END_REQ` on the backward path.
4. Target executes the command and sends `BEGIN_RESP` on the backward path.
5. Initiator checks the response and sends `END_RESP` on the forward path.

The bus writes these transitions to `phase_trace.csv`.

## Build and Run

From the repository root:

```bash
cmake -S examples/at -B build/examples/at \
  -DUSER_SYSTEMC_LIB_DIR=<absolute path to SystemC lib> \
  -DUSER_SYSTEMC_INCLUDE_DIR=<absolute path to SystemC include>
cmake --build build/examples/at
./build/examples/at/at
```

If SystemC is installed in a standard search path, the two `USER_SYSTEMC_*`
arguments may be omitted.

To build against the bundled SystemC source tree instead:

```bash
cmake -S systemc -B build/systemc \
  -DCMAKE_CXX_STANDARD=17 \
  -DCMAKE_POLICY_VERSION_MINIMUM=3.5
cmake --build build/systemc --target systemc
cmake -S examples/at -B build/examples/at \
  -DUSER_SYSTEMC_LIB_DIR="$PWD/build/systemc/src" \
  -DUSER_SYSTEMC_INCLUDE_DIR="$PWD/systemc/src"
cmake --build build/examples/at
./build/examples/at/at
```

The trace is written to the current working directory of the `at` executable.
When using the commands above, that is the repository root.

## Expected Trace Shape

```csv
txn_id,component,direction,phase,command,address,data,time_ns,delay_ns,response_status
1,bus,FW,BEGIN_REQ,WRITE,0x0000000000000000,0x1234abcd,0.000,0.000,TLM_INCOMPLETE_RESPONSE
1,bus,BW,END_REQ,WRITE,0x0000000000000000,0x1234abcd,1.000,0.000,TLM_INCOMPLETE_RESPONSE
1,bus,BW,BEGIN_RESP,WRITE,0x0000000000000000,0x1234abcd,5.000,0.000,TLM_OK_RESPONSE
1,bus,FW,END_RESP,WRITE,0x0000000000000000,0x1234abcd,5.000,0.000,TLM_OK_RESPONSE
2,bus,FW,BEGIN_REQ,READ,0x0000000000000000,0x00000000,5.000,0.000,TLM_INCOMPLETE_RESPONSE
2,bus,BW,END_REQ,READ,0x0000000000000000,0x00000000,6.000,0.000,TLM_INCOMPLETE_RESPONSE
2,bus,BW,BEGIN_RESP,READ,0x0000000000000000,0x1234abcd,10.000,0.000,TLM_OK_RESPONSE
2,bus,FW,END_RESP,READ,0x0000000000000000,0x1234abcd,10.000,0.000,TLM_OK_RESPONSE
```
