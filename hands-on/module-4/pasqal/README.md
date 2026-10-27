# Pasqal Module 4: MPI post-processing (optional)

**What you learn:** quantum work integrates with the standard HPC libraries
you already use. Here the results of a quantum job go to an ordinary MPI
program, compiled with `mpicxx` and started by your workload manager like any
other MPI job.

This is the stretch goal: do it if you finish Modules 1–3 early, or after the
break. A quantum sampling job writes its samples; a classical MPI job then
processes them on both compute nodes. Nothing in the MPI program knows about
QRMI or the quantum resource.

Sample a ten-atom chain, then count the samples across four MPI ranks on the
two execution nodes. Only the sampling job requests a quantum resource.

This module uses pattern A: a separate quantum job, then a separate MPI job that
runs only after the sampling job succeeded. Slurm uses an `afterok` dependency;
the OCS helper waits for successful sampling before submitting the MPI job.
On OpenPBS and LSF, confirm that sampling succeeded before continuing with the
MPI commands. In pattern B, MPI rank 0 runs the quantum task itself inside one
parallel job, and the other ranks wait for its result. Pattern A keeps the
quantum resource allocated only while sampling; pattern B keeps all MPI ranks
allocated during the quantum task.

Open your shell as described in
[Module 2](../../module-2/pasqal/README.md#your-user-environment). In a new shell,
activate the environment first:

```bash
source /shared/pyenv/bin/activate
cd ~/hands-on/module-4/pasqal
```

## The sampling program

Open `chain.py`. The program:

1. Places ten atoms in a line, 6 micrometers apart: close enough that
   neighbors block each other's excitation.
2. Adds one pulse that sweeps the detuning from negative, where the atoms stay
   in the ground state, to positive, where excitation is favored. Because
   neighbors cannot both be excited, most shots nearly alternate `1` and `0`,
   usually with one defect such as `1010101001`; perfectly alternating strings
   are rarer. Pulser's
   [antiferromagnetic state preparation tutorial](https://pulser.readthedocs.io/en/stable/tutorials/optimization.html)
   explains this in more depth.
3. Runs it on the allocated resource as in Module 3, prints the three most
   common bitstrings, and writes one native `uint32` per shot to `input.bin`.
   If the task fails, the program exits with an error and writes no
   `input.bin`, so that the workload manager marks the sampling job as failed.

The quantum result is already a histogram. `chain.py` expands it into samples
for MPI to count again, so that the result is easy to check. The point is the
integration with MPI, not a speedup: in a real workflow, this is where your own
MPI code (post-processing, a classical optimizer, a simulation) takes the
quantum results.

## Run it

Run only the block for your workload manager below. The steps are the same on
every scheduler: compile the MPI program, run the sampling job on the quantum
resource (`input.bin`), then run the MPI job with four ranks on the two compute
nodes. The MPI job needs no quantum resource. `MPI_Scatterv` divides the
samples, including any remainder, and `MPI_Reduce` adds the local histograms.
Each rank prints its node and its share, for example
`Rank 2 of 4 on c2: 125 samples`: two ranks should be on each compute node. The
lines are in the MPI job's output file (on Slurm and LSF `get_counts.log`, on
OpenPBS `get_counts.out`, on OCS `get_counts_job.ocs.o<job ID>`).
JSON output keys are decimal encodings of the input bitstrings: for example,
binary `0101010101` is decimal `341`.

Slurm: `run.sh` submits both jobs. The MPI job starts only after the sampling
job succeeded (`--dependency=afterok`); `run.sh` returns when it ends, and fails
if sampling failed. The jobs write `sampling.log` and `get_counts.log`:

```bash
QPU=EMU_FREE    # or PASQAL_LOCAL for the Warden backup
REQ="--qpu=$QPU --licenses=${QPU,,}@slurmdb:1"
bash run.sh $REQ
```

OpenPBS:

```bash
Q=EMU_FREE    # or PASQAL_LOCAL for the Warden backup
qsub -W block=true -l quantum_resources=$Q -o $PWD/sampling.out -e $PWD/sampling.log <<END
cd $PWD
source /shared/pyenv/bin/activate
python chain.py
END
mpicxx -O2 -o get_counts get_counts.cpp
qsub -W block=true -l select=2:ncpus=2:mpiprocs=2 -l place=scatter -o $PWD/get_counts.out -e $PWD/get_counts.log <<END
cd $PWD
mpirun ./get_counts
END
```

`$PWD` in the here-documents is expanded when you submit, so both jobs start in
this directory, and `chain.py` writes `input.bin` where the MPI job reads it.

LSF:

```bash
QPU=EMU_FREE    # or PASQAL_LOCAL for the Warden backup
export PATH=/opt/mpich/bin:$PATH
QRMI_QPU_RESOURCES=$QPU bsub -K -oo sampling.log "python chain.py"
mpicxx -O2 -o get_counts get_counts.cpp
bsub -K -n 4 -R "span[ptile=2]" -oo get_counts.log mpirun ./get_counts
```

MPICH's `mpirun` takes the four slots on the two compute nodes from LSF. With
rootless Podman, the MPI job can take several minutes to start its processes on
the second node; let it run. On this container cluster a short job sometimes exits at once
with exit code 255 and an empty `get_counts.log` (`bjobs -a` shows `EXIT`);
submit the MPI job again.

OCS: `run_ocs.sh` does the same steps:

```bash
QPU=qpu=EMU_FREE    # or qpu=PASQAL_LOCAL,qpu_ready=1 for the Warden backup
bash run_ocs.sh -l "$QPU"
```

## Check the result

Compare the MPI result with the samples:

```bash
cat output.json
python -c 'import json, numpy as np; v, c = np.unique(np.fromfile("input.bin", dtype=np.uint32), return_counts=True); q = {str(k): int(n) for k, n in zip(v, c)}; m = json.load(open("output.json")); assert q == m; print("MPI preserved all", sum(m.values()), "samples")'
```

The included `input.bin` is an old example input. A new run replaces it in your
working copy. Always compare against the `input.bin` from that same run.

For a network-free exercise even without Warden, generate input on the CPU and
submit only the classical MPI job. This needs the optional
`pulser-simulation==1.9.0` package
([Module 2, Your user environment](../../module-2/pasqal/README.md#your-user-environment)):

```bash
python chain.py --simulate --runs 1003
mpicxx -O2 -o get_counts get_counts.cpp
```

Then submit only the MPI job: on Slurm `sbatch -W -o get_counts.log get_counts_job.sh`, on OCS
`qsub -sync y get_counts_job.ocs`, on OpenPBS and LSF the MPI command above.
Repeat the comparison. Using 1,003 shots checks the case where four ranks do
not divide the work evenly.

**Try it:** open `get_counts.cpp`: which MPI calls does it use, and is there
anything quantum-specific in it? Then find what stops the MPI job from running
on an old `input.bin` when sampling fails (Slurm: in `run.sh`; OCS: in
`run_ocs.sh`; OpenPBS and LSF: the order of your commands).
