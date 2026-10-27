# Open Cluster Scheduler Cluster Containers

A local, container-based Open Cluster Scheduler (OCS) cluster (1 master + 2 execution nodes) for developing and testing QRMI and OCS integrations without access to a production HPC cluster.

- Rocky Linux 9 + Open Cluster Scheduler 9.1.7 (binary release from open.clusterscheduler.io)
- Open MPI 4.1.8 with Grid Engine tight integration + mpi4py (Python 3.12)
- MUNGE on all nodes (used by QRMI for Pasqal Local)
- Docker/Podman and macOS/Windows guidance in [docs/INSTALL.md](docs/INSTALL.md)

| Container | Role |
|-----------|------|
| `ocs-master` | OCS qmaster (`sge_qmaster`); job submission host |
| `ocs-node1` | Execution node #1 (`sge_execd`) |
| `ocs-node2` | Execution node #2 (`sge_execd`) |

See **[docs/INSTALL.md](docs/INSTALL.md)** for setup, verification, image details, customization and troubleshooting.

For the tutorial, build the images ([docs/INSTALL.md](docs/INSTALL.md#1-building-the-containers),
including the tutorial images), then follow
**[Module 1: QRMI with OCS](../../hands-on/module-1/ocs/INSTALL.md)**. It covers
hook installation, the provider configuration and, for Pasqal, a local Warden
backup. Then continue with Module 2 for your provider (see the
[tutorial README](../../README.md#2-choose-your-quantum-provider)).

## Files

| Path | Description |
|------|-------------|
| `Dockerfile` | Image shared by all nodes (OCS, Open MPI, mpi4py, tools) |
| `Dockerfile.qrmi`, `compose.qrmi.yaml` | QRMI 0.26.4 image with MUNGE, Pulser and the OCS hooks |
| `compose.warden.yaml` | Optional local Warden for Pasqal Local (built from `../warden`) on the same MUNGE key and network |
| `compose.ibm.yaml` | Optional local IBM Quantum System API emulator and its S3 storage |
| `compose.yaml` | Cluster definition: 3 containers, network, shared `/home`, `/opt/ocs` and `/etc/munge` volumes and `/shared` bind mount |
| `entrypoint.sh` | Installs (first start) and starts OCS according to `OCS_ROLE` (`master` / `execd`) without systemd |
| `qrmi_config.json.example` | Example QRMI configuration; copied to `/etc/qrmi` in the containers |
| `qrmi-ocs-load-sensor.yaml.example` | Example QRMI Load Sensor configuration; copied to `/etc` in the containers |
| `examples/` | MPI test programs and job scripts (C and mpi4py) |
| `docs/INSTALL.md` | Installation and reference guide |
| `images/` | Cluster diagram (PNG and SVG) |
