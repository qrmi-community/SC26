#!/bin/bash
# Print Warden's most recent sessions with their tasks (run on the host).
# Warden records the scheduler's job ID in a column named slurm_job_id for every scheduler.
# Uses Docker, or Podman if Docker does not run the warden container; CONTAINER_ENGINE overrides.
set -euo pipefail
engine=${CONTAINER_ENGINE:-}
if [ -z "$engine" ]; then
    if command -v docker >/dev/null 2>&1 && docker container inspect warden >/dev/null 2>&1; then
        engine=docker
    else
        engine=podman
    fi
fi
"$engine" exec -i warden python3.12 - "${1:-5}" <<'EOF'
import sqlite3
import sys

db = sqlite3.connect("/var/lib/warden/warden.db")
rows = db.execute(
    """
    select s.slurm_job_id, s.user_id, substr(s.id, 1, 8), s.created_at, s.revoked_at,
           j.id, j.status, j.shots, j.canceled_at
    from sessions s left join jobs j on j.session_id = s.id
    where s.id in (select id from sessions order by created_at desc limit ?)
    order by s.created_at, j.id
    """,
    (int(sys.argv[1]),),
)
print(f"{'sched. job':<14}{'uid':<6}{'session':<10}{'opened':<21}{'revoked':<21}{'task':<6}{'status':<10}{'shots':<7}canceled")
for job, uid, sid, opened, revoked, task, status, shots, canceled in rows:
    print(
        f"{job:<14}{uid:<6}{sid:<10}{opened[:19]:<21}{(revoked or '-')[:19]:<21}"
        f"{task or '-':<6}{status or '-':<10}{shots or '-':<7}{(canceled or '-')[:19]}"
    )
EOF
