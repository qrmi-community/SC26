#!/bin/bash

#SBATCH --job-name=verify_setup
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --qpu=ibm_kingston
#SBATCH --licenses=ibm_kingston@slurmdb:1

# Your script goes here
echo Hello
