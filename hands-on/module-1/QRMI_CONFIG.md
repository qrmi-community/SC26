# The QRMI resource configuration (`qrmi_config.json`)

Every scheduler integration in this tutorial reads one JSON file that lists the
quantum resources users can request. In Module 1 you generate it from the
template of your track, `containers/<scheduler>/qrmi_config.json.example`, and
deploy it where the scheduler's QRMI plugin or hooks read it. This page
describes the format and the location for each scheduler; the Module 1 guides
contain the commands.

## Format

```json
{
  "resources": [
    {
      "name": "ibm_kingston",
      "type": "ibm-quantum-compute-service",
      "environment": {
        "QRMI_IBM_QCS_ENDPOINT": "https://quantum.cloud.ibm.com/api/v1",
        "QRMI_IBM_QCS_IAM_ENDPOINT": "https://iam.cloud.ibm.com",
        "QRMI_IBM_QCS_SESSION_MODE": "batch",
        "QRMI_IBM_QCS_IAM_APIKEY": "<your API key>",
        "QRMI_IBM_QCS_SERVICE_CRN": "<your service CRN>"
      }
    },
    {
      "name": "PASQAL_LOCAL",
      "type": "pasqal-local",
      "environment": {"QRMI_WARDEN_URL": "http://warden:4207"}
    }
  ]
}
```

| Field | Description |
| --- | --- |
| `name` | The name users request: `--qpu=<name>` in Slurm, `-l quantum_resources=<name>` in OpenPBS, `-l qpu=<name>` in OCS, `QRMI_QPU_RESOURCES=<name>` in LSF. Scheduler resources that track it (Slurm licenses, the OpenPBS counter `qrmi_<name>`) use the same name. |
| `type` | The QRMI resource type (table below). |
| `environment` | Settings passed to QRMI. The keys depend on the type. The integrations pass them to the job as `<name>_<key>`, for example `ibm_kingston_QRMI_IBM_QCS_IAM_APIKEY`. |

## Resource types

| `type` | QRMI type | `environment` keys | In the templates |
| --- | --- | --- | --- |
| `ibm-quantum-system` | `IBMQuantumSystem` | `QRMI_IBM_QS_ENDPOINT`, `_IAM_ENDPOINT`, `_IAM_APIKEY`, `_SERVICE_CRN`, `_AWS_ACCESS_KEY_ID`, `_AWS_SECRET_ACCESS_KEY`, `_S3_ENDPOINT`, `_S3_BUCKET`, `_S3_REGION` | `fake_brisbane`: the local IBM Quantum System API emulator started by `compose.ibm.*` |
| `ibm-quantum-compute-service` | `IBMQuantumComputeService` | `QRMI_IBM_QCS_ENDPOINT`, `_IAM_ENDPOINT`, `_IAM_APIKEY`, `_SERVICE_CRN` | `ibm_kingston` |
| `pasqal-cloud` | `PasqalCloud` | `PASQAL_CONFIG_ROOT`: the home directory that holds the user's `.pasqal/config` (Slurm and OpenPBS; OCS Module 1 step 3 sets it; LSF needs none) | `EMU_FREE` |
| `pasqal-local` | `PasqalLocal` | `QRMI_WARDEN_URL` | `PASQAL_LOCAL`: the Warden started by `compose.warden.*` |
| `alice-bob-felis` | `AliceBobFelis` | `QRMI_AB_FELIS_BASE_ENDPOINT`, `QRMI_AB_FELIS_API_KEY` | `ab_emu_1q_lescanne_2020`, `ab_emu_6q_physical_cats` |
| `iqm-server` | `IQMServer` | `QRMI_IQM_ISA_ENDPOINT`, `QRMI_IQM_ISA_TOKEN` | `garnet_mock` |
| `oqtopus` | `OQTOPUS` | See the [QRMI documentation](https://github.com/qiskit-community/qrmi) | — |

`QRMI_JOB_TIMEOUT_SECONDS` sets the job timeout for any type.

For Pasqal Cloud, each participant keeps their own account in
`~/.pasqal/config` (mode 600); see the [Pasqal Cloud onboarding](../../onboarding/pasqal-cloud-onboarding.md).
`PASQAL_CONFIG_ROOT` names that home directory, because the scheduler hooks run
as root.

## Generating the file

Copy the template of your track and replace the `<...>` placeholders of the
resources you will use. Entries you don't use can stay as they are: a job only
reads the resource it requests. On a production system, remove them. If `jq` is installed, check the
syntax:

```bash
cp qrmi_config.json.example qrmi_config.json
jq . qrmi_config.json > /dev/null && echo OK
```

`jq` can select entries instead of editing by hand, for example
`jq '{resources: [.resources[] | select(.name == "PASQAL_LOCAL")]}' qrmi_config.json.example`.

## Where each scheduler reads it

| Scheduler | Location | Read by | Steps |
| --- | --- | --- | --- |
| Slurm | `/etc/slurm/qrmi_config.json` (the `/etc/slurm` volume shared by all Slurm nodes) | The SPANK plugin (path in `plugstack.conf`) and the license poller (`config_path`) | [Slurm Module 1](slurm/INSTALL.md), steps 3–4 |
| OpenPBS | `/var/spool/pbs/server_priv/qrmi_config.json` on `pbs-server`, mode 600 | The hooks; `install_qrmi_hooks.sh` imports it as their configuration and the server copies it to the compute nodes | [OpenPBS Module 1](openpbs/INSTALL.md#2-generating-the-qrmi-configuration) |
| OCS | `/opt/ocs/qrmi-config.json` (the `/opt/ocs` volume shared by all nodes), mode 600 | The prolog, epilog and load sensor | [OCS Module 1](ocs/INSTALL.md#3-configure-your-provider) |
| LSF | `/opt/lsfce/conf/qrmi_config.json` (no secrets, readable by all) and `~/.config/qrmi_config.json` (the user's keys, mode 600) | The `JOB_STARTER` hook and, for Pasqal Local, the `PRE_EXEC`/`POST_EXEC` hook | [LSF Module 1](lsf/INSTALL.md#2-generating-the-qrmi-configuration) |

After changing the file, deploy it again the same way; for OpenPBS, also run
`install_qrmi_hooks.sh` again.

## Keeping credentials safe

- A file with API keys must be readable by root only, and kept outside `/shared`.
  The guides create it in your copy of the tutorial repository: don't commit it. LSF keeps the keys in the user's file instead.
- The integrations pass the settings to the job's environment, so the user who
  submits the job can read them in that job.
- Users can bring their own credentials instead: Pasqal Cloud through
  `~/.pasqal/config`, OpenPBS through `qsub -v <name>_<key>=...`, Slurm through
  `<name>_<key>=... sbatch ...` (Slurm passes the job's environment to the SPANK
  plugin), for example `ibm_kingston_QRMI_IBM_QCS_IAM_APIKEY=<my apikey> sbatch run_sampler.sh`,
  and LSF through `~/.config/qrmi_config.json`.
