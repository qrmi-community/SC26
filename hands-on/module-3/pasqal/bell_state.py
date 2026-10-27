"""Prepare a two-atom state with Pulser and run it through QRMI, or simulate it on the CPU."""

import argparse
import json
import math
import sys

from pulser import Pulse, QPUBackend, Register, Sequence
from pulser.devices import Device, DigitalAnalogDevice
from qrmi.pulser import PulserQRMIConnection


def bell_sequence(device: Device, distance: float) -> Sequence:
    """Build a two-atom pulse that prepares (|gr> + |rg>)/sqrt(2) under the Rydberg blockade.

Args:
    device (Device): Device whose rules the sequence must respect.
    distance (float): Distance between the two atoms in micrometers.

Returns:
    (Sequence): Measured Pulser sequence on the device.
"""
    register = Register({"q0": (-distance / 2, 0), "q1": (distance / 2, 0)})
    sequence = Sequence(register.with_automatic_layout(device), device)
    sequence.declare_channel("rydberg", "rydberg_global")
    # A pi pulse at Rabi frequency omega (rad/us). Under the blockade the pair oscillates
    # sqrt(2) times faster; durations are in ns, in multiples of 4 ns.
    omega = math.pi
    radius = device.rydberg_blockade_radius(omega)
    print(f"Atoms {distance:g} um apart; blockade radius on {device.name}: {radius:.1f} um", file=sys.stderr)
    pi_pulse_ns = round(1000 * math.pi / (math.sqrt(2) * omega) / 4) * 4
    sequence.add(Pulse.ConstantPulse(pi_pulse_ns, omega, 0, 0), "rydberg")
    sequence.measure("ground-rydberg")
    return sequence


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--simulate", action="store_true", help="simulate on the CPU instead of using QRMI")
    parser.add_argument("--runs", type=int, default=500, help="number of shots (at most 500 on Pasqal's QPUs)")
    parser.add_argument("--distance", type=float, default=5.0, help="distance between the atoms in um")
    parser.add_argument("--output", type=argparse.FileType("w"), default=sys.stdout)
    args = parser.parse_args()

    if args.simulate:
        # Imported here: pulser-simulation is an optional package.
        from pulser_simulation import QutipBackendV2

        results = QutipBackendV2(bell_sequence(DigitalAnalogDevice, args.distance)).run()
        counts = dict(results.final_state.sample(num_shots=args.runs))
    else:
        # Scheduler hooks own acquisition and release; this connection uses their session.
        connection = PulserQRMIConnection()
        # Build for the device the resource reports (Pasqal Cloud: its QPU's specs,
        # also for emulators), so the same program would run on hardware.
        device = list(connection.fetch_available_devices().values())[0]
        backend = QPUBackend(bell_sequence(device, args.distance), connection)
        remote = backend.run(job_params=[{"runs": args.runs}], wait=True)
        result, = remote.get_available_results().values()
        counts = result.final_bitstrings
    print(json.dumps({"counter": counts}), file=args.output)
