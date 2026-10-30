# Test matrix

| Container engines | Containers | Platform | Host OS | Result |
| ---- | ---- | ---- | ---- | ---- |
| Linux docker | openpbs | x86_64 | Ubuntu 24.04.5 LTS | Confirmed |
| | ocs | x86_64 | Ubuntu 24.04.5 LTS | Confirmed |
| | slurm | x86_64 | Ubuntu 24.04.5 LTS | Confirmed |
| | lsf | x86_64 | Ubuntu 24.04.5 LTS | Confirmed |
| Docker Desktop | openpbs | aarch64 | macOS | Confirmed |
| | ocs | aarch64 | macOS | Confirmed |
| | slurm | aarch64 | macOS | |
| | lsf | aarch64 | macOS | Confirmed |
| Rancher Desktop 1.24 | openpbs | aarch64 | macOS | Confirmed |
| | ocs | aarch64 | macOS | Confirmed |
| | slurm | aarch64 | macOS | Confirmed |
| | lsf | aarch64 | macOS | Confirmed |
| Podman 6.0.2 | openpbs | aarch64 | macOS | Confirmed |
| | ocs | aarch64 | macOS | Confirmed |
| | slurm | aarch64 | macOS | Confirmed |
| | lsf | aarch64 | macOS | Confirmed |
| | openpbs | x86_64 | macOS | Confirmed |
| | ocs | x86_64 | macOS | Confirmed |
| | slurm | x86_64 | macOS | Confirmed |
| | lsf | x86_64 | macOS | Confirmed |
| Windows/WSL | openpbs | x86_64 | Windows + Ubuntu 20.04| Confirmed |
| | ocs | x86_64 | Windows  + Ubuntu 20.04 | Confirmed |
| | slurm | x86_64 | Windows  + Ubuntu 20.04 | Confirmed |
| | lsf | x86_64 | Windows | Confirmed |
| Podman 4.9.3 (Windows/WSL) | openpbs | x86_64 | Windows + Ubuntu 24.04 | Confirmed |
| | ocs | x86_64 | Windows + Ubuntu 24.04 | Confirmed |
| | slurm | x86_64 | Windows + Ubuntu 24.04 | Confirmed |
| | lsf | x86_64 | Windows + Ubuntu 24.04 | Confirmed |
| Rootless Docker 29.9 (Windows/WSL) | openpbs | x86_64 | Windows + Ubuntu 24.04 | Confirmed |
| | ocs | x86_64 | Windows + Ubuntu 24.04 | Confirmed |
| | slurm | x86_64 | Windows + Ubuntu 24.04 | Confirmed |
| | lsf | x86_64 | Windows + Ubuntu 24.04 | Confirmed |

On a 2-core laptop with 3 GB of RAM (rootless Docker in WSL), the first start of the LSF cluster takes about an hour, mostly compiling MPICH.
