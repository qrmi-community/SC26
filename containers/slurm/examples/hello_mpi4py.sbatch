#!/bin/bash
# Runs mpi4py (Python 3.12) on 2 nodes with 4 processes in total
#   --nodes=2            : 2 nodes
#   --ntasks-per-node=2  : 2 MPI processes per node -> 4 processes in total
#   --cpus-per-task=1    : 1 core per process -> 2 cores per node
#SBATCH --job-name=hello_mpi4py
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=2
#SBATCH --cpus-per-task=1
#SBATCH --output=%x.o%j

source /shared/pyenv/bin/activate

srun --mpi=pmix python hello_mpi4py.py
