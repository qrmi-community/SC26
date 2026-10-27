# Observe the integration

Modules 1–3 show the integration working. This exercise shows what it does when
the resource is busy, unavailable or cancelled, and how a scheduler job connects
to what the quantum backend recorded. Do it after Module 2; it takes about 15
minutes.

Do the version for your provider: [Pasqal](#pasqal-the-warden-backup) or
[IBM](#ibm-the-local-ibm-quantum-system-api-emulator). Each part has a block or a table row per workload
manager: run only yours. Each part ends with a question; answer it with
something you observed (a queue reason, a log line, a record on the backend),
not from memory.

## Pasqal: the Warden backup

This version uses the Warden backup, `PASQAL_LOCAL`, because Warden's sessions
and tasks can be inspected: it records which scheduler job opened each session,
for which user, and which tasks ran in it.

### Tools

You need two shells: your user shell from
[Module 2, Your user environment](../module-2/pasqal/README.md#your-user-environment),
in `~/hands-on/module-2/pasqal` with the environment activated, and a shell on
the host in `containers/<your workload manager>`. On the host, this prints
Warden's five most recent sessions with their tasks:

```bash
bash ../../hands-on/module-1/warden-sessions.sh
```

It uses Docker, or Podman when Docker does not run the `warden` container; set
`CONTAINER_ENGINE=podman` (or `docker`) to choose.

| Column | Meaning |
| --- | --- |
| `sched. job` | The scheduler's job ID that opened the session. Warden stores it in a column named `slurm_job_id` for every scheduler. |
| `uid` | The UID of the job's user, set by the privileged hook from the scheduler, not by the program. |
| `session`, `opened`, `revoked` | The session's ID, and when the hook opened and revoked it. |
| `task`, `status`, `shots`, `canceled` | The quantum tasks submitted in the session. |

On OCS, first [switch the cluster to Warden](ocs/INSTALL.md#pasqal-switch-to-the-warden-backup).


### Part 1: two jobs, one resource


Submit two jobs that hold `PASQAL_LOCAL` for two minutes each, and see what the
scheduler does with the second one.

**Slurm.** The `pasqal_local` license has a count of 1:

```bash
REQ="--qpu=PASQAL_LOCAL --licenses=pasqal_local@slurmdb:1"
sbatch $REQ --wrap "sleep 120"
sbatch $REQ --wrap "sleep 120"
squeue                                       # the second job: PD (Licenses)
scontrol show license pasqal_local@slurmdb   # Used=1 Free=0
```

**OpenPBS.** The counter `qrmi_PASQAL_LOCAL` has a limit of 1:

```bash
qsub -l quantum_resources=PASQAL_LOCAL -- /bin/sleep 120
qsub -l quantum_resources=PASQAL_LOCAL -- /bin/sleep 120
qstat                                        # the second job stays Q
qstat -f -F json <second job ID> | grep comment   # names qrmi_PASQAL_LOCAL
```

**LSF.** The integration has no counter for the resource:

```bash
QRMI_QPU_RESOURCES=PASQAL_LOCAL bsub sleep 120
QRMI_QPU_RESOURCES=PASQAL_LOCAL bsub sleep 120
bjobs                                        # both run
```

**OCS.** The tutorial's `qpu.q` has no counter for the resource either:

```bash
qsub -q qpu.q -l qpu=PASQAL_LOCAL,qpu_ready=1 -b y /bin/sleep 120
qsub -q qpu.q -l qpu=PASQAL_LOCAL,qpu_ready=1 -b y /bin/sleep 120
qstat                                        # both run
```

Run `warden-sessions.sh` on the host: one open session (empty `revoked`) on
Slurm and OpenPBS, two on LSF and OCS. Now cancel the first job (`scancel`,
`qdel` or `bkill` with its ID) and run the script again: its session is revoked
within seconds, and on Slurm and OpenPBS the second job starts and opens its own.
Cancel the remaining jobs when you are done.

**Question:** Which component made the second job wait, or let it run, and what
output showed it?


### Part 2: when Warden is down


Wait until no job from Part 1 is left (`squeue`, `qstat` or `bjobs`): a job that is
still ending when Warden stops cannot release its session. Then, on the host, stop Warden:

```bash
docker stop warden
```

On OCS, wait until `qhost -F qpu_ready` in your user shell shows `qpu_ready=0`
(20–30 seconds). Then submit one job as in Part 1 and watch it:

| Workload manager | What to expect | Where to look |
| --- | --- | --- |
| Slurm | `pasqal_local` is a static license, so Slurm starts the job on a node; the SPANK plugin cannot open a session and the job fails before your command runs (`FAILED`; the output file says `PASQAL_LOCAL is not accessible`) | `sacct -j <job ID>`, the job's output file |
| OpenPBS | `qrmi_check` finds Warden unreachable before the job starts and puts it back in the queue, without using a node | `qstat -f -F json <job ID> \| grep comment`: `Waiting for quantum resources: PASQAL_LOCAL: temporary QRMI error (<error type>)` |
| LSF | `PRE_EXEC` cannot open a session. LSF puts the job back to pending and dispatches it again every few seconds, with no limit, so it takes a compute-node slot each time and `bjobs` mostly shows `RUN` | `bhist -l <job ID>` (`Pending: The queue's pre-exec command exited with non-zero status`) |
| OCS | Once the load sensor reports `qpu_ready=0`, the job stays `qw`. A job submitted before that starts, its prolog fails, and OCS puts it back in the queue (`Rq`) | `qhost -F qpu_ready`, `qalter -w p <job ID>` |

Start Warden again with `docker start warden` and see whether the job runs. On
Slurm it has already failed: submit it again. On OpenPBS the scheduler retries
at its next cycle (every 10 minutes, or when a job is submitted or ends); to
retry now, run `qmgr -c "set server scheduling = true"`. Cancel the job if it
is still waiting.

**Question:** On which workload managers does a job wait for the resource
without using a compute node, and on which does it fail or occupy a node first?


### Part 3: one job, end to end


Run Pasqal Module 2's program on `PASQAL_LOCAL` once more and note the job ID and your
UID:

| Workload manager | Command |
| --- | --- |
| Slurm | `REQ="--qpu=PASQAL_LOCAL --licenses=pasqal_local@slurmdb:1"; sbatch -W $REQ -o trace.log --wrap "python qrmi_example.py bell.json --runs 100 --output trace.json"` |
| OpenPBS | `qsub -W block=true -l quantum_resources=PASQAL_LOCAL -o $PWD/trace.out -e $PWD/trace.log -- /shared/pyenv/bin/python $PWD/qrmi_example.py $PWD/bell.json --runs 100 --output $PWD/trace.json` |
| LSF | `QRMI_QPU_RESOURCES=PASQAL_LOCAL bsub -K -oo trace.log "python qrmi_example.py bell.json --runs 100 --output trace.json"` |
| OCS | `qsub -sync y -l qpu=PASQAL_LOCAL,qpu_ready=1 -o trace.out -e trace.log ../run_python.ocs qrmi_example.py bell.json --runs 100 --output trace.json` |

Then `id -u` in your shell, `cat trace.log` (it names the task), and
`warden-sessions.sh` on the host. Follow the chain: scheduler job ID → UID →
session → task (`DONE`, 100 shots) → session revoked after the job ended.

Now start a task that runs for about a minute on Warden's simulator and cancel
the job while the task runs. Use the same command with `--runs 60000` and the
output files `long.*` instead of `trace.*`, submitted without waiting: on Slurm
`sbatch` without `-W`, on OpenPBS `qsub` without `-W block=true`, on LSF `bsub`
without `-K`, on OCS `qsub` without `-sync y`. On a small laptop, use fewer runs,
for example `--runs 20000`. Run `warden-sessions.sh` until the
new task shows `RUNNING`, then cancel the job with its ID. Run the script again:
the session is revoked and the task is `CANCELED` (for a few seconds it can
still show `RUNNING` with a `canceled` time), because Warden cancels a session's
unfinished tasks when the session is revoked.

**Question:** On `EMU_FREE`, would cancelling the job also stop the task on
Pasqal Cloud? (Hint: what do acquire and release do for Pasqal Cloud, and does
`qrmi_example.py` stop its task when the job is cancelled?)

**Answers to compare with:** Part 1: the scheduler's counter (Slurm license,
OpenPBS `qrmi_PASQAL_LOCAL`), seen in `squeue` or `comment`; LSF and OCS let
both run and Warden accepted both sessions. Part 2: OpenPBS and OCS wait without
a node (OpenPBS retries at the next scheduling cycle; OCS waits once the load
sensor reports 0), Slurm starts the job on a node and fails it, and LSF retries
`PRE_EXEC` on a compute node until Warden is back, then runs the job. Part 3:
no: Pasqal Cloud has no session, so release does nothing, and the example stops
a task only when its own time limit expires; the task runs on, and stopping it
is the program's job (`task_stop`).

## IBM: the local IBM Quantum System API emulator

This version uses the local IBM Quantum System API emulator from your Module 1:
`fake_brisbane`. Below, `<RES>`
stands for that name. The emulator keeps no record of scheduler jobs or users,
so the trace in Part 3 goes through the task ID. You need two shells (and a
second host shell for the cancel test in Part 3): a shell on the host in `containers/<your workload manager>`, and your user shell from
[IBM Module 2, Your user environment](../module-2/ibm/README.md#your-user-environment),
in `~/hands-on/module-2/ibm` with `/shared/pyenv` activated. Part 3 runs IBM
Module 2's program on its input file; create it for the emulator as IBM Module 2
does:

```bash
python gen_sampler_input.py <RES> http://qsa-sim:8290 sc26apikey crn:v1:local:sc26 --iam_url http://qsa-sim:8290
```

### IBM Part 1: two jobs, one resource

Submit two jobs that each hold the resource for two minutes, and see what the
scheduler does with the second one:

| Workload manager | Command (run it twice) | What happens to the second job |
| --- | --- | --- |
| Slurm | `sbatch --qpu=fake_brisbane --licenses=fake_brisbane@slurmdb:1 --wrap "sleep 120"` | `PD (Licenses)` in `squeue` |
| OpenPBS | `qsub -l quantum_resources=fake_brisbane -- /bin/sleep 120` | stays `Q`; `qstat -f -F json <job ID> \| grep comment`: `Insufficient amount of server resource: qrmi_fake_brisbane` |
| LSF | `QRMI_QPU_RESOURCES=fake_brisbane bsub sleep 120` | runs: there is no counter |
| OCS | `qsub -q qpu.q -l qpu=fake_brisbane -b y /bin/sleep 120` | runs: there is no counter |

Cancel the first job and watch the second start on Slurm and OpenPBS. The
emulator itself would accept several jobs at once (it has five lanes); the
limit of one comes from the scheduler's license or counter. Cancel the
remaining jobs when you are done.

**Question:** Which component made the second job wait, or let it run, and what
output showed it?

### IBM Part 2: when the emulator is down

Wait until no job from Part 1 is left (`squeue`, `qstat` or `bjobs`): a job that is
still ending when the emulator stops cannot release it. Then, on the host, stop the
emulator and submit one job as in IBM Part 1. On
Slurm, submit a second one 2 to 4 minutes later to see both outcomes below:

```bash
docker stop qsa-sim
```

| Workload manager | What to expect | Where to look |
| --- | --- | --- |
| Slurm | The license poller checks the emulator every minute and marks the license busy after 3 failed checks (2 to 4 minutes). A job submitted before that starts and fails (`fake_brisbane is not accessible`); one submitted after waits as `PD (Licenses)` without using a node | `squeue`, `sacct -j <job ID>`, the job's output file (`slurm-<job ID>.out`), on `slurmctld`: `/shared/slurm_poller_daemon_example/poller/poller.log` |
| OpenPBS | `qrmi_check` finds the emulator unreachable before the job starts and keeps it queued, without using a node | `qstat -f -F json <job ID> \| grep comment`: `Waiting for quantum resources: fake_brisbane: temporary QRMI error (<error type>)` |
| LSF | The job starts on a node; `JOB_STARTER` cannot reach the emulator (about 30 seconds per try), prints `QRMI request for fake_brisbane failed, treated as unavailable` and exits 99, so LSF requeues it. After 3 requeues the job is suspended (`PSUSP`, "Job has reached its requeue limit"); it takes a slot on each try. On this container cluster a retry can instead end the job (`EXIT`, exit code 127, `.lsbatch/...: No such file or directory`); submit it again after `docker start qsa-sim` | `bjobs -l <job ID>`, `bhist -l <job ID>` (exit code 99 entries); the message shows with `bsub -Is` |
| OCS | The prolog cannot reach the emulator and asks OCS to reschedule the job: it moves between nodes (`Rr`, `Rq`), taking a slot on each try, and its `.e` file (`~/sleep.e<job ID>`) gets a `No route to host` error each time | `qstat`, `qacct -j <job ID>` (`failed 25 : rescheduling`) |

Start it again with `docker start qsa-sim`. On Slurm the poller frees the
license about a minute later, and a waiting job starts. On OpenPBS the job
starts at the next scheduling cycle (up to 10 minutes);
`qmgr -c "set server scheduling = true"` starts it now. On LSF,
`bresume <job ID>` runs the suspended job. On OCS the job's next try runs.

**Question:** On which workload managers does a job wait for the resource
without using a compute node, and on which does it fail or occupy a node first?

### IBM Part 3: one task, end to end

Run IBM Module 2's program as a job and note the task ID that the job's log
prints (`Resource: <RES>; task: <task ID>`):

| Workload manager | Command |
| --- | --- |
| Slurm | `sbatch -W --qpu=fake_brisbane --licenses=fake_brisbane@slurmdb:1 -o trace.log ../run_python.slurm qrmi_example.py sampler_input_fake_brisbane.json` |
| OpenPBS | `qsub -W block=true -l quantum_resources=fake_brisbane -o $PWD/trace.out -e $PWD/trace.log -- $PWD/../run_python.pbs $PWD/qrmi_example.py $PWD/sampler_input_fake_brisbane.json` |
| LSF | `QRMI_QPU_RESOURCES=fake_brisbane bsub -K -oo trace.log "python qrmi_example.py sampler_input_fake_brisbane.json"` |
| OCS | `qsub -sync y -l qpu=fake_brisbane -o trace.out -e trace.log ../run_python.ocs qrmi_example.py sampler_input_fake_brisbane.json` |

On OpenPBS, the output files appear a second or two after `qsub -W block=true`
returns. On the host, follow the task in the emulator's log:

```bash
docker logs qsa-sim 2>&1 | grep <task ID>
```

It shows the task's request arriving (`"id": "<task ID>"`, with its storage
URLs), the program polling it (`GET /v1/jobs/<task ID>`), then `Executing` and
`Finished`. The chain is scheduler job ID → job log → task ID → emulator;
nothing on the emulator side records the scheduler job or the user.

Now run a long task and cancel its job while the task runs. Copy your input
with many more shots (`shots` in the JSON), then submit it with the same
command, `long_input.json` instead of the input file and the output files
`long.*` instead of `trace.*`, without waiting: on Slurm `sbatch` without `-W`, on OpenPBS `qsub` without
`-W block=true`, on LSF `bsub` without `-K`, on OCS `qsub` without `-sync y`.

```bash
python -c 'import json; d = json.load(open("sampler_input_<RES>.json")); d["parameters"]["shots"] = 20000000; json.dump(d, open("long_input.json", "w"))'
```

On a small laptop, 20 million shots can exhaust the memory; use fewer, for
example `2000000`, and cancel sooner. The task takes 20–30 seconds on a laptop
with enough memory: cancel the job as soon as the emulator starts it
(`docker logs -f --tail 0 qsa-sim 2>&1 | grep Executing` on the host, started
before you submit; Ctrl-C to stop).
Then check the emulator's log again: the task still finishes. Acquire and
release are no-ops for this resource, so cancelling the scheduler job does not
stop the task; only the program can (`task_stop`).

**Question:** At your site, which records would tell you who ran a task on an
IBM backend?

**Answers to compare with:** IBM Part 1: the Slurm license and the OpenPBS
counter `qrmi_fake_brisbane`; LSF and OCS run both jobs, and the emulator
accepts both tasks. IBM Part 2: OpenPBS waits without a node; Slurm waits
without a node once the poller has marked the license busy, and fails jobs
that start before that; LSF requeues the job and suspends it after 3 tries
(`bresume` runs it later); OCS keeps retrying it on the nodes.
IBM Part 3: the scheduler's accounting (job ID, user, time) and the job's log
with the task ID; the emulator itself records only the task. With a real IBM
backend, the provider's own records of the task complete the chain.
