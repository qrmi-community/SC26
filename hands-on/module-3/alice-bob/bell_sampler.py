# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright 2026 Alice and Bob. All Rights Reserved.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Sample a cat-qubit Bell state with Qiskit, locally or on the Felis resource allocated by the scheduler."""

import argparse
import json
import sys

from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler
from qiskit.transpiler import generate_preset_pass_manager
from qrmi import EnvVarNotSetError, QRMIService, QuantumResource

from felis_primitives import SamplerV2, get_backend


def bell_circuit() -> QuantumCircuit:
    """Build a two-qubit circuit that prepares (|00> + |11>)/sqrt(2), the cat-qubit way.

Returns:
    (QuantumCircuit): Circuit measured into the "meas" register.
"""
    circuit = QuantumCircuit(2)
    # Cat qubits prepare |+> natively: this replaces the textbook Hadamard on |0>,
    # and runs on the physical-cat emulators, which have no Hadamard gate.
    circuit.initialize("+", 0)
    circuit.cx(0, 1)
    circuit.measure_all()
    return circuit


def scheduler_resource() -> QuantumResource:
    """Return the single quantum resource allocated to this scheduler job.

Returns:
    (QuantumResource): Resource named by the job's QRMI_JOB_QPU_RESOURCES.
"""
    # Scheduler hooks own acquisition and release; QRMIService reads the job's QPU environment.
    try:
        resources = QRMIService().resources()
    except EnvVarNotSetError:
        raise SystemExit("no quantum resource is allocated to this process; submit it with sbatch --qpu=...") from None
    if not resources:
        raise SystemExit("the quantum resource allocated to this job is not online")
    resource, = resources
    return resource


def transpile_for(backend, circuit: QuantumCircuit) -> QuantumCircuit:
    """Map a circuit onto the gates the resource's target supports.

Args:
    backend: Backend describing the target, from get_backend(resource).
    circuit (QuantumCircuit): Circuit to transpile.

Returns:
    (QuantumCircuit): Circuit ready to run on the resource.
"""
    pass_manager = generate_preset_pass_manager(optimization_level=1, backend=backend)
    return pass_manager.run(circuit)


def simulate(shots: int) -> dict[str, int]:
    """Sample the Bell circuit on the local CPU without QRMI or credentials.

Args:
    shots (int): Number of shots.

Returns:
    (dict[str, int]): Count for each measured bitstring.
"""
    result = StatevectorSampler().run([bell_circuit()], shots=shots).result()
    return result[0].data.meas.get_counts()


def run_sampler(resource: QuantumResource, shots: int, photons: float, poll_interval: float = 1.0) -> dict[str, int]:
    """Transpile the Bell circuit for the resource and run it through the Felis SamplerV2.

Args:
    resource (QuantumResource): Allocated Alice & Bob Felis resource.
    shots (int): Number of shots.
    photons (float): Average number of photons per cat qubit, the emulator's averageNbPhotons.
    poll_interval (float): Seconds between task status checks.

Returns:
    (dict[str, int]): Count for each measured bitstring.
"""
    isa_circuit = transpile_for(get_backend(resource), bell_circuit())
    print(f"Transpiled circuit ops: {dict(isa_circuit.count_ops())}", file=sys.stderr, flush=True)
    sampler = SamplerV2(resource, options={"input_params": {"averageNbPhotons": photons},
                                           "poll_interval": poll_interval})
    job = sampler.run([isa_circuit], shots=shots)
    print(f"Resource: {resource.resource_id()}; task: {job.job_id()}", file=sys.stderr, flush=True)
    return job.result()[0].data.meas.get_counts()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["sampler", "simulate"], default="sampler")
    parser.add_argument("--shots", type=int, default=1000)
    parser.add_argument("--photons", type=float, default=4,
                        help="average number of photons per cat qubit, at least 4 (default: %(default)s)")
    parser.add_argument("--output", type=argparse.FileType("w"), default=sys.stdout)
    args = parser.parse_args(argv)
    if args.mode == "simulate":
        counts = simulate(args.shots)
    else:
        counts = run_sampler(scheduler_resource(), args.shots, args.photons)
    print(json.dumps({"counter": counts}), file=args.output)
    args.output.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
