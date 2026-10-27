# Slurm Cluster Containers

A local, container-based Slurm cluster (controller, database, login node and 2 compute nodes) for running QRMI and the SPANK plugin without a production HPC cluster.

- Rocky Linux 9 + Slurm 26.05.5
- Open MPI 4.1.8 and Slurm built against OpenPMIx 4.1.3 (`srun --mpi=pmix`)
- Works with Docker or Podman on Apple silicon, Intel/AMD and Windows (WSL2)

| Container | Role |
|-----------|------|
| `mysql` | Database (Slurm accounting storage) |
| `slurmdbd` | Slurm database daemon (`slurmdbd`) |
| `slurmctld` | Slurm controller (`slurmctld`) |
| `login` | Login node (job submission) |
| `c1` | Compute node #1 (`slurmd`) |
| `c2` | Compute node #2 (`slurmd`) |

See **[docs/INSTALL.md](docs/INSTALL.md)** for setup, verification, image details, customization and troubleshooting.

## Files

| Path | Description |
|------|-------------|
| `Dockerfile` | Image shared by all nodes (Slurm, OpenPMIx, Open MPI, tools) |
| `compose.yml` | Cluster definition: 6 containers, network, shared /home volume and /shared bind mount |
| `entrypoint.sh` | Configures and starts each node according to the container command (`slurmdbd` / `slurmctld` / `slurmd` / `login`) |
| `slurm.conf` | Slurm configuration; copied to `/etc/slurm` in the containers |
| `slurmdbd.conf` | `slurmdbd` configuration; copied to `/etc/slurm` in the containers |
| `cgroup.conf` | Slurm cgroup configuration; copied to `/etc/slurm` in the containers |
| `plugstack.conf.example` | Example SPANK plugin configuration (`plugstack.conf`); copied to `/etc/slurm` in the containers |
| `qrmi_config.json.example` | Example QRMI configuration; copied to `/etc/slurm` in the containers |
| `update_slurmfiles.sh` | Updates the Slurm configuration files in the containers from the host |
| `compose.ibm.yml` | IBM add-on: the local IBM Quantum System API emulator and its S3 storage; see the [IBM hands-on](../../hands-on/module-2/ibm/README.md#slurm) |
| `compose.warden.yml` | Pasqal Local add-on: a local Warden; see the [Pasqal hands-on](../../hands-on/module-2/pasqal/README.md#slurm) |
| `docs/INSTALL.md` | Installation and reference guide |
| `images/` | Cluster diagram (PNG) |
