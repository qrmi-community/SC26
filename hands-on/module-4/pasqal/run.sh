#!/bin/bash
# Sampling job (quantum), then the MPI job, which runs only if sampling succeeded.
# Pass the resource request, e.g.: bash run.sh --qpu=PASQAL_LOCAL --licenses=pasqal_local@slurmdb:1
set -euo pipefail
rm -f input.bin output.json get_counts.log  # so a failed run leaves nothing from an earlier run
mpicxx -O2 -o get_counts get_counts.cpp
jobidA=$(sbatch --parsable -o sampling.log "$@" run_sampler.sh)
jobidA=${jobidA%%;*}
sbatch -W -o get_counts.log --kill-on-invalid-dep=yes --dependency=afterok:"$jobidA" get_counts_job.sh
# sbatch -W also returns 0 when Slurm cancels the MPI job because sampling failed
[ "$(sacct -n -X -P -o State -j "$jobidA")" = COMPLETED ] || { echo "Sampling job $jobidA failed; see sampling.log" >&2; exit 1; }
