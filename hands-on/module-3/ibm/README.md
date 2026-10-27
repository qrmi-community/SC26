# IBM Module 3: Qiskit's programming model

**What you learn:** how a provider SDK runs on the resource the scheduler
allocated: the programming interface changes, the resource ownership does not,
and you can tell which lines are specific to the provider.

For standard Qiskit workflows, QRMI provides a SamplerV2 primitive implementing BaseSamplerV2.

Open your shell and create the Python environment as described in
[Module 2, Your user environment](../../module-2/ibm/README.md#your-user-environment),
then work in this module's directory:

```bash
cd ~/hands-on/module-3/ibm
source /shared/pyenv/bin/activate
```

Open `bell_sampler.py`. The program:

1. Asks the allocated resource for its backend (`get_backend(resource)`) and
   builds a transpiler target from the backend's configuration and properties.
   The target fixes the rules the circuit must respect, such as the native gate
   set (the instruction set architecture, ISA) and which qubits are connected.
   The program expects the scheduler to have allocated exactly one resource.
2. Builds a two-qubit Bell state circuit: a Hadamard gate on qubit 0, a CNOT
   from qubit 0 to qubit 1, and measurement of all qubits.
3. Transpiles the circuit into an ISA circuit with
   `generate_preset_pass_manager(optimization_level=1, target=target)`, so it
   only uses instructions the QPU supports, and prints the resulting gate counts.
4. Runs `SamplerV2(resource, options={"default_shots": 1024})` on the ISA
   circuit and prints the counts for the `meas` register. For a Bell state,
   expect roughly half `00` and half `11`. If the job fails, the program prints
   the task logs from the resource.

The circuit has no parameters, so `param_values` is an empty array; the
PUB keeps the same shape you would use for a parameterized circuit.

Run only the block for your workload manager. Each uses the local IBM Quantum
System API emulator; for IBM Quantum hardware, use your backend name instead.

Slurm:

```bash
sbatch -W --qpu=fake_brisbane --licenses=fake_brisbane@slurmdb:1 -o sampler.log \
  ../../module-2/run_python.slurm bell_sampler.py
```

OpenPBS:

```bash
qsub -W block=true -l quantum_resources=fake_brisbane -j oe -o $PWD/sampler.log -- \
  $PWD/../../module-2/run_python.pbs bell_sampler.py
```

LSF:

```bash
QRMI_QPU_RESOURCES=fake_brisbane bsub -K -oo sampler.log "python bell_sampler.py"
```

OCS (delete `sampler.log` before re-running, because OCS appends to it):

```bash
qsub -sync y -l qpu=fake_brisbane -o sampler.log -j y \
  ../../module-2/run_python.ocs bell_sampler.py
```

On every scheduler, the log holds the job's output and any QRMI warnings:

```bash
cat sampler.log
```

The log shows the job ID and the counts of the 1,024 shots. Most should be `00`
or `11`, as in [Module 2](../../module-2/ibm/README.md#the-result); the rest
come from the device's noise model.

**Checkpoint:** Which lines of `bell_sampler.py` would change for a real IBM
system? None: the resource configuration selects the system, and the target
fetched from it drives the transpilation. Why does an ideal Bell state never give
`01` or `10`, and where do those counts come from here?

If a job fails, read its `.log` file. For a job that stays queued, `squeue`
(Slurm), `qstat -f <job-id> | grep comment` (OpenPBS), `bjobs -p` (LSF) or
`qalter -w p <job-id>` (OCS) shows why; the resource you request must be
configured.

## Porting a Qiskit Runtime program to QRMI

`bell_sampler_qiskit_original.py` is the same program written for Qiskit Runtime: it
runs on IBM Quantum Platform with your own account, without a workload manager.
`bell_sampler.py` is its port to QRMI. Compare them:

```bash
diff -u bell_sampler_qiskit_original.py bell_sampler.py
```

**Try it:** before reading on, answer these from the diff:

1. Which lines changed, and which parts of the program did not change at all?
2. In the original, who chooses the backend, and where do the credentials come
   from? Who decides both in the QRMI version?
3. Why does the QRMI version expect exactly one resource
   (`(resource,) = QRMIService().resources()`)?

<details>
<summary>Answers</summary>

Only the code that connects to IBM changes:

| Step | Qiskit Runtime (`bell_sampler_qiskit_original.py`) | QRMI (`bell_sampler.py`) |
|------|---------------------------------------------|--------------------------|
| Imports | `QiskitRuntimeService`, `Sampler` from `qiskit_ibm_runtime` | `QRMIService` from `qrmi.primitives`; `SamplerV2`, `get_backend` from `qrmi.primitives.ibm` |
| Select the backend | `service.least_busy(...)`: the program picks a system, with the account saved in your home directory | `QRMIService().resources()`: the scheduler allocated the resource you requested (`--qpu`, `quantum_resources`, ...), with credentials from the administrator's `qrmi_config.json` |
| Transpiler target | `backend.target` | `get_backend(resource).target` |
| Sampler | `SamplerV2(mode=backend, ...)` | `SamplerV2(resource, ...)` |
| Logs on failure | `job.logs()` | `resource.task_logs(job.job_id())` |

The circuit, the transpilation with `generate_preset_pass_manager`, the PUB
passed to `sampler.run()` and the result handling are unchanged. QRMI's
`SamplerV2` implements Qiskit's `BaseSamplerV2` interface, so code written
against the Sampler primitive keeps working.

The main change is who owns the decision. In the original, the program chooses
where to run and uses your account. With QRMI, the workload manager allocates
the resource before the program starts, and the program uses the one it is
given. This is why the same `bell_sampler.py` runs on the emulator and on
hardware without changes, and why the scheduler can account for and limit
access to the QPU like any other resource.

</details>

To port your own Qiskit Runtime program, change these five places and leave
the rest as it is.

For troubleshooting, see [Module 2](../../module-2/ibm/README.md#if-something-fails).
