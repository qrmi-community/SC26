#!/usr/bin/env bash
# Copy Slurm configuration files from this directory into the containers and restart
# the cluster, e.g. ./update_slurmfiles.sh slurm.conf
# This replaces the containers' copy: edits made inside a container are lost.

set -e

# Use the engine that runs the slurmctld container (override with CONTAINER_ENGINE=...)
engine="${CONTAINER_ENGINE:-}"
if [ -z "$engine" ]; then
    if command -v podman >/dev/null 2>&1 && podman container exists slurmctld 2>/dev/null; then
        engine=podman
    elif command -v docker >/dev/null 2>&1; then
        engine=docker
    else
        engine=podman
    fi
fi

restart=false

for var in "$@"
do
    if [ "$var" = "slurmdbd.conf" ] || [ "$var" = "slurm.conf" ] || [ "$var" = "cgroup.conf" ] || [ "$var" = "plugstack.conf" ] || [ "$var" = "gres.conf" ]
    then
        # Written by root into the existing file, which keeps its owner and mode
        "$engine" exec -i slurmctld sh -c "cat > /etc/slurm/$var" < "$var"
        restart=true
    fi
done
if $restart; then "$engine" compose restart; fi
