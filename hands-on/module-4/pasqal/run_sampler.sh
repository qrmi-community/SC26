#!/bin/bash
#SBATCH --job-name=sampler
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --qpu=EMU_FREE
#SBATCH --licenses=emu_free@slurmdb:1
#SBATCH -p normal
#SBATCH --time=00:10:00

set -euo pipefail
source /shared/pyenv/bin/activate
srun python chain.py "$@"
