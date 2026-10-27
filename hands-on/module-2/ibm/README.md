# IBM Module 2: the lower-level QRMI API

Run one simple Bell-state circuit through two programming interfaces. This module
uses QRMI's task API directly, while [Module 3](../../module-3/ibm/README.md)
uses the Qiskit Primitives interface. [Module 4](../../module-4/ibm/README.md) then
post-processes the samples with MPI. All three modules run on IBM Quantum
hardware, or on the local IBM Quantum System API emulator as a fallback, without changing the circuit.

New participants should first complete the
[IBM Quantum onboarding](../../../onboarding/ibm-quantum-onboarding.md) and the
Module 1 guide for their workload manager: [Slurm](../../module-1/slurm/INSTALL.md),
[OpenPBS](../../module-1/openpbs/INSTALL.md), [LSF](../../module-1/lsf/INSTALL.md)
or [OCS](../../module-1/ocs/INSTALL.md). The
[terminology reference](../../GLOSSARY.md) explains scheduler jobs, quantum tasks,
sessions and shots.

The program and the QRMI calls are the same on every scheduler; only the
commands that open a shell and submit a job differ. Each scheduler has its own
section below, so skip the ones you are not using.
Each module takes about 15 minutes once your cluster and access are set up.
MPI is only needed for Module 4. The same circuit runs on both the local IBM Quantum System API emulator
and IBM Quantum hardware; Qiskit transpiles it for the target backend.

## What the program does

> **In plain terms.** A *qubit* is the basic unit of quantum information. A
> *circuit* is a sequence of gates applied to qubits, followed by a measurement.
> One *shot* is one run of the circuit, and the result *counts* how often each
> bitstring was measured. Here, `00` and `11` mean that both qubits were
> measured in the same state.

The circuit applies a Hadamard (H) gate to the first qubit and then a CNOT gate
from the first qubit to the second. This prepares the Bell state
`(|00> + |11>)/sqrt(2)`. Measuring it gives mostly `00` and `11`, with roughly
equal counts. On hardware, noise also produces a small number of `01` and `10`
results.

Counts fluctuate between runs. Seeing mostly `00` and `11` does not by itself
prove entanglement, since a classical mixture of `00` and `11` would give the
same counts. Verifying entanglement requires measurements in other bases as
well. This exercise demonstrates programming and execution, not entanglement
verification.

## Your user environment

In Modules 2–4 you work as an HPC user: you create your own Python environment
on the cluster's shared volume, `/shared/pyenv`, and your jobs use it. `/shared`
is mounted on every node, so the jobs run with this environment; the job
scripts activate it themselves.

**1. Open your shell.** On the host, give your user a directory for the
environment, then open a shell as that user. Use the block for your scheduler.

OCS (the exercises are already in `~/hands-on`):

```bash
docker exec ocs-master install -d -o ocsuser -g ocsuser /shared/pyenv
docker exec -it -u ocsuser -w /home/ocsuser/hands-on/module-2/ibm ocs-master bash -l
```

Slurm, on the host in `containers/slurm`:

```bash
cp -r ../../hands-on shared/
docker exec login bash -c "install -d /shared/pyenv && chown -R user:user /shared/pyenv"
docker exec -it -u user -w /home/user login bash
```

The `chown -R` hands you the environment if you created it as root for the
mpi4py test in the Slurm container guide; `mpi4py` stays installed.

OpenPBS, on the host in `containers/openpbs`:

```bash
cp -r ../../hands-on shared/
docker exec pbs-server install -d -o pbsuser -g pbsuser /shared/pyenv
docker exec -it -u pbsuser -w /home/pbsuser pbs-server bash -l
```

LSF, on the host in `containers/lsf`:

```bash
cp -r ../../hands-on shared/
docker exec -u root lsf-head install -d -o lsfuser -g lsfuser /shared/pyenv
docker exec -it -u lsfuser -w /home/lsfuser lsf-head bash -l
```

