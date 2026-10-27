"""Sample a ten-atom chain with Pulser and write one uint32 per shot to input.bin for MPI."""

import argparse
from collections import Counter

import numpy as np
from pulser import Pulse, QPUBackend, Register, Sequence
from pulser.devices import Device, DigitalAnalogDevice
from pulser.waveforms import InterpolatedWaveform
from qrmi.pulser import PulserQRMIConnection


def chain_sequence(device: Device) -> Sequence:
    """Build a detuning sweep that favors alternating excitations along a ten-atom chain.

Args:
    device (Device): Device whose rules the sequence must respect.

Returns:
    (Sequence): Measured Pulser sequence on the device.
"""
    # Neighbors 6 micrometers apart block each other's excitation.
    register = Register({f"q{i}": (6 * (i - 4.5), 0) for i in range(10)})
    sequence = Sequence(register.with_automatic_layout(device), device)
    sequence.declare_channel("rydberg", "rydberg_global")
    # Over 4 us, ramp the amplitude up and down while sweeping the detuning from
    # negative (atoms stay in the ground state) to positive (excitation is favored).
    times = [0, 0.2, 0.8, 1]
    amplitude = InterpolatedWaveform(4000, [0, 4, 4, 0], times=times)
    detuning = InterpolatedWaveform(4000, [-10, -10, 10, 10], times=times)
    sequence.add(Pulse(amplitude, detuning, 0), "rydberg")
    sequence.measure("ground-rydberg")
    return sequence


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--simulate", action="store_true", help="simulate on the CPU instead of using QRMI")
    parser.add_argument("--runs", type=int, default=500, help="number of shots (at most 500 on Pasqal's QPUs)")
    args = parser.parse_args()

    if args.simulate:
        # Imported here: pulser-simulation is an optional package.
        from pulser_simulation import QutipBackendV2

        results = QutipBackendV2(chain_sequence(DigitalAnalogDevice)).run()
        counts = dict(results.final_state.sample(num_shots=args.runs))
    else:
        # Scheduler hooks own acquisition and release; this connection uses their session.
        connection = PulserQRMIConnection()
        device = list(connection.fetch_available_devices().values())[0]
        backend = QPUBackend(chain_sequence(device), connection)
        remote = backend.run(job_params=[{"runs": args.runs}], wait=True)
        result, = remote.get_available_results().values()
        counts = result.final_bitstrings

    print("Most common:", Counter(counts).most_common(3))
    # Expand the histogram into one sample per shot, each bitstring as an integer.
    samples = np.repeat([int(bitstring, 2) for bitstring in counts], list(counts.values())).astype(np.uint32)
    samples.tofile("input.bin")
    print(f"Wrote {len(samples)} samples to input.bin")
