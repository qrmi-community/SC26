# Tutorial terminology

Use this as a reference while following the guides of your workload manager and provider.
For the introduction, focus on six terms: workload manager, resource, session,
task, payload and shot. The distinction between a scheduler job and a
quantum task matters throughout the exercises.

## Systems and execution

| Term | Meaning in this tutorial |
| --- | --- |
| HPC | High-performance computing: computing systems and software used for large or demanding workloads. Here we use a small container cluster to demonstrate its job-management pattern. |
| Workload manager / scheduler | Software that queues jobs and assigns execution resources according to requests and policy. This tutorial has tracks for Slurm, OpenPBS, LSF and OCS. |
| Open Cluster Scheduler (OCS) | One of the four workload managers. Use this product name in the tutorial; commands retain names familiar from Grid Engine systems. |
| Host / node | A machine participating in the cluster. One node accepts submissions and manages scheduling; two compute nodes run applications. Here each is a container. |
| Container image | The packaged software used to create a container. Loading an image does not start a running cluster or configure its queues. |
| Container / volume | A container is a running instance of an image. A volume holds data independently of that container, such as the shared home directory and scheduler configuration. |
| Batch job | A program submitted to the workload manager. A job has a scheduler job ID and may submit zero, one or several quantum tasks. The `hostname` exercise submits none. |
| Queue / partition | A scheduler configuration that controls where and how jobs run. In OCS, `qpu.q` has the QRMI hooks and `all.q` runs the classical MPI work. A queue name is not a quantum device. |
| Scheduler hook / plugin | A program the scheduler runs at a point in a job's life, as administrator or as the job's user. **Validator plugins** check a QPU request at submission (Slurm job submit plugin, OpenPBS `qrmi_validate`). **Job execution plugins** acquire the resource before the application starts and release it after it ends: the Slurm SPANK plugin, the OpenPBS hooks, the OCS prolog and epilog, LSF's `JOB_STARTER`, `PRE_EXEC` and `POST_EXEC`. |
| WLM resource / sensor | A scheduler representation of a quantum resource: a Slurm license, OpenPBS counter, or OCS selection/readiness complex. Counters limit allocations within that scheduler; status checks report availability without reserving it. Slurm's poller pushes updates, OpenPBS checks before dispatch, and OCS queries a Warden readiness sensor. The tutorial's LSF integration checks after dispatch and requeues unavailable work. |
| License (Slurm) | A cluster-wide counter that jobs request with `--licenses`. Slurm starts a job only when enough are free. The poller updates monitored licenses from QRMI status; the tutorial's `PASQAL_LOCAL` license is static. A license does not itself reserve a physical QPU. |
| QRMI | Quantum Resource Management Interface. It exposes resource and task operations through a common interface, with provider-specific implementations and payload formats. |
| Resource / backend | A configured execution destination exposed through QRMI, such as a cloud emulator or an on-premises service. A resource name does not necessarily identify a physical QPU. |
| Session / allocation | The context obtained when a resource is acquired and used until it is released. Some backends open a session on acquire (IBM Quantum batch sessions, Pasqal's Warden); for others acquire and release do nothing (Pasqal Cloud, Alice & Bob). Acquisition does not guarantee a physical QPU reservation. |
| Quantum task | One provider execution request created by `task_start`. Its identifier and lifecycle differ from the scheduler job. A scheduler job ending and a quantum task completing are separate events. |
| Payload | The data passed to a quantum backend. Its format depends on the provider: a Qiskit Sampler input for IBM, a serialized Pulser sequence and a shot count for Pasqal, a QIR program for Alice & Bob. It is not a provider-independent quantum program. |
| Warden | Pasqal's service between the scheduler integration and an on-premises QPU. The tutorial's Warden backup drives a mock QPU that simulates with QuTiP. |
| MUNGE | An authentication service common on HPC clusters. The Pasqal Local hooks use it to authenticate to Warden, which holds the same key as the cluster. |
| MPI | Message Passing Interface, used for communication between cooperating processes. A rank is a process's identifier within the MPI communicator. Our example counts samples on four ranks. |
| CPU slot / QPU slot | A CPU slot is a unit requested for a classical process allocation. A QPU slot is one of the parallel jobs a quantum resource accepts; the exercises request one per job. |

## Quantum program and results

| Term | Meaning in this tutorial |
| --- | --- |
| QPU | Quantum processing unit: physical hardware that executes quantum programs. The exercises run on emulators unless you use your own IBM Quantum account. |
| Emulator / simulator | A classical computation of a quantum program's behavior: the local IBM Quantum System API emulator, Pasqal's `EMU_FREE` and Warden mock, Alice & Bob's Felis emulators. |
| Qubit / atom | The basic unit of quantum information: a two-level quantum system that can be in a superposition of its two basis states, `0` and `1`. IBM uses superconducting circuits, Alice & Bob cat qubits stored in superconducting resonators, and Pasqal neutral atoms held in optical tweezers. In the Pasqal example, an atom's ground state is `0` and its Rydberg state `1`. |
| Register (Pasqal) | The collection of atoms, their identifiers and positions. The main example places two atoms five micrometers apart. |
| Layout / device (Pasqal) | A layout describes available trap positions; a device specifies constraints such as geometry and allowed pulse channels. The Pulser program uses a device reported by the allocated resource; `DigitalAnalogDevice` is Pulser's example device, used offline and by the Warden backup. |
| Pulser / sequence (Pasqal) | Pulser is the Python framework used to describe neutral-atom pulse programs. A sequence combines a register, device, channels, pulses and measurement. |
| Pulse / channel (Pasqal) | A pulse specifies controls including amplitude, detuning and phase over time. A channel describes how those controls address the atoms; this example drives a global Rydberg channel. |
| Analog program / circuit | An analog program describes controlled evolution, such as a pulse sequence. A gate circuit describes operations such as H and CNOT. The IBM example runs an H/CNOT circuit; the Pasqal example prepares a Bell-like state with a pulse instead. |
| Rydberg blockade (Pasqal) | An interaction effect that suppresses simultaneous Rydberg excitation of nearby driven atoms. It makes the two-atom program favor a single shared excitation. |
| Shot / bitstring / counts | A shot is one measurement sample. A bitstring records its outcome, such as `01`. Counts are the number of occurrences of each bitstring; their sum must match the requested number of shots after a successful run. |
| Ground/Rydberg basis (Pasqal) | The measurement basis used here: `0` represents the ground state and `1` the Rydberg excitation. `01` and `10` each have one excitation. |
| Bell-like state | The IBM circuit prepares `(\|00> + \|11>)/sqrt(2)`: expect mostly `00` and `11`. The Pasqal pulse approximately prepares `(\|gr> + \|rg>)/sqrt(2)`, up to global phase: expect nearly equal `01` and `10`. Counts alone do not prove entanglement. |
| Histogram | A map from outcomes to counts. The quantum JSON uses binary bitstring keys; the MPI result uses their decimal integer encodings. Compare after converting the keys. |
| Polling / timeout / cancellation | Polling repeatedly queries task status. A timeout bounds waiting. Task cancellation asks the service to stop a task. Cancelling a batch job or releasing a session does not universally cancel its remote tasks; check their backend state. |

## Names and states you will see

| Name or state | Read it as |
| --- | --- |
| `fake_brisbane`, `ibm_kingston` (IBM) | The local IBM Quantum System API emulator and an IBM Quantum backend, as named in the QRMI configuration. |
| `ab_emu_1q_lescanne_2020` (Alice & Bob) | The QRMI resource for Alice & Bob's one-qubit Felis emulator. |
| `ab_emu_6q_physical_cats` (Alice & Bob) | The QRMI resource for Alice & Bob's Felis emulator of six physical cat qubits (Module 3). |
| `PASQAL_LOCAL` (Pasqal) | The configured QRMI resource name used for the Warden backup. Request it exactly as written. |
| `EMU_FREE` (Pasqal) | The Pasqal Cloud emulator resource used in the Pasqal exercises; requires project access and credentials. |
| `QPUBackend` (Pasqal) | Pulser's remote-backend class used by the example. Its class name does not mean the selected resource is physical hardware. |
| `--qpu=...` and `--licenses=...@slurmdb:1` (Slurm) | The resource for the SPANK plugin to acquire, and the license Slurm counts for it. The license name is the resource name in lowercase, for example `emu_free@slurmdb`. |
| `PENDING (Licenses)` (Slurm) | `squeue`'s reason for a job that waits until its license is free. |
| `-l quantum_resources=...` (OpenPBS) | The OpenPBS request selecting the configured quantum resource, optionally with a slot count (`<name>:<slots>`). |
| `QRMI_QPU_RESOURCES=...` (LSF) | The variable that names the quantum resources when calling `bsub`; `JOB_STARTER` reads it. |
| `qpu=...` (OCS) | The OCS request selecting the configured quantum resource name. The execution hosts must advertise the same name. |
| `qpu_ready=1` (OCS) | A scheduling requirement that our Warden readiness sensor report ready. It is not a Cloud-availability check or a task-completion flag. |
| `qw` / `r` / queue `E` (OCS) | OCS queued-and-waiting / running / queue error states. Use `qstat` to investigate; a queue error can indicate a failed prolog. |
| `Completed`, `Failed`, `Cancelled` | Terminal QRMI task outcomes. Retrieve results after `Completed`; do not interpret failure or cancellation as successful empty counts. |

The Module 2 lifecycle table ([IBM](module-2/ibm/README.md#where-acquire-and-release-happen),
[Pasqal](module-2/pasqal/README.md#where-acquire-and-release-happen)) shows which
process owns each call. The [OCS command reference](../containers/ocs/docs/INSTALL.md#slurm-to-ocs-command-reference)
maps familiar Slurm operations to OCS commands.