On Slurm, OpenPBS and LSF, copy the exercises into your home directory once,
inside that shell:

```bash
mkdir -p ~/hands-on && cp -r /shared/hands-on/. ~/hands-on/
```

**2. Create the environment** once, inside your shell (on LSF, use `python3`
instead of `python3.12`):

```bash
python3.12 -m venv /shared/pyenv
source /shared/pyenv/bin/activate
pip install "qrmi[ibm]==0.26.4"
```

**Backup for a slow network.** On OCS, if `pip install` fails, use the
environment prepared in the image. On the host:

```bash
docker exec ocs-master bash -c 'rm -rf /shared/pyenv && ln -s /opt/qrmi/venv /shared/pyenv'
```

The Slurm, OpenPBS and LSF images have no prepared environment.

Whenever you open a new shell, run `source /shared/pyenv/bin/activate` again and
set the resource as shown in your scheduler's section.

## The task API

The payload is a Qiskit Sampler input: the transpiled circuit and the number of
shots. Generate it with `gen_sampler_input.py`, then look at it:

```bash
cd ~/hands-on/module-2/ibm

# If you use IBM Quantum hardware
python gen_sampler_input.py <backend_name> https://quantum.cloud.ibm.com/api <your apikey> <your instance, starting with 'crn:v1:'>

# If you use the local IBM Quantum System API emulator
python gen_sampler_input.py fake_brisbane http://qsa-sim:8290 sc26apikey crn:v1:local:sc26 --iam_url http://qsa-sim:8290
```

The script first prints the backend's configuration, which is long. The generated
`sampler_input_{backend_name}.json` is the input QRMI sends to the backend.

Open `qrmi_example.py`. Identify these calls:

```python
resource, = QRMIService().resources()
primitive_input = json.dumps(input_json["parameters"])
program_id = input_json["program_id"]
task = resource.task_start(
    Payload.QiskitPrimitive(input=primitive_input, program_id=program_id)
)
status = resource.task_status(task)
result = resource.task_result(task).value
```

The `QiskitPrimitive` payload format is used by both IBM Quantum Compute Service and IBM Quantum System Service.
The application must not acquire a second session or release the hook's
session: the scheduler's hooks own that lifecycle. The complete pattern is
acquire → `task_start` → `task_status` → `task_result` → release; in a batch job,
the scheduler performs the first and last steps, and the program the steps in
between.

## Submit with your scheduler

Use the section for your scheduler. Each runs the same program: the Python
programs use QRMI's scheduler environment rather than scheduler-specific
variables. Request exactly one quantum resource using the site's existing hooks.

### OCS

Complete [OCS Module 1](../../module-1/ocs/INSTALL.md) with IBM as your provider.

Select the resource:

```bash
cd ~/hands-on/module-2/ibm
QPU=qpu=ibm_kingston
```

`QPU` holds the scheduler's resource request for the commands below. When using
the local IBM Quantum System API emulator, set `QPU=qpu=fake_brisbane` instead.

Submit the task through the scheduler:

```bash
qsub -sync y -l "$QPU" -o low-level.out -e low-level.log \
  ../run_python.ocs qrmi_example.py sampler_input_${QPU#qpu=}.json
cat low-level.log
```

OCS appends to the `-o` and `-e` files, so delete `low-level.out` and
`low-level.log` before re-running, or choose new names.
The log identifies the resource and task; the result is in `low-level.out`.

### Slurm

Complete [Slurm Module 1](../../module-1/slurm/INSTALL.md) with IBM as your provider.

Then, as `user`, with the environment activated:

```bash
cd ~/hands-on/module-2/ibm

# If you use IBM Quantum hardware
sbatch -W --qpu=ibm_kingston --licenses=ibm_kingston@slurmdb:1 -o low-level.log ../run_python.slurm qrmi_example.py sampler_input_ibm_kingston.json

# If you use the local IBM Quantum System API emulator
sbatch -W --qpu=fake_brisbane --licenses=fake_brisbane@slurmdb:1 -o low-level.log ../run_python.slurm qrmi_example.py sampler_input_fake_brisbane.json

cat low-level.log
```

