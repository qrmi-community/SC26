# LSF Cluster Containers

A local, container-based LSF cluster (1 server + 2 compute nodes) for developing and testing QRMI and LSF hooks without access to a production HPC cluster.

- Ubuntu 24.04 + LSF Community Edition
- MPICH 4.2.3 with PMI support
- Works with Docker or Podman on Apple silicon, Intel/AMD and Windows (WSL2)

| Container   | Role |
|-------------|------|
| `lsf-head`  | LSF management/login node (`mbatchd`) |
| `compute01` | Compute node #1 (`sbatchd`) |
| `compute02` | Compute node #2 (`sbatchd`) |

See **[docs/INSTALL.md](docs/INSTALL.md)** for setup, verification, image details, customization and troubleshooting.

## Files

| Path | Description |
|------|-------------|
| `Dockerfile` | Image shared by all nodes |
| `compose.yaml` | Cluster definition: 3 cluster containers and a one-shot `ssh-generator`, network, shared `/home` volume and `/shared` bind mount |
| `compose.ibm.yaml` | IBM add-on: the local IBM Quantum System API emulator and its S3 storage |
| `compose.warden.yaml` | Pasqal Local add-on: a local Warden, sharing the cluster's MUNGE key |
| `qrmi_config.json.example` | Template for the site-wide QRMI configuration, generated and installed in [LSF Module 1](../../hands-on/module-1/lsf/INSTALL.md) |
| `qrmi_config.json.user.example` | Template for a user's private QRMI values (API keys) |
| `entrypoint.sh` | Configures and starts LSF according to `ROLE` (`head` / `compute`) |
| `examples/` | MPI test programs and job scripts (C and mpi4py) |
| `docs/INSTALL.md` | Installation and reference guide |
| `images/` | Cluster diagram (PNG) |

