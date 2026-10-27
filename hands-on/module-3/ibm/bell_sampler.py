"""Sample a Bell state with Qiskit on the IBM resource allocated by the scheduler."""

# pylint: disable=import-outside-toplevel, no-name-in-module

import numpy as np
from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qrmi.primitives import QRMIService
from qrmi.primitives.ibm import SamplerV2, get_backend

# Create QRMI
(resource,) = QRMIService().resources()

# Generate transpiler target from backend configuration & properties
target = get_backend(resource).target

# Build a Bell state circuit
qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()
print(qc.draw("text"))

param_values = np.random.rand(qc.num_parameters)

# The circuit needs to be transformed to only use instructions supported by
# the QPU (referred to as an instruction set architecture (ISA) circuit).
pm = generate_preset_pass_manager(
    optimization_level=1,
    target=target,
)
isa_circuit = pm.run(qc)
print(f"\nTranspiled gate counts: {isa_circuit.count_ops()}")

# Initialize QRMI Sampler
sampler = SamplerV2(resource, options={"default_shots": 1024})

# Next, invoke the run() method to generate the output. The circuit and optional
# parameter value sets are input as primitive unified bloc (PUB) tuples.
job = sampler.run([(isa_circuit, param_values)])
print(f"Job ID: {job.job_id()} | Status: {job.status()}")
try:
    result = job.result()

    # Get results for the first (and only) PUB
    pub_result = result[0]
    print(f"Counts for the 'meas' output register: {pub_result.data.meas.get_counts()}")
except RuntimeError as err:
    print(err)

if job.errored():
    print(resource.task_logs(job.job_id()))
