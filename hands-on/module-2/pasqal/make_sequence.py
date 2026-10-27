"""Build the two-atom Pulser sequence and save it as JSON for qrmi_example.py.

This only uses Pulser: no QRMI, scheduler, network or credentials.
"""

import math

from pulser import Pulse, Register, Sequence
from pulser.devices import DigitalAnalogDevice

# Two atoms 5 micrometers apart, inside the Rydberg blockade radius.
device = DigitalAnalogDevice  # Pulser's example device; emulators accept it
register = Register({"q0": (-2.5, 0), "q1": (2.5, 0)})
sequence = Sequence(register.with_automatic_layout(device), device)
sequence.declare_channel("rydberg", "rydberg_global")

# A pi pulse at Rabi frequency omega (rad/us). Under the blockade the pair oscillates
# sqrt(2) times faster; durations are in ns, in multiples of 4 ns.
omega = math.pi
pi_pulse_ns = round(1000 * math.pi / (math.sqrt(2) * omega) / 4) * 4
sequence.add(Pulse.ConstantPulse(pi_pulse_ns, omega, 0, 0), "rydberg")
sequence.measure("ground-rydberg")

with open("bell.json", "w", encoding="utf-8") as f:
    f.write(sequence.to_abstract_repr())
print(f"Wrote bell.json: two atoms, one {pi_pulse_ns} ns pulse")
