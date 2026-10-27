#!/bin/bash
set -euo pipefail
# The key comes from the cluster's MUNGE volume; LSF's head node creates it only when it starts
until [ -f /etc/munge/munge.key ]; do sleep 2; done
install -d -o munge -g munge -m 755 /run/munge
runuser -u munge -- /usr/sbin/munged
alembic -c /opt/warden/warden/api/alembic.ini upgrade head
uvicorn warden_mock:app --host 127.0.0.1 --port 8005 &
mock_pid=$!
python -m warden &
warden_pid=$!
trap 'kill "$mock_pid" "$warden_pid"; wait' EXIT
trap 'exit 0' TERM INT
wait -n "$mock_pid" "$warden_pid"
