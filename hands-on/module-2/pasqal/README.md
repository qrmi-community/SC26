# Pasqal Module 2: the lower-level QRMI API

**What you learn:** the contract between your program and the resource the
scheduler gives it: find the resource, submit a task, follow its status, fetch
the result, and tell a failed task from an empty result.

Run one neutral-atom program through two programming interfaces. This module
uses QRMI's task API directly; [Module 3](../../module-3/pasqal/README.md) uses
Pulser's backend interface, and [Module 4](../../module-4/pasqal/README.md)
post-processes samples with MPI. All run on Pasqal Cloud's `EMU_FREE` emulator,
or on the local Warden backup without changing the program.

New participants should follow the [Pasqal Cloud onboarding](../../../onboarding/pasqal-cloud-onboarding.md)
and the Module 1 guide of their workload manager first
([Slurm](../../module-1/slurm/INSTALL.md), [OpenPBS](../../module-1/openpbs/INSTALL.md),
[LSF](../../module-1/lsf/INSTALL.md) or [OCS](../../module-1/ocs/INSTALL.md)). The
[terminology reference](../../GLOSSARY.md) explains scheduler jobs, quantum tasks,
sessions, pulses and shots.

The program and the QRMI calls are the same on every scheduler; only the
commands that open a shell and submit a job differ. Each is in its own section
below; skip the schedulers you are not using.
Each module should take about 15 minutes with the cluster and access ready.
MPI is optional. Module 2's exported sequence uses Pulser's example device and
targets emulators; Module 3 builds its sequence for the device the resource
reports, as a hardware run requires.

## What the program does

> **In plain terms.** A *register* says where the atoms are. A *pulse* says how
> the laser drives them over time. A *sequence* is a register plus pulses plus a
> measurement. One *shot* is one run of the sequence, and the result *counts*
> how often each bitstring was measured. Here, `01` and `10` mean that exactly
> one of the two atoms ended up excited.

