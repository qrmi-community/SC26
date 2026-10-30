# IBM Module 4: MPI post-processing (optional)

**What you learn:** quantum work integrates with the standard HPC libraries
you already use. Here the results of a quantum job go to an ordinary MPI
program, compiled with `mpicxx` and started by your workload manager like any
other MPI job.

This is the stretch goal: do it if you finish Modules 1–3 early, or after the
break. A quantum sampling job writes its samples; a classical MPI job then
processes them on both compute nodes. Nothing in the MPI program knows about
QRMI or the quantum resource.

Sample a two-qubit Bell state, then count the samples across four MPI ranks
on the two execution nodes. Only the sampling job requests a quantum resource.

There are two ways to combine a quantum job with an MPI job. In pattern A,
you submit two jobs: a quantum job that only samples, then an MPI job that
starts only after the sampling job succeeded. In pattern B, you submit one
parallel job: MPI rank 0 runs the quantum task itself, and the other ranks
wait for its result. This module uses pattern A, because it keeps the quantum
resource allocated only while sampling and does not keep MPI ranks idle while
the quantum task runs.

Slurm starts the MPI job after successful sampling with an `afterok`
dependency; the OCS helper waits for successful sampling before submitting the
MPI job. On OpenPBS and LSF, confirm that sampling succeeded before continuing
with the MPI commands.

Open your shell as described in
[Module 2](../../module-2/ibm/README.md#your-user-environment). In a new shell,
activate the environment first:

```bash
source /shared/pyenv/bin/activate
cd ~/hands-on/module-4/ibm
```

## The sampling program

Open `bell_sampler.py`. The program:

1. Asks the allocated resource for its backend (`get_backend(resource)`) and
   builds a transpiler target from the backend's configuration and properties.
   The target fixes the rules the circuit must respect, such as the native gate
   set and which qubits are connected. The program expects the scheduler to
   have allocated exactly one resource.
2. Builds a two-qubit Bell state circuit: a Hadamard gate on qubit 0, a CNOT
   from qubit 0 to qubit 1, and measurement of all qubits.
3. Transpiles the circuit into an instruction set architecture (ISA) circuit
   with `generate_preset_pass_manager(optimization_level=1, target=target)`,
   so it only uses instructions the QPU supports.
4. Runs `SamplerV2(resource, options={"default_shots": 1024})`, converts each
   measured bitstring to one native `uint32`, and writes the 1,024 values to
   `input.bin`. If the job fails, the program prints the task logs from the
   resource, writes no `input.bin`, and exits with status 1, so that the
   workload manager marks the sampling job as failed.

The circuit has no parameters, so `param_values` is an empty array; the PUB
keeps the same shape you would use for a parameterized circuit.

## Run it

Run only the block for your workload manager below. The steps are the same on
every scheduler: compile the MPI program, run the sampling job on the quantum
resource (`input.bin`), then run the MPI job with four ranks on the two compute
nodes. The MPI job needs no quantum resource. `MPI_Scatter` divides the samples
evenly among the ranks, and `MPI_Reduce` adds the local histograms. JSON output
keys are decimal encodings of the measured bitstrings: Qiskit writes qubit 0 as
the rightmost bit, so `00` is `0` and `11` is `3`.

The sampler already returns counts. `bell_sampler.py` writes the individual
shots instead, so that MPI has samples to count and the result is easy to
check. The point is the integration with MPI, not a speedup: in a real
workflow, this is where your own MPI code (post-processing, a classical
optimizer, a simulation) takes the quantum results.

Slurm: `run.sh` submits both jobs. The MPI job starts only after the sampling
job succeeded (`--dependency=afterok`); `run.sh` returns when it ends, and fails
if sampling failed. The jobs write `sampling.log` and `get_counts.log`:

```bash
QPU=fake_brisbane
REQ="--qpu=$QPU --licenses=${QPU,,}@slurmdb:1"
bash run.sh $REQ
```

The options you pass override the `#SBATCH` lines in `run_sampler.sh`, which
default to `fake_brisbane`.

OpenPBS:

```bash
Q=fake_brisbane
qsub -W block=true -l quantum_resources=$Q -o $PWD/sampling.out -e $PWD/sampling.log <<END
cd $PWD
source /shared/pyenv/bin/activate
python bell_sampler.py
END
mpicxx -O2 -o get_counts get_counts.cpp
qsub -W block=true -l select=2:ncpus=2:mpiprocs=2 -l place=scatter -o $PWD/get_counts.out -e $PWD/get_counts.log <<END
cd $PWD
mpirun ./get_counts
END
```

`$PWD` in the here-documents is expanded when you submit, so both jobs start in
this directory, and `bell_sampler.py` writes `input.bin` where the MPI job
reads it.

LSF:

```bash
QPU=fake_brisbane
QRMI_QPU_RESOURCES=$QPU bsub -K -oo sampling.log "python bell_sampler.py"
mpicxx -O2 -o get_counts get_counts.cpp
bsub -K -n 4 -R "span[ptile=2]" -oo get_counts.log mpirun ./get_counts
```

MPICH's `mpirun` takes the four slots on the two compute nodes from LSF. With
rootless Podman, the MPI job can take several minutes to start its processes on
the second node; let it run. On this container cluster a short job sometimes exits at once
with exit code 255 and an empty `get_counts.log` (`bjobs -a` shows `EXIT`);
submit the MPI job again.

OCS: `run_ocs.sh` does the same steps. It stops before the MPI job if the
sampling job fails or writes no `input.bin`. The jobs write `sampling.out`,
`sampling.log` and `get_counts.log`:

```bash
QPU=qpu=fake_brisbane
bash run_ocs.sh -l "$QPU"
```

## Check the result

Compare the MPI result with the samples:

```bash
cat output.json
python -c 'import json, numpy as np; v, c = np.unique(np.fromfile("input.bin", dtype=np.uint32), return_counts=True); q = {str(k): int(n) for k, n in zip(v, c)}; m = json.load(open("output.json")); assert q == m; print("MPI preserved all", sum(m.values()), "samples")'
```

For an ideal Bell state, expect roughly half `0` and half `3`. A noisy backend
such as `fake_brisbane` also gives a few percent `1` and `2`.

A new run replaces `input.bin` in your working copy. Always compare against the
`input.bin` from that same run.

**Try it:** open `get_counts.cpp`: which MPI calls does it use, and is there
anything quantum-specific in it? What happens to the samples left over if the
number of shots is not divisible by the number of ranks? Then find what stops
the MPI job from running on an old `input.bin` when sampling fails (Slurm: in
`run.sh`; OCS: in `run_ocs.sh`; OpenPBS and LSF: the order of your commands).
