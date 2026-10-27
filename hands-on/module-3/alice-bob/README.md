# Alice & Bob Module 3: Qiskit's Sampler

Start from a Qiskit circuit, transpile it for an Alice & Bob cat-qubit emulator,
and run it through a Qiskit `SamplerV2`, as a Slurm job.

Complete [Module 2](../../module-2/alice-bob/README.md) first, including its
"Before you start" section, which copies this module to `/shared/alice-bob/module-3`.
Then work there on the login node:

```bash
docker exec -it -u user -w /shared/alice-bob/module-3 login bash
source /shared/alice-bob/pyenv/bin/activate
```

## What the program does

`bell_sampler.py` prepares a Bell state, `(|00> + |11>)/sqrt(2)`, on
`EMU:6Q:PHYSICAL_CATS`, an emulator of six physical cat qubits, as the QRMI
resource `ab_emu_6q_physical_cats`. Open it and find:

1. `bell_circuit`: the circuit. There is no Hadamard: cat qubits prepare `|+>`
   natively, which is what the Hadamard does to `|0>`, so the circuit prepares
   `|+>` directly and then applies a CNOT. This emulator has no Hadamard gate.
2. `transpile_for`: the circuit is transpiled explicitly, for the gates of the
   resource's target. `get_backend(resource)` builds that target from the
   resource's description.
3. `run_sampler`: `SamplerV2(resource).run([isa_circuit])` runs the transpiled
   circuit and returns a Qiskit result.

`--photons` sets the emulator's `averageNbPhotons`, the average number of
photons for each cat qubit. The job below passes `--photons 4`, the smallest
value the emulator accepts.

`felis_primitives.py` implements `get_backend` and `SamplerV2`, since
`qiskit-alice-bob-provider` has no Sampler. It plays the part that
`qrmi.primitives.ibm` plays in the [IBM exercise](../ibm/README.md). Felis
returns counts rather than individual shots, so only the counts are meaningful,
not the order of the shots.

## Simulate it locally

This needs neither a scheduler allocation nor an API key, and is useful for
checking the circuit before submitting it:

```bash
python bell_sampler.py --mode simulate --shots 1000
```

The simulation is noiseless, so the counter has only `00` and `11`.

## Run it through the scheduler

```bash
sbatch -W --qpu=ab_emu_6q_physical_cats --licenses=ab_emu_6q_physical_cats@slurmdb:1 -o sampler.log \
  --wrap "python bell_sampler.py --shots 1000 --photons 4 --output sampler.json"
cat sampler.log
python -c 'import json; c=json.load(open("sampler.json"))["counter"]; assert sum(c.values()) == 1000; print(c, "00+11:", c.get("00", 0) + c.get("11", 0))'
```

The log shows the operations of the transpiled circuit and the task ID, then the
same QRMI release warning as in Module 2. Most of the 1000 shots are `00` or
`11`, but about 1% are `01` or `10`. The emulator models the noise of physical
cat qubits, and those shots had a bit flip.

Try it: run the job again with `--photons 16`. The `01` and `10` shots are gone.

> **Aside, for the curious:** the
> number of photons in a cat qubit trades one kind of error for another: with
> more photons, bit flips (`0` to `1`) become exponentially rarer, and phase
> flips (`+` to `-`) become more frequent. This job can't see phase flips: a
> phase flip turns `(|00> + |11>)/sqrt(2)` into `(|00> - |11>)/sqrt(2)`, which
> gives the same counts when measured in the Z basis. That is why only bit flips
> show up in the counts.

If a job fails, see [Module 2](../../module-2/alice-bob/README.md#if-something-fails).
