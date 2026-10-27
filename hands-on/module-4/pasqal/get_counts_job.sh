#!/bin/bash
#SBATCH --job-name=get_counts
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=2
#SBATCH --time=00:05:00
#SBATCH -p normal

set -euo pipefail
srun --mpi=pmix ./get_counts
