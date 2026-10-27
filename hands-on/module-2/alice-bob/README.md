# Alice & Bob Module 2: the lower-level QRMI API

Run a QIR program on Alice & Bob's Felis emulator directly through the QRMI API, as a Slurm job. In contrast, [Module 3](../../module-3/alice-bob/README.md) runs a Qiskit circuit through a Qiskit Sampler on the same cluster.

Complete [Slurm Module 1](../../module-1/slurm/INSTALL.md) first, following its
**If you chose Alice & Bob** notes. It configures the cluster with the Alice &
Bob resources and the tutorial's Felis API key, from the
[Alice & Bob onboarding](../../../onboarding/alice-bob.md).

## What's in this directory

- `qrmi_example.py`: the program you submit.
- `circuits/`: QIR programs, ready to submit. The name of each one ends with the
  target it was transpiled for. `circuits/sources/` holds the Qiskit circuits
  they were transpiled from.
- `felis/`: `felis`, a command-line helper for the Felis API, and
  `circuit.py`, an example circuit for it.

## What the program does

`qrmi_example.py` submits a QIR program as a QRMI task, polls its status and
prints the counts. The program to run, `circuits/coin_flip.EMU-1Q-LESCANNE_2020.ll`,
flips a coin with a cat qubit: it prepares `|+>` and measures it, so expect `0`
and `1` about equally often. It runs on `EMU:1Q:LESCANNE_2020`, a one-qubit
emulator, as the QRMI resource `ab_emu_1q_lescanne_2020`.

## Before you start

1. On the host, in `containers/slurm`, copy the hands-on material to the shared
   directory, and give `user` a directory of its own there, `/shared/alice-bob`:

   ```bash
   cp -r ../../hands-on shared/
   docker exec login install -d -o user -g user /shared/alice-bob
   ```

2. Open a shell on the login node as `user`. Copy Modules 2 and 3 into your
   directory, so your jobs can write their results there whoever owns the
   copied material, and create the Python environment for the Alice & Bob
   exercises. All of it is on `/shared`, so the compute nodes see it too:

   ```bash
   docker exec -it -u user -w /shared/alice-bob login bash
   cp -r /shared/hands-on/module-2/alice-bob module-2
   cp -r /shared/hands-on/module-3/alice-bob module-3
   python3.12 -m venv /shared/alice-bob/pyenv
   source /shared/alice-bob/pyenv/bin/activate
   pip install -r module-2/requirements.txt
   cd module-2
   ```

   In a new shell, run `source /shared/alice-bob/pyenv/bin/activate` again, and
   work in `/shared/alice-bob/module-2`.

## Optional: transpile your own circuit

The QIR programs in `circuits/` were transpiled from the circuits in
`circuits/sources/`. To transpile one yourself, for example from your own
version of [`felis/circuit.py`](./felis/circuit.py), put the Felis URL and the
tutorial key from the [Alice & Bob onboarding](../../../onboarding/alice-bob.md)
in a `.env` file in this directory, and run `felis`:

```bash
(umask 077; cat > .env << 'EOF'
QRMI_AB_FELIS_BASE_ENDPOINT=<the Felis URL>
QRMI_AB_FELIS_API_KEY=<the tutorial key>
EOF
)
felis/felis transpile EMU:1Q:LESCANNE_2020 circuits/sources/coin_flip.py > circuits/coin_flip.ll
```

Then submit `circuits/coin_flip.ll` instead of the ready-made program below.
Note that only `felis` reads `.env`; the job gets its credentials from Slurm.

## Submit the task

Open `qrmi_example.py` and find these calls:

```python
resource, = QRMIService().resources()
task = resource.task_start(Payload.AliceBobFelis(human_qir=qir, input_params=...))
status = resource.task_status(task)
result = resource.task_result(task).value
```

`QRMIService` finds the resource that Slurm allocated to the job. The program
does not acquire or release it: the SPANK plugin does that around the job.

```bash
sbatch -W --qpu=ab_emu_1q_lescanne_2020 --licenses=ab_emu_1q_lescanne_2020@slurmdb:1 -o low-level.log \
  --wrap "python qrmi_example.py circuits/coin_flip.EMU-1Q-LESCANNE_2020.ll --shots 100 --output low-level.json"
cat low-level.log
cat low-level.json
python -c 'import json; c=json.load(open("low-level.json"))["counter"]; assert sum(c.values()) == 100; print("Received", sum(c.values()), "shots")'
```

`sbatch -W` waits for the job to finish. The log names the resource and the task.
Its last line is a QRMI warning that releasing the resource is a no-op: Felis
resources need no lock, so this is expected. The result looks like this (the
exact numbers will differ):

```json
{"counter": {"0": 52, "1": 48}}
```

Reflection: Who acquired the resource, and when was it released? What would
change to run the same program on another Felis emulator?

## If something fails

- **The job stays pending:** `squeue` shows `(Licenses)` when the license is not
  free. Check `scontrol show license` and the poller's `poller.log`, as in
  [Module 1's troubleshooting](../../module-1/slurm/INSTALL.md#troubleshooting).
- **`no quantum resource is allocated to this process`:** the program was run
  without `sbatch --qpu=...`.
- **The task failed:** QRMI does not report why. The task ID is the Felis job ID,
  so with the `.env` file of [Optional: transpile your own circuit](#optional-transpile-your-own-circuit),
  `felis/felis job status <task>` shows the job's events and error.
- **Authentication failure:** check the key in `qrmi_config.json` (Module 1,
  step 3), and copy the file into `slurmctld` again (step 4). Avoid printing the
  job's environment: it contains the key.