Two atoms are placed 5 micrometers apart. Rydberg blockade suppresses simultaneous
excitation. A global pulse of about 708 ns prepares approximately
`(|gr> + |rg>)/sqrt(2)`, up to a global phase. Measuring it gives mostly `01` and
`10`, with roughly equal counts. This is the neutral-atom counterpart of a Bell
state example; it uses a pulse rather than an H/CNOT circuit. Module 3 lets you move
the atoms apart and watch the blockade disappear; Pulser's
[Register and Rydberg-atom interactions](https://pulser.readthedocs.io/en/stable/register.html)
explains it in more depth.

Counts fluctuate between runs. Two outcome populations alone do not establish
entanglement: this exercise demonstrates programming and execution, not state
tomography. Module 4's ten-atom program sweeps detuning to favor alternating
excitations along a chain, with defects possible.

## Your user environment

In Modules 2–4 you work as an HPC user: you create your own Python environment
on the cluster's shared volume, `/shared/pyenv`, and your jobs use it. `/shared`
is mounted on every node, so the jobs run with this environment; the job
scripts activate it themselves.

**1. Open your shell.** On the host, give your user a directory for the
environment, then open a shell as that user. Run only the block for your
workload manager and skip the others.

Slurm, on the host in `containers/slurm`:

```bash
until docker exec login curl -fsS http://warden:4207/accessible; do sleep 3; done   # skip without compose.warden.yml
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

OCS (the exercises are already in `~/hands-on`):

```bash
docker exec ocs-master install -d -o ocsuser -g ocsuser /shared/pyenv
docker exec -it -u ocsuser -w /home/ocsuser/hands-on/module-2/pasqal ocs-master bash -l
```

**2. Create the environment** once, inside your shell (on LSF, use `python3`
instead of `python3.12`):

```bash
python3.12 -m venv /shared/pyenv
source /shared/pyenv/bin/activate
pip install qrmi==0.26.4 pulser-core==1.9.0
```

`qrmi` and `pulser-core` are all that Modules 2 and 3 need on a QPU or emulator.
The local CPU simulation in Modules 3 and 4 (`--simulate`) also needs
`pip install pulser-simulation==1.9.0`, which is larger; install it only if you
use it.

**Backup for a slow network.** On OCS, if `pip install` fails, use the
environment prepared in the image. On the host:

```bash
docker exec ocs-master bash -c 'rm -rf /shared/pyenv && ln -s /opt/qrmi/venv /shared/pyenv'
```

The Slurm, OpenPBS and LSF images have no prepared environment.

Whenever you open a new shell, run `source /shared/pyenv/bin/activate` again and
set the resource as shown in your scheduler's section.

## The task API

The payload consists of the serialized pulse sequence and the number of shots.
`make_sequence.py` builds the sequence with Pulser and saves it as `bell.json`.
It needs no QRMI, scheduler, network or credentials, so run it directly in your
shell, then look at the file:

```bash
cd ~/hands-on/module-2/pasqal
python make_sequence.py
python -m json.tool bell.json | head -45
```

This JSON is what QRMI sends to the backend:

- `register`: the two atoms `q0` and `q1`, with their coordinates in micrometers.
- `channels`: the global Rydberg laser channel.
- `operations`: the pulse, with its amplitude and detuning over 708 ns.
- `measurement`: the basis, `ground-rydberg`.
- `device`: the rules of the emulated device (`DigitalAnalogDevice`). Module 3
  uses the device the resource reports instead.

The number of shots is not in the file: it is the `job_runs` value of the
payload below.

Open `qrmi_example.py`. Identify these calls:

```python
resource, = QRMIService().resources()
task = resource.task_start(Payload.PasqalCloud(sequence=sequence, job_runs=runs))
status = resource.task_status(task)
result = resource.task_result(task).value
```

The `PasqalCloud` payload format is used by both Pasqal Cloud and Pasqal Local.
`QRMIService` discovers the resource and session allocated by the scheduler.
The application must not acquire a second Local session or release the hook's
session: the scheduler's hooks own that lifecycle. The complete pattern is
acquire → `task_start` → `task_status` → `task_result` → release; in a batch job,
the scheduler performs the first and last steps, and the program the steps in
between.

## Submit with your scheduler

Use only the section for your workload manager and skip the other three. Each
runs the same program: the Python programs use QRMI's scheduler environment
rather than scheduler-specific variables. Request exactly one Pasqal resource;
the scheduler's plugins acquire it before your program starts and release it
afterwards. A job can also request several resources (on Slurm, for example
`--qpu=EMU_FREE,PASQAL_LOCAL` with both licenses), and `QRMIService().resources()`
then returns all of them; the programs here expect exactly one.

A job script can carry the resource request itself, as directives:

| Scheduler | Directives in the job script |
| --- | --- |
| Slurm | `#SBATCH --qpu=EMU_FREE` and `#SBATCH --licenses=emu_free@slurmdb:1` |
| OpenPBS | `#PBS -l quantum_resources=EMU_FREE` |
| LSF | none: set `QRMI_QPU_RESOURCES=EMU_FREE` when calling `bsub` |
| OCS | `#$ -q qpu.q` and `#$ -l qpu=EMU_FREE` |

The commands below pass the resource on the command line instead, so that one
job script serves both `EMU_FREE` and the Warden backup `PASQAL_LOCAL`.

### Slurm

Complete [Slurm Module 1](../../module-1/slurm/INSTALL.md) with Pasqal as your
provider: `compose.warden.yml` (started by default in step 2) and the `emu_free`
and `pasqal_local` licenses. `compose.warden.yml` adds a local Warden with a
simulated QPU at `http://warden:4207` that shares the cluster's MUNGE key. For Cloud, write your
own account to `~/.pasqal/config` as `user` in the login node
([Pasqal Cloud onboarding, step 3](../../../onboarding/pasqal-cloud-onboarding.md#step-3-write-your-credentials-file));
`/home` is shared, so the compute nodes see it.

A Slurm job asks for a Pasqal resource with two options:

- `--qpu=EMU_FREE` tells the QRMI SPANK plugin which resource to acquire for the
  job and publish to your program.
- `--licenses=emu_free@slurmdb:1` makes Slurm hold the job until the resource is
  free: the license poller daemon keeps the license count in line with what QRMI
  reports. Slurm stores license names in lowercase.

The job submit plugin rejects a job whose `--qpu` has no matching license, so
the two always go together. This job script runs Module 2 on Pasqal Cloud:

```bash
#!/bin/bash
#SBATCH --job-name=module2
#SBATCH --ntasks=1
#SBATCH --time=00:10:00
#SBATCH --qpu=EMU_FREE
#SBATCH --licenses=emu_free@slurmdb:1
set -euo pipefail
source /shared/pyenv/bin/activate
python qrmi_example.py bell.json --runs 100 --output low-level.json
```

Save it as `job.slurm` in `~/hands-on/module-2/pasqal` and submit it with
`sbatch -W job.slurm`. For the Warden backup, use `--qpu=PASQAL_LOCAL` and
`--licenses=pasqal_local@slurmdb:1`.

To switch between the two resources without editing scripts, set the request
once and pass it on the command line; options there override the script's
`#SBATCH` lines. Modules 3 and 4 use the same `REQ`:

```bash
QPU=EMU_FREE    # or PASQAL_LOCAL for the Warden backup
REQ="--qpu=$QPU --licenses=${QPU,,}@slurmdb:1"   # ${QPU,,} is the name in lowercase
cd ~/hands-on/module-2/pasqal
sbatch -W $REQ -o low-level.log --wrap "python qrmi_example.py bell.json --runs 100 --output low-level.json"
cat low-level.json
```

`sbatch -W` returns when the job ends, with the job's exit status. The SPANK
plugin acquires the resource before the job starts and releases it when the job
ends or is cancelled (`scancel <job-id>`); the program uses the session it is
given. `low-level.log` holds the job's output, including QRMI's messages; Slurm
overwrites it on each run. While a job waits, `squeue` shows the reason:
`(Licenses)` means the resource is not free yet.

### OpenPBS

Complete [OpenPBS Module 1](../../module-1/openpbs/INSTALL.md#pasqal-cloud-and-pasqal-local)
with `compose.warden.yaml` and the `EMU_FREE` and `PASQAL_LOCAL` resources, and
write `~/.pasqal/config` as `pbsuser` as described there. A job requests the
resource with `-l quantum_resources=<name>`. Jobs start in your home directory,
so the commands use absolute paths:

```bash
Q=EMU_FREE    # or PASQAL_LOCAL for the Warden backup
PY=/shared/pyenv/bin/python
cd ~/hands-on/module-2/pasqal
qsub -W block=true -l quantum_resources=$Q -o $PWD/low-level.out -e $PWD/low-level.log -- \
  $PY $PWD/qrmi_example.py $PWD/bell.json --runs 100 --output $PWD/low-level.json
cat low-level.json
```

`qsub -W block=true` returns when the job ends; the `.out` and `.log` files can
appear a few seconds later. The hooks acquire the resource when the job starts
on its first compute node and release it when the job ends or is deleted
(`qdel <job-id>`).

### LSF

Complete [LSF Module 1](../../module-1/lsf/INSTALL.md) with Pasqal as your
provider, including your `~/.pasqal/config` (step 4). `/home` and `/shared` are
shared by all LSF nodes. A job requests the resource with the
`QRMI_QPU_RESOURCES` variable when you call `bsub`:

```bash
QPU=EMU_FREE    # or PASQAL_LOCAL for the Warden backup
cd ~/hands-on/module-2/pasqal
QRMI_QPU_RESOURCES=$QPU bsub -K -oo low-level.log "python qrmi_example.py bell.json --runs 100 --output low-level.json"
cat low-level.json
```

`bsub -K` waits for the job to finish; the job inherits your environment,
including the activated Python environment, and `bsub -K` can return a second
before the `-oo` file is written (`-oo` overwrites the file; `-o` would append
to it). `JOB_STARTER` publishes the resource before the program starts and
releases it afterwards; for `PASQAL_LOCAL`, the root `PRE_EXEC`/`POST_EXEC` hook
opens and revokes the Warden session, also when you `bkill` the job.

### OCS

Complete [OCS Module 1](../../module-1/ocs/INSTALL.md) with Pasqal as your
provider. A job requests the resource with `-l qpu=<name>` on `qpu.q`;
`run_python.ocs` is a job script that activates your environment and runs a
Python program there:

```bash
QPU=qpu=EMU_FREE    # or qpu=PASQAL_LOCAL,qpu_ready=1 for the Warden backup
cd ~/hands-on/module-2/pasqal
qsub -sync y -l "$QPU" -o low-level.out -e low-level.log \
  ../run_python.ocs qrmi_example.py bell.json --runs 100 --output low-level.json
cat low-level.json
```

`qpu_ready=1` makes OCS wait until the load sensor reports Warden ready. Before
using `PASQAL_LOCAL`,
[switch the cluster to Warden](../../module-1/ocs/INSTALL.md#pasqal-switch-to-the-warden-backup).
OCS appends to the `-o` and `-e` files, so delete them before re-running, or
choose new names.

A job script can request the resource itself; this one runs Module 2 on Pasqal
Cloud with `qsub -sync y job.ocs`:

```bash
#!/bin/bash
#$ -S /bin/bash
#$ -cwd
#$ -q qpu.q
#$ -l h_rt=00:10:00
#$ -l qpu=EMU_FREE
set -euo pipefail
source /shared/pyenv/bin/activate
python qrmi_example.py bell.json --runs 100 --output low-level.json
```

For the Warden backup, use `#$ -l qpu=PASQAL_LOCAL,qpu_ready=1`.

## The result

On every scheduler the result should look like this (the exact numbers will
differ):

```json
{"counter": {"01": 49, "10": 51}}
```

Check the total:

```bash
python -c 'import json; c=json.load(open("low-level.json"))["counter"]; assert sum(c.values()) == 100; print("Received", sum(c.values()), "shots")'
```

Expect nearly all shots in `01` and `10`, with roughly equal counts. If most
shots are `00`, the pulse did not excite the atoms: check that you submitted
the exported sequence unchanged.

The example polls until completion, failure or cancellation. Its five-minute
polling limit cancels a task that takes too long and exits with an error. A failed
task must not be mistaken for a successful empty result.

On `EMU_FREE`, the job log (on OpenPBS, the hooks' log) and the standalone mode
can show QRMI warnings that acquiring or releasing is not implemented by
`PasqalCloud` (and that a dummy acquisition ID is used). They are expected: Pasqal
Cloud has no session to hold, so acquire and release do nothing for it.

### Where acquire and release happen

| Stage | Scheduler job | Standalone Cloud example |
| --- | --- | --- |
| Acquire | Scheduler hook (OCS prolog, Slurm SPANK plugin, OpenPBS hooks, LSF `JOB_STARTER`/`PRE_EXEC`) | `resource_context()` |
| Submit, poll, fetch | User application | User application |
| Release | Scheduler hook (OCS epilog, Slurm SPANK plugin, OpenPBS hooks, LSF `JOB_STARTER`/`POST_EXEC`) | `finally` in `resource_context()` |

To examine the complete lifecycle in one Python process, use the standalone
Cloud mode outside a batch job. It reads your `~/.pasqal/config`
([Pasqal Cloud onboarding, step 3](../../../onboarding/pasqal-cloud-onboarding.md#step-3-write-your-credentials-file)).
See the [QRMI Cloud configuration reference](https://github.com/qiskit-community/qrmi/tree/0.26.4/examples/qrmi/python/pasqal_cloud).
Then run:

```bash
python qrmi_example.py bell.json --standalone EMU_FREE --runs 100
```

This mode deliberately supports Cloud only. Local acquisition belongs to the
scheduler's privileged hook; do not run the application as root to bypass it.

**Try it:** submit again with `--runs 200` and new output and log files. Before
looking, predict the sum of the counts; then find the task ID in the job's log
and check that it differs from the first run's.

**Checkpoint:** Explain which process owns the session, which call returns a
task identifier, and why task completion and resource release are separate steps.

To see the scheduler hold, cancel and release a resource, and to follow one job
into Warden's records, continue with
[Observe the integration](../../module-1/OBSERVE.md).

## If something fails

- **Wrong shell or directory:** `docker` commands run on the host; the
  scheduler commands and the exercise Python commands run inside the shell you
  opened in [Your user environment](#your-user-environment).
  Each module runs in its own directory: `~/hands-on/module-2/pasqal`,
  `~/hands-on/module-3/pasqal` or `~/hands-on/module-4/pasqal`.
- **No JSON or an empty result file:** check the job's exit status and its log.
  `--output` creates the file before task execution; its existence alone does
  not mean the job succeeded.
- **No allocated resource:** submit through the scheduler with a resource
  request. Plain `python` works for `make_sequence.py` and `--simulate`, not
  for running on the resource.
- **Job rejected or waiting:**
  - Slurm: `sbatch` fails with `--qpu=... requires --licenses ...` when the
    license is missing or not in lowercase. A job pending with `(Licenses)` in
    `squeue` waits for the license: `scontrol show license` shows `Free=0` while
    another job holds it, or until the license poller daemon has released it
    (`EMU_FREE` only; its log is
    `/shared/slurm_poller_daemon_example/poller/poller.log` on `slurmctld`).
  - OpenPBS: `qstat -f <job-id>` shows the reason in `comment`.
  - LSF: `bjobs -l <job-id>` and `bhist -l <job-id>`; a job requeued with exit
    99 found no free resource. A `PASQAL_LOCAL` job that `bhist -l` shows
    dispatched again and again with `pre-exec command exited with non-zero
    status` cannot reach Warden.
  - OCS: `qalter -w p <job-id>` prints why the job cannot start, for example a
    host that `offers only hf:qpu=PASQAL_LOCAL` when you requested `EMU_FREE`;
    compare `qconf -se ocs-node1 | grep complex_values` with your `QPU` value.
    Stop a waiting `qsub -sync y` with Ctrl-C and `qdel <job-id>`.
- **Authentication or connection failure:** check Warden health and MUNGE for
  Local, or the username, password and project ID in `~/.pasqal/config` for
  Cloud. Module 1's check job does not test Cloud credentials; only a task does.
  Avoid printing the job's complete environment; it can contain credentials.
- **Device mismatch:** build the sequence for a device from
  `PulserQRMIConnection().fetch_available_devices()`, as Module 3 does. A
  physical QPU may require different device specs, register layout and pulse
  limits.

**Stop and resume.** Your files in `/shared` are in `containers/<your scheduler>/shared`
on the host. Stop and start the cluster with the same `-f` list you started it
with (`docker compose -f ... stop`, then `start`); `down -v` deletes the volumes,
including `/home` with your `~/.pasqal/config`. On Slurm, start the license
poller daemon again after a restart
([Slurm Module 1, step 16](../../module-1/slurm/INSTALL.md)). On OCS, if the
containers were removed with `down`, follow
[OCS Module 1, Recovery](../../module-1/ocs/INSTALL.md#recovery).

**If Pasqal Cloud is slow for the whole room**, everyone can move to the Warden
backup: set `PASQAL_LOCAL` as the resource, as shown in each scheduler's
section. Nothing else changes on Slurm, OpenPBS and LSF; on OCS, first
[switch the cluster to Warden](../../module-1/ocs/INSTALL.md#pasqal-switch-to-the-warden-backup).
