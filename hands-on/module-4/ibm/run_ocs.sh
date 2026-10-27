#!/bin/bash
# Sampling job (quantum), then the MPI job, which runs only if sampling succeeded.
# Pass the resource request, e.g.: bash run_ocs.sh -l qpu=fake_brisbane
set -euo pipefail
source /shared/pyenv/bin/activate
rm -f sampling.out sampling.log get_counts.log  # OCS appends to -o/-e files
rm -f input.bin  # so the MPI job never counts samples from an earlier run
mpicxx -O2 -o get_counts get_counts.cpp
# qsub -sync y returns the exit status of the job, so set -e stops here if sampling failed
qsub -sync y -o sampling.out -e sampling.log "$@" ../../module-2/run_python.ocs bell_sampler.py
# bell_sampler.py writes input.bin only when the sampler returned a result
[ -s input.bin ] || { echo "Sampling produced no input.bin; see sampling.out and sampling.log" >&2; exit 1; }
qsub -sync y -o get_counts.log -j y get_counts_job.ocs
