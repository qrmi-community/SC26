#!/bin/bash
set -euo pipefail
source /shared/pyenv/bin/activate
rm -f sampling.out sampling.log  # OCS appends to -o/-e files
rm -f input.bin  # so the MPI job never counts samples from an earlier run
mpicxx -O2 -o get_counts get_counts.cpp
# qsub -sync y returns the exit status of the job, so set -e stops here if sampling failed
qsub -sync y -o sampling.out -e sampling.log "$@" ../../module-2/run_python.ocs chain.py
qsub -sync y get_counts_job.ocs
