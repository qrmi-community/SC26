#!/bin/bash

#SBATCH --job-name=sampler
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --qpu=fake_brisbane
#SBATCH --licenses=fake_brisbane@slurmdb:1

echo "Starting at `date`"
echo "Running on hosts: $SLURM_NODELIST"
echo "Running on $SLURM_NNODES nodes."
echo "Running $SLURM_NTASKS tasks."
echo "Current working directory is `pwd`"

# Your script goes here
source /shared/pyenv/bin/activate
srun python ./bell_sampler.py