`sbatch -W` waits for the job to finish. The SPANK plugin acquires the resource
before the job starts and releases it when the job ends or is cancelled
(`scancel`); the program uses the session it is given.


### OpenPBS

Complete [OpenPBS Module 1](../../module-1/openpbs/INSTALL.md) with IBM as your provider.

Jobs start in your home directory, so the commands give `run_python.pbs` with an
absolute path; it changes to the directory you submitted from:

```bash
cd ~/hands-on/module-2/ibm

# If you use IBM Quantum hardware
qsub -W block=true -l quantum_resources=ibm_kingston -o $PWD/low-level.out -e $PWD/low-level.log -- \
  $PWD/../run_python.pbs qrmi_example.py sampler_input_ibm_kingston.json

# If you use the local IBM Quantum System API emulator
qsub -W block=true -l quantum_resources=fake_brisbane -o $PWD/low-level.out -e $PWD/low-level.log -- \
  $PWD/../run_python.pbs qrmi_example.py sampler_input_fake_brisbane.json
cat low-level.log low-level.out
```

### LSF

Complete [LSF Module 1](../../module-1/lsf/INSTALL.md) with IBM as your
provider.

```bash
cd ~/hands-on/module-2/ibm

# If you use IBM Quantum hardware
QRMI_QPU_RESOURCES=ibm_kingston bsub -K -oo low-level.log "python qrmi_example.py sampler_input_ibm_kingston.json"

# If you use the local IBM Quantum System API emulator
QRMI_QPU_RESOURCES=fake_brisbane bsub -K -oo low-level.log "python qrmi_example.py sampler_input_fake_brisbane.json"
```

`bsub -K` waits for the job to finish; the job inherits your environment,
including the activated Python environment, and `bsub -K` can return a second
before the `-oo` file is written. `JOB_STARTER` publishes the
resource before the program starts and releases it afterwards. Module 4 gives the LSF commands directly; its helper scripts are for Slurm and OCS.

## The result

On every scheduler the result should look like this (the exact numbers will
differ):

```json
{"counter": {"00": 4637, "11": 4749, "10": 327, "01": 287}}
```

Expect most shots in `00` and `11`, with roughly equal counts; the emulator's
noise model puts a few percent of the shots in `01` and `10` (about 6% above).

The example polls until completion, failure or cancellation. Its five-minute
polling limit cancels a task that takes too long and exits with an error. A failed
task must not be mistaken for a successful empty result.

### Where acquire and release happen

| Stage | Where |
| --- | --- |
| Acquire | Scheduler hook (OCS prolog, Slurm SPANK plugin, OpenPBS hooks, LSF `JOB_STARTER`) |
| Submit, poll, fetch | User application (`qrmi_example.py`) |
| Release | Scheduler hook (OCS epilog, Slurm SPANK plugin, OpenPBS hooks, LSF `JOB_STARTER`) |

**Checkpoint:** Explain which process owns the session, which call returns a
task identifier, and why task completion and resource release are separate steps.

## If something fails

- **Wrong shell or directory:** `docker` commands run on the host; the
  scheduler and exercise Python commands run in your scheduler's shell as your
  user (`user` on Slurm, `pbsuser`, `lsfuser` or `ocsuser`).
  Each module runs in its own directory: `~/hands-on/module-2/ibm`,
  `~/hands-on/module-3/ibm` or `~/hands-on/module-4/ibm`.
- **Old output in `.out` or `.log` files:** OCS appends to `-o` and `-e` files (the LSF commands use `-oo`, which overwrites).
  Delete them or choose new names before re-running.

To stop and resume, use `docker compose ... stop` and `start` with the same `-f`
list you started the cluster with; your files in `/shared` are in
`containers/<your scheduler>/shared` on the host.
