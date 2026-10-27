# Installation of Slurm Cluster Containers

This guide sets up a local Slurm cluster in containers, for running QRMI and the SPANK plugin without a production HPC cluster.

## Jump To

- [Container Contents](#container-contents)
- [Prerequisites](#prerequisites)
- [Creating a Docker-based Slurm Cluster](#creating-a-docker-based-slurm-cluster)
  - [1. Building the containers](#1-building-the-containers)
  - [2. Starting the cluster](#2-starting-the-cluster)
  - [3. Verifying the cluster](#3-verifying-the-cluster)
  - [4. Stopping and cleaning up](#4-stopping-and-cleaning-up)

## Container Contents

All cluster nodes are built from the same base image with the following software stack:

| Component | Version | Notes |
|-----------|---------|-------|
| Base OS   | Rocky Linux 9 | RHEL 9–compatible base image |
| Slurm     | 26.05.5 | Workload manager (`slurmctld`, `slurmd`, `slurmdbd`) |
| OpenPMIx  | 4.1.3   | Process management interface used by Slurm and Open MPI |
| Open MPI  | 4.1.8   | MPI implementation, built against the bundled OpenPMIx |

Slurm and Open MPI share the same OpenPMIx installation, so MPI programs can be launched directly with `srun --mpi=pmix` without using `mpirun`.

## Prerequisites

A container manager such as one of the following:

- [Docker](https://docs.docker.com/get-docker/)
- [Podman](https://podman.io/getting-started/installation.html)
- [Rancher Desktop](https://rancherdesktop.io/)

> **Note for Podman users:** `docker-compose` must be installed separately. On macOS, install it with:
>
> ```bash
> brew install docker-compose
> ```
>
> On Ubuntu (including WSL2), use Compose v2 through `podman compose`:
>
> ```bash
> sudo apt install --no-install-recommends podman docker-compose-v2
> systemctl --user enable --now podman.socket
> export PODMAN_COMPOSE_PROVIDER=/usr/libexec/docker/cli-plugins/docker-compose
> ```
>
> On both, also set these before building. Compose's default builder cannot see Podman's local images, so an image built on top of another local image fails with `pull access denied` without them:
>
> ```bash
> export DOCKER_BUILDKIT=0 COMPOSE_DOCKER_CLI_BUILD=0 COMPOSE_BAKE=false
> ```
>
> Add the `export` lines to `~/.bashrc` (`~/.zshrc` on macOS). Don't use Ubuntu's `podman-compose` (1.0.x): it drops the values of `sysctls`, cannot build the local IBM Quantum System API emulator from its Git URL, and does not resolve short image names such as `mariadb:10.11`. Ubuntu's `docker-compose` package is the old v1.
>
> The build compiles Slurm and Open MPI from source, so give the Podman machine at least 4 GB of memory:
>
> ```bash
> podman machine stop
> podman machine set --cpus 4 --memory 4096
> podman machine start
> ```

> **Note for Windows (WSL2) users:**
>
> - **Location**: clone and edit the files inside the WSL file system (for example `~/SC26`), not under `/mnt/c`, to avoid permission and performance problems.
> - **Container manager**: Docker Engine installed inside the WSL distribution works, and so does Docker Desktop. If systemd is not enabled in the distribution, start the daemon after each WSL restart with `sudo service docker start`.
> - **Resources**: with 2 CPUs and about 3 GB of memory for WSL, the first build takes about 25 minutes. Set the memory with `memory=` in `.wslconfig`.
> - **CPU count**: `slurm.conf` defines 4 CPUs per node. `SlurmdParameters=config_overrides` lets nodes register with that count even if the host has fewer cores, so the nodes do not end up in the `inval` state.

## Creating a Docker-based Slurm Cluster

> **Note for Podman users:** The commands below use the `docker` CLI. With Podman, replace `docker` with `podman` (for example `podman logs slurmctld`, `podman exec ...`), or define `alias docker=podman`. `docker compose` / `docker-compose` work with Podman as long as `docker-compose` is installed.


### 1. Building the containers

Run the following command from the directory containing `compose.yml`:

```bash
docker compose build --no-cache
```

The first build compiles Slurm, OpenPMIx and Open MPI from source, so it may take some time.

### 2. Starting the cluster

```bash
docker compose up -d
```

Use `docker ps` to check that the following six containers are running:

| Container   | Role |
|-------------|------|
| `mysql`     | Database node (Slurm accounting storage) |
| `slurmdbd`  | Slurm database daemon node |
| `slurmctld` | Central management node (Slurm controller) |
| `login`     | Login node (job submission) |
| `c1`        | Compute node #1 |
| `c2`        | Compute node #2 |

The containers share two directories:

| Path | Backing storage | Mounted on | Purpose |
|------|-----------------|------------|---------|
| `/shared` | `./shared` on the host (bind mount) | All containers | Exchanging files with the host |
| `/home` | `home` volume | `login`, `c1`, `c2` | Users' home directories, like an NFS home |


Jobs run in the directory they were submitted from and write their output files
there, so submit jobs from a directory in one of them, such as your home
directory or `/shared`. On first start, the `home` volume is filled with `/home`
from the image; it keeps your files until you remove it with
`docker compose down -v`.

You now have a Slurm cluster as shown below:

<p align="center">
  <img src="../images/slurm-docker-cluster.png" width="640">
</p>

### 3. Verifying the cluster

Open a shell on the login node:

```bash
docker exec -it login bash
```

Check that both compute nodes are available (they should be in the `idle` state):

```bash
sinfo -N -l
scontrol ping
sacctmgr show cluster
```

```
Fri Oct 09 11:07:50 2026
NODELIST   NODES PARTITION       STATE CPUS    S:C:T MEMORY TMP_DISK WEIGHT AVAIL_FE REASON              
c1             1   normal*        idle 4       4:1:1   1000        0      1   (null) none                
c2             1   normal*        idle 4       4:1:1   1000        0      1   (null) none

Slurmctld(primary) at slurmctld is UP

   Cluster     ControlHost  ControlPort   RPC     Share GrpJobs       GrpTRES GrpSubmit MaxJobs       MaxTRES MaxSubmit     MaxWall                  QOS   Def QOS 
---------- --------------- ------------ ----- --------- ------- ------------- --------- ------- ------------- --------- ----------- -------------------- --------- 
     linux       10.89.0.4         6817 11520   
```

Run a simple job across both nodes:

```bash
srun -N 2 hostname
```

```
c2
c1
```

Confirm that the PMIx plugin is available to Slurm:

```bash
srun --mpi=list
```

```
MPI plugin types are...
	none
	cray_shasta
	pmi2
	pmix
specific pmix plugin versions available: pmix_v4
```

To test MPI, first copy the example programs from the host into the shared directory:

```bash
# On the host
cp examples/* shared/
```

```bash
cd /shared
mpicc -o hello_mpi hello_mpi.c
sbatch -W hello_mpi.sbatch
cat hello_mpi.o*
```

```
=== Allocated nodes ===
c1
c2
=== srun (launched via Slurm + PMIx; no -np or hostfile needed) ===
Hello from rank 1 of 4 on c1
Hello from rank 0 of 4 on c1
Sum of ranks = 6 (expected 6)
Hello from rank 2 of 4 on c2
Hello from rank 3 of 4 on c2
```

Confirm that Python 3.12 is available in the containers:

```
python3.12 -c 'import sys; print(sys.version)'
```

```
3.12.15 (main, Oct  1 2026, 00:00:00) [GCC 11.5.0 20240719 (Red Hat 11.5.0-14)]
```

To test MPI with mpi4py, first create a Python virtual environment in the shared directory, then submit the job:

```
python3.12 -m venv /shared/pyenv
source /shared/pyenv/bin/activate
pip install mpi4py
cd /shared
sbatch -W hello_mpi4py.sbatch
cat hello_mpi4py.o*
```

```
[mpi4py] rank 2 of 4 on c2 (Python 3.12.15)
[mpi4py] rank 0 of 4 on c1 (Python 3.12.15)
[mpi4py] rank 3 of 4 on c2 (Python 3.12.15)
[mpi4py] rank 1 of 4 on c1 (Python 3.12.15)
[mpi4py] sum of ranks = 6 (expected 6)
```

To change a Slurm configuration file (`slurm.conf`, `cgroup.conf`, `plugstack.conf`, `gres.conf` or `slurmdbd.conf`), edit it in `containers/slurm` on the host and run, from there, `./update_slurmfiles.sh slurm.conf` (or the files you changed). The script replaces the containers' copy and restarts the cluster. Edits made inside a container are lost, for example `JobSubmitPlugins=lua` from Module 1 step 19, so add those lines to the host file first. The restart also stops the license poller daemon of Module 1 (step 16).


### 4. Stopping and cleaning up

If you started the cluster with the add-ons (Module 1 step 2), use the same `-f` list in these commands, for example `docker compose -f compose.yml -f compose.ibm.yml -f compose.warden.yml down`.

Stop the cluster while keeping its data (job accounting database, etc.):

```bash
docker compose down
```

Stop the cluster and remove all volumes for a completely fresh start:

```bash
docker compose down -v
```

With rootless Podman, files that the containers created in `shared/` belong to sub-UIDs of your user, so `rm` cannot delete them; use `podman unshare rm -rf shared`.

## END OF DOCUMENT
