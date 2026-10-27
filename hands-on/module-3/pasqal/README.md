# Pasqal Module 3: Pulser's programming model

**What you learn:** how a provider SDK runs on the resource the scheduler
allocated: the programming interface changes, the resource ownership does not,
and you can tell which lines are specific to the provider.

Open your shell and create the Python environment as described in
[Module 2, Your user environment](../../module-2/pasqal/README.md#your-user-environment),
then work in this module's directory:

```bash
cd ~/hands-on/module-3/pasqal
source /shared/pyenv/bin/activate
```

Open `bell_state.py`. The program:

1. Asks the allocated resource for its devices (`fetch_available_devices()`)
   and defines the atom positions and a layout for one of them. A device fixes
   the rules the sequence must respect, such as the minimum atom distance and
   the laser channels available. Pasqal Cloud reports its QPUs, also for the
   emulator (the log shows `FRESNEL_CAN1`), so the same program would run on
   hardware; the Warden backup reports Pulser's example device
   `DigitalAnalogDevice`, which `--simulate` also uses. The two atoms are 5 micrometers apart (`--distance`), well inside
   the device's blockade radius, which the program prints: within it, the
   atoms cannot both be excited.
2. Declares a global Rydberg channel and adds a pulse.
3. Adds measurement in the ground/Rydberg basis.
4. Runs `QPUBackend(sequence, PulserQRMIConnection())`.

First run the CPU simulator. This needs neither a scheduler allocation nor an
account, and is useful for checking the physics before submitting a task. It
needs the optional simulation package; install it once if you have not yet:

```bash
pip install pulser-simulation==1.9.0
```

Then:

```bash
python bell_state.py --simulate
```

Then run the same sequence through your scheduler and QRMI. Run only the block
for your workload manager below. The resource request is the same as in [Module
2](../../module-2/pasqal/README.md#submit-with-your-scheduler); set it again in
a new shell.

Slurm: the job script `run_bell_state.sh` asks for `EMU_FREE` in its `#SBATCH`
lines; `$REQ` on the command line overrides them, so the same script serves the
Warden backup:

```bash
QPU=EMU_FREE    # or PASQAL_LOCAL for the Warden backup
REQ="--qpu=$QPU --licenses=${QPU,,}@slurmdb:1"
cat run_bell_state.sh
sbatch -W $REQ -o pulser.log run_bell_state.sh --runs 100 --output pulser.json
```

OpenPBS:

```bash
Q=EMU_FREE    # or PASQAL_LOCAL for the Warden backup
qsub -W block=true -l quantum_resources=$Q -o $PWD/pulser.out -e $PWD/pulser.log -- \
  /shared/pyenv/bin/python $PWD/bell_state.py --runs 100 --output $PWD/pulser.json
```

LSF:

```bash
QPU=EMU_FREE    # or PASQAL_LOCAL for the Warden backup
QRMI_QPU_RESOURCES=$QPU bsub -K -oo pulser.log "python bell_state.py --runs 100 --output pulser.json"
```

OCS (delete `pulser.out` and `pulser.log` before re-running: OCS appends to them):

```bash
QPU=qpu=EMU_FREE    # or qpu=PASQAL_LOCAL,qpu_ready=1 for the Warden backup
qsub -sync y -l "$QPU" -o pulser.out -e pulser.log \
  ../../module-2/run_python.ocs bell_state.py --runs 100 --output pulser.json
```

On every scheduler, the log holds the job's output: the atom distance, the
device's blockade radius and any QRMI warnings (on OCS, the hooks' INFO lines
are in `pulser.out` and their warnings in `pulser.log`). The result is in
`pulser.json`:

```bash
cat pulser.json
python -c 'import json; c=json.load(open("pulser.json"))["counter"]; assert sum(c.values()) == 100; print("Single excitation fraction:", (c.get("01", 0)+c.get("10", 0))/100)'
```

Expect nearly all shots in `01` and `10`, with roughly equal counts, as in
[Module 2](../../module-2/pasqal/README.md#the-result). If most shots are `00`,
the pulse did not excite the atoms. The local simulation and remote run need not
have identical counts.

Cloud queue time is outside the hands-on timing budget. If access or queue delays
prevent completing the exercise, switch to the Warden backup: select `PASQAL_LOCAL` as above (on OCS, first
[switch the cluster to Warden](../../module-1/ocs/INSTALL.md#pasqal-switch-to-the-warden-backup));
the output format is unchanged.

**Try it:**

- Run the scheduler command on the other resource (`EMU_FREE` or
  `PASQAL_LOCAL`; on OCS, first run Module 1 step 4 again with that
  `--host-value`, as in
  [switch the cluster](../../module-1/ocs/INSTALL.md#pasqal-switch-to-the-warden-backup)).
  Which lines of `bell_state.py` did you change?
- Move the atoms apart: add `--distance 15` to the program's arguments in your
  scheduler command, with new output names (on Slurm:
  `sbatch -W $REQ -o far.log run_bell_state.sh --runs 100 --distance 15 --output far.json`).
  The log shows the device's blockade radius: about 8 micrometers on Pasqal
  Cloud's devices, 11 on Warden's. Predict the counts, then compare: outside
  the blockade radius the atoms no longer block each other, both can be
  excited, and `11` becomes the most common result. `python bell_state.py
  --simulate --distance 15` shows the same on your CPU.

**Checkpoint:** Which parts of the code describe the physical program, and which
parts select its execution path? What remains unchanged when switching from
Cloud to Local?

For troubleshooting, see [Module 2](../../module-2/pasqal/README.md#if-something-fails).

## Further reading

- Pulser: [Programming a neutral-atom QPU](https://pulser.readthedocs.io/en/stable/programming.html):
  the atoms, pulses and interactions this program uses.
- [Register and Rydberg-atom interactions](https://pulser.readthedocs.io/en/stable/register.html):
  why the atoms' positions matter, and the Rydberg blockade.
- [QPU execution](https://pulser.readthedocs.io/en/stable/tutorials/qpu.html):
  what changes when a sequence runs on a QPU instead of an emulator.
- [Optimal control for antiferromagnetic state preparation](https://pulser.readthedocs.io/en/stable/tutorials/optimization.html):
  a larger version of the atom chain that Module 4 samples.
