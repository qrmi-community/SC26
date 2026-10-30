#!/bin/bash

#SBATCH --job-name=slurm_mod2
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1

# The participant's environment from Module 2; sbatch --export=ALL,PYENV=<dir> selects another one.
source "${PYENV:-/shared/pyenv}/bin/activate"

srun python "$@"
