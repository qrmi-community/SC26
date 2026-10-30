# Installation of LSF Cluster Containers

This document describes how to set up a local, container-based LSF development environment. The environment is intended for developing and testing QRMI and LSF hooks without access to a production HPC cluster.

## Jump To

- [Container Contents](#container-contents)
- [Prerequisites](#prerequisites)
- [Creating a Podman-based LSF Cluster](#creating-a-podman-based-lsf-cluster)
  - [1. Building the containers](#1-building-the-containers)
  - [2. Starting the cluster](#2-starting-the-cluster)
  - [3. Verifying the cluster](#3-verifying-the-cluster)
  - [4. Stopping and cleaning up](#4-stopping-and-cleaning-up)
- [LSF Command Reference](#lsf-command-reference)
- [Image Details](#image-details)
- [Customizing the Cluster](#customizing-the-cluster)
- [Troubleshooting](#troubleshooting)

## Container Contents

All cluster nodes are built from the same base image with the following software stack:

| Component | Version | Notes |
|-----------|---------|-------|
| Base OS   | Ubuntu 24.04 | |
| LSF CE    | 10.2.0.15 | Workload manager (`mbatchd`, `sbatchd`) |
| Python    | 3.12.3 | Used by the QRMI hooks |
| MPICH     | 4.2.3   | MPI implementation, built without Fortran support |
| mpi4py    | latest at build time | Python 3.12 MPI bindings |

Instructions for downloading LSF can be found in [TUTORIAL_DOWNLOADS.md](TUTORIAL_DOWNLOADS.md). The tar file should be placed in the shared directory.

MPICH is built with PMI support, so `mpirun` inside an LSF job automatically picks up the nodes allocated by LSF and launches its processes through LSF. No hostfile, `-np` option or ssh is required.

The LSF daemons are started from `entrypoint.sh` after LSF is installed and configured in the containers.

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
> Add the `export` lines to `~/.bashrc` (`~/.zshrc` on macOS). Don't use Ubuntu's `podman-compose` (1.0.x): it drops the values of `sysctls`, cannot build the local IBM Quantum System API emulator from its Git URL, and does not resolve short image names such as `rustfs/rustfs`. Ubuntu's `docker-compose` package is the old v1.
>
> The head node compiles MPICH from source on its first start (unless a prebuilt MPICH archive is in `shared/`), so give the Podman machine at least 8 GB of memory:
>
> ```bash
> podman machine stop
> podman machine set --cpus 8 --memory 8192
> podman machine start
> ```

> **Note for Windows (WSL2) users:**
>
> - **Location**: extract and edit the files inside the WSL file system (for example `~/SC26`), not under `/mnt/c`, to avoid permission and performance problems.
> - **Line endings**: files saved by Windows editors may get CRLF line endings, which break shell scripts. `entrypoint.sh` is converted to LF automatically at build time; fix job scripts with `dos2unix *.bsub` before submitting them.
> - **Subnet**: the cluster uses `10.10.10.0/24`. If that range is already used on your machine or network, see [Changing the network](#changing-the-network).
> - **Container manager**: Podman runs directly on Linux in WSL, so no Podman machine is needed (on Ubuntu, see the Podman note above). Docker Desktop also works. Memory is set with `memory=` in `.wslconfig`.

The image builds natively on both Apple silicon (arm64) and Intel/AMD (x86_64) hosts. An image built on one architecture cannot be reused on the other; build it again on each host.

## Creating a Podman-based LSF Cluster

> **Note for Docker users:** The commands below use the `podman` CLI. With Docker, replace `podman` with `docker` or define `alias podman=docker`.

### 1. Building the containers

Run the following command from the directory containing `compose.yaml`:

```bash
podman compose build --build-arg LSF_TAR=lsfsce10.2.0.15-armv8.tar.Z    # Apple silicon (arm64)
podman compose build --build-arg LSF_TAR=lsfsce10.2.0.15-x86_64.tar.Z   # Intel/AMD (x86_64)
```

Run the line for your architecture (Intel/AMD hosts, including Windows/WSL2, use the x86_64 one). The archive itself
must be in `containers/lsf/shared/` (see [TUTORIAL_DOWNLOADS.md](TUTORIAL_DOWNLOADS.md)); it is installed on the first start.

`LSF_TAR` is stored in the image and read when the head node first starts. If the image is rebuilt without `--build-arg` (for example by `podman compose up --build`), the head node uses the package for its architecture from `containers/lsf/shared/`; if there is none, it stops with `ERROR: LSF CE package '...' does not exist in /shared`.

The build itself is quick. The slow steps run when the cluster first starts: the head node installs LSF (about 5 minutes) and then installs MPICH. If `containers/lsf/shared/` contains a prebuilt `mpich-4.2.3-<arch>-install.tgz` (`<arch>` is `x86_64` or `aarch64`), it is unpacked; otherwise MPICH is compiled from source, which took about 55 minutes on a 2-core laptop with 2.8 GB of RAM (Windows, WSL2, rootless Docker). Both steps run only once, because the results are kept in the `opt_install` volume; on a small machine, provide the prebuilt MPICH or do the first start before the session.

### 2. Starting the cluster

Start the cluster with the add-ons of all vendors. The `-d` specifies detached mode. If it is not used, container messages will be output to the terminal.

```bash
podman compose -f compose.yaml -f compose.ibm.yaml -f compose.warden.yaml up -d
```

`compose.ibm.yaml` adds the local IBM Quantum System API emulator (`fake_brisbane`); it builds the API emulator from GitHub on first start. `compose.warden.yaml` adds a local Warden for Pasqal Local, which shares the cluster's MUNGE key; its image is built from `containers/warden` on first start.

To run fewer containers, leave out `compose.ibm.yaml` or `compose.warden.yaml`. Both start only local backends: the IBM emulator for participants without an IBM account, and Warden as Pasqal's offline backup. Jobs on IBM Quantum Platform or Pasqal Cloud don't need them. Use the same `-f` list in every later `podman compose` command.

Use `podman ps` to check that the following three cluster containers are running (the add-ons start more, such as `warden` and `qsa-sim`):

| Container    | Role |
|--------------|------|
| `lsf-head`   | LSF management/login host (`mbatchd`) |
| `compute01`  | Compute host #1 (`sbatchd`) |
| `compute02`  | Compute host #2 (`sbatchd`) |

The containers share two directories:

| Path | Backing storage | Purpose |
|------|-----------------|---------|
| `/home` | Named volume `lsf_home` | Shared home directory, like an NFS home on a real cluster |
| `/shared` | `./shared` on the host (bind mount) | Exchanging files with the host |

Jobs can be submitted from either `/home/lsfuser` or `/shared`.

When not running in detached mode, the startup is complete after the following messages have been printed (on the first start, only after LSF is installed and MPICH is compiled, see [1. Building the containers](#1-building-the-containers)):

```
lsf-head      | LSF head node ready. Container initialization complete.
compute01     | LSF compute node ready. Container initialization complete.
compute02     | LSF compute node ready. Container initialization complete.
```

When running in detached mode, check the startup with:

```bash
podman logs lsf-head | tail -n 10
podman logs compute01 | tail -n 10
podman logs compute02 | tail -n 10
```

On the first start, wait until `lsf-head` prints `LSF head node ready. Container initialization complete.` (follow it with `podman logs -f lsf-head`). Until then, `lsfuser` has no LSF commands: `bhosts: command not found` means that the head node is still installing LSF or compiling MPICH.

You now have an LSF cluster as shown below:

<p align="center">
  <img src="../images/lsf-cluster.png" width="700">
</p>

### 3. Verifying the cluster

Open a shell on `lsf-head` as `lsfuser`, starting in its home directory using the following:

```bash
podman exec -it -u lsfuser -w /home/lsfuser lsf-head bash -l
```

> Without `-w /home/lsfuser`, the shell starts in `/`. The commands below assume that the current directory is `/home/lsfuser`.

Check that both compute nodes are available (they should be in the `ok` state; right after the start they can show `unavail` or `closed` for about a minute, and `lsf-head` stays `closed` because it runs no jobs):

```bash
bhosts
```

Run a simple job:

```bash
bsub -Is hostname
```

MPI can be tested using the programs in the examples directory.

Use the following commands to compile and run a small MPI program using the installed MPICH. The job script requests 2 nodes with 2 processes each (4 processes in total):

```bash
cd examples
mpicc -o hello_mpi hello_mpi.c
bsub -Is -n 4 -R "span[ptile=2]" mpirun ./hello_mpi
```

```
Hello from rank 0 of 4 on compute02
Sum of ranks = 6 (expected 6)
Hello from rank 2 of 4 on compute01
Hello from rank 1 of 4 on compute02
Hello from rank 3 of 4 on compute01
```

The order of the lines may differ. `Sum of ranks = 6 (expected 6)` confirms that MPI communication between the nodes works.

Set up the Python environment for lsfuser with the following commands:

```bash
python3 -m venv /shared/pyenv
source /shared/pyenv/bin/activate
pip install mpi4py
```

To run the same test with mpi4py use the following command. Of course, the `source $HOME/pyenv/bin/activate` is redundant immediately after setting up the Python environment above. It was included for completeness.

```bash
bsub -Is -n 4 -R "span[ptile=2]" "source $HOME/pyenv/bin/activate; mpirun python3 ./hello_mpi4py.py"
```

```
[mpi4py] rank 0 of 4 on compute01 (Python 3.12.3)
[mpi4py] rank 1 of 4 on compute01 (Python 3.12.3)
[mpi4py] rank 2 of 4 on compute02 (Python 3.12.3)
[mpi4py] rank 3 of 4 on compute02 (Python 3.12.3)
[mpi4py] sum of ranks = 6 (expected 6)
```

Both the `hello_mpi` and `hello_mpi4py` examples can be run using bsub scripts in the examples directory as follows:

```bash
bsub < hello_mpi.bsub
bsub < hello_mpi4py.bsub
```

Instructions for the next step in the tutorial can be found in `hands-on/module-1/lsf/INSTALL.md`. The sections below are for reference.

### 4. Stopping and cleaning up

Stop the cluster while keeping its data (the `/home` volume):

```bash
podman compose -f compose.yaml -f compose.ibm.yaml -f compose.warden.yaml down
```

Stop the cluster and remove all volumes for a completely fresh start:

```bash
podman compose -f compose.yaml -f compose.ibm.yaml -f compose.warden.yaml down -v
```

Use the same `-f` list you started the cluster with. Without the add-on files, Warden and the local IBM Quantum System API emulator keep running and the network is not removed.

With rootless Podman, files that the containers created in `shared/` belong to sub-UIDs of your user, so `rm` cannot delete them; use `podman unshare rm -rf shared`.

## LSF Command Reference

| Command   | Description |
|-----------|-------------|
| `lsadmin` | Administrator command to manage the base cluster infrastructure and host-level daemons (lim and res). |
| `badmin`  | Administrator command to manage the batch scheduling engine and job-level daemons (mbatchd and sbatchd) |
| `bhosts`  | Displays the status and resource availability of execution hosts in the cluster |
| `bsub`    | Submits a new job to the LSF batch system |
| `bjobs`   | Displays information about active, pending, and recently completed jobs |
| `bkill`   | Sends a signal to terminate or cancel running or pending jobs |
| `bacct`   | Displays historical accounting statistics for completed jobs |

## Image Details

### Users and permissions

- Jobs are submitted as `lsfuser` (UID 1002).
- `lsfuser` can use `sudo` without a password (`/etc/sudoers.d/lsfuser`). This is intended for a local test cluster only.

## Customizing the Cluster

### Adding compute nodes

1. Add a service to `compose.yaml` (for example `compute03`).
2. Add the node name to the `getent hosts` list in `entrypoint.sh`.
3. Add the node name to `LSF_MASTER_LIST` in `install-lsf.sh`.
4. Run `podman compose up -d` with the same `-f` list you started the cluster with. The add-ons give each node the addresses of `warden`, `qsa-sim` and `rustfs` in `extra_hosts`; add the new node there too.

### Changing the network

If `10.10.10.0/24` conflicts with another network (for example the WSL2 network, or another cluster on the same host: `subnet 10.10.10.0/24 is already used on the host`), move the cluster to another range such as `10.89.10.0/24`. Change every `10.10.10.` address in three files:

- `compose.yaml`: the `subnet` of the `lsfnet` network and the `ipv4_address` of the three nodes
- `compose.ibm.yaml` and `compose.warden.yaml`: the `ipv4_address` of `qsa-sim`, `rustfs` and `warden`, and `extra_hosts`

Or replace them all with one command:

```bash
sed -i 's/10\.10\.10\./10.89.10./g' compose.yaml compose.ibm.yaml compose.warden.yaml
```

## Troubleshooting

The entrypoint stops at the first failing command (`set -e`), so the container exits; its output shows the failing step. If a container has failed to start, the logs can be inspected as follows:

```bash
podman logs lsf-head
podman logs compute01
podman logs compute02
```

## END OF DOCUMENT
