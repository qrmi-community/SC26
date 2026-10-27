#!/bin/bash
# Equivalent of: srun -N 2 -n 4 --mpi=pmix ./hello_mpi
#   --nodes=2            : 2 nodes
#   --ntasks-per-node=2  : 2 MPI processes per node -> 4 processes in total
#   --cpus-per-task=1    : 1 core per process -> 2 cores per node
#SBATCH --job-name=hello_mpi
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=2
#SBATCH --cpus-per-task=1
#SBATCH --output=%x.o%j

echo "=== Allocated nodes ==="
scontrol show hostnames "$SLURM_JOB_NODELIST"

echo "=== srun (launched via Slurm + PMIx; no -np or hostfile needed) ==="
srun --mpi=pmix ./hello_mpi
