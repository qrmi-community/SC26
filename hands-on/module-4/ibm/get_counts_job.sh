#!/bin/bash
#SBATCH --job-name=get_counts      # Job name
#SBATCH --nodes=2                # Request 2 nodes
#SBATCH --ntasks-per-node=2      # 2 MPI tasks per node (4 in total)
#SBATCH --time=00:05:00          # Time limit (hh:mm:ss)
#SBATCH -p normal

echo "Starting at `date`"
echo "Running on hosts: $SLURM_NODELIST"
echo "Running on $SLURM_NNODES nodes."
echo "Running $SLURM_NTASKS tasks."
echo "Current working directory is `pwd`"

# Run the MPI program using srun or mpirun
# srun is often the preferred method with Slurm
srun ./get_counts
# Alternatively, you could use mpirun:
# mpirun ./get_counts
