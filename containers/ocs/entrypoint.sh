#!/bin/bash
# Entrypoint for the Open Cluster Scheduler cluster
#   OCS_ROLE=master : sge_qmaster (does not run jobs); installs the cell on the first start
#   OCS_ROLE=execd  : sge_execd only (execution node); installs itself on the first start
# systemd is not used; the OCS rc scripts in the cell directory are called directly
set -o pipefail

export SGE_ROOT=/opt/ocs SGE_CELL=default
SETTINGS="$SGE_ROOT/$SGE_CELL/common/settings.sh"
HOST="$(uname -n)"
ROLE="${OCS_ROLE:-master}"
MASTER_HOST="${OCS_MASTER_HOST:-ocs-master}"
NODES="${OCS_NODES:-}"

log() { echo "[entrypoint:$ROLE] $*"; }

# On failure, do not exit; keep the container running so it can be inspected with docker exec
hold_for_debug() {
    log "ERROR: $*"
    log "Keeping the container running for inspection:  docker exec -it $HOST bash"
    sleep infinity &
    wait $!
    exit 1
}

# Write the inst_sge auto-installation configuration
write_inst_conf() {  # write_inst_conf EXEC_HOST_LIST
    cat > /tmp/inst_sge.conf <<EOF
SGE_ROOT="$SGE_ROOT"
SGE_QMASTER_PORT="6444"
SGE_EXECD_PORT="6445"
SGE_ENABLE_SMF="false"
SGE_CLUSTER_NAME="ocs"
CELL_NAME="$SGE_CELL"
ADMIN_USER="root"
QMASTER_SPOOL_DIR="$SGE_ROOT/$SGE_CELL/spool/qmaster"
EXECD_SPOOL_DIR="$SGE_ROOT/$SGE_CELL/spool"
GID_RANGE="20000-20100"
SPOOLING_METHOD="classic"
DB_SPOOLING_DIR="$SGE_ROOT/$SGE_CELL/spool/spooldb"
PAR_EXECD_INST_COUNT="20"
ADMIN_HOST_LIST="$MASTER_HOST $NODES"
SUBMIT_HOST_LIST="$MASTER_HOST $NODES"
EXEC_HOST_LIST="$1"
EXECD_SPOOL_DIR_LOCAL=""
HOSTNAME_RESOLVING="true"
SHELL_NAME="ssh"
COPY_COMMAND="scp"
DEFAULT_DOMAIN="none"
ADMIN_MAIL="none"
ADD_TO_RC="false"
SET_FILE_PERMS="true"
RESCHEDULE_JOBS="wait"
SCHEDD_CONF="1"
SHADOW_HOST=""
EXEC_HOST_LIST_RM=""
REMOVE_RC="false"
CSP_RECREATE="true"
CSP_COPY_CERTS="false"
EOF
}

log "hostname=$HOST  master=$MASTER_HOST  OCS $(cat "$SGE_ROOT/OCS_VERSION")"

# Check name resolution (this host, the master, and on the master each execution node)
for h in "$HOST" "$MASTER_HOST" $NODES; do
    getent hosts "$h" >/dev/null || hold_for_debug "cannot resolve hostname: $h"
done

# MUNGE authentication (used by QRMI for Pasqal Local) on every node
install -d -o munge -g munge -m 755 /run/munge
runuser -u munge -- /usr/sbin/munged || hold_for_debug "munged failed to start"

case "$ROLE" in
    master)
        if [ ! -f "$SETTINGS" ]; then
            log "installing the qmaster (first start) ..."
            write_inst_conf ""
            (cd "$SGE_ROOT" && ./inst_sge -m -auto /tmp/inst_sge.conf) \
                || hold_for_debug "qmaster installation failed"
            # shellcheck disable=SC1090
            . "$SETTINGS"
            # Make ocsuser an OCS manager (allows qconf configuration changes without sudo)
            qconf -am ocsuser
            # Parallel environment for Open MPI tight integration (mpirun starts remote
            # processes with "qrsh -inherit"), copied from the built-in "make" PE
            # (control_slaves TRUE, $round_robin) and added to the default queue all.q
            qconf -sp make | sed 's/^pe_name .*/pe_name mpi/' > /tmp/mpi.pe
            qconf -Ap /tmp/mpi.pe
            qconf -aattr queue pe_list mpi all.q
        else
            # shellcheck disable=SC1090
            . "$SETTINGS"
            log "starting the qmaster ..."
            "$SGE_ROOT/$SGE_CELL/common/sgemaster" start || hold_for_debug "sgemaster start failed"
        fi
        stop_ocs() { log "stopping the qmaster ..."; "$SGE_ROOT/$SGE_CELL/common/sgemaster" stop; exit 0; }
        LOG_FILE="$SGE_ROOT/$SGE_CELL/spool/qmaster/messages"
        ;;
    execd)
        # Check each answer once: when all containers restart together, the old qmaster may
        # answer and then shut down, so a second query can fail although the cluster is fine
        log "waiting for the qmaster on $MASTER_HOST ..."
        qmaster_up=
        for _ in $(seq 1 120); do
            [ -f "$SETTINGS" ] && . "$SETTINGS" && qconf -sh 2>/dev/null | grep -qx "$HOST" && qmaster_up=1 && break
            sleep 2
        done
        [ -n "$qmaster_up" ] || hold_for_debug "qmaster is not responding"

        # The spool directory exists once the execd is installed (it is on the shared ocs-root volume);
        # sge_execd itself retries until the qmaster is reachable
        if [ ! -d "$SGE_ROOT/$SGE_CELL/spool/$HOST" ]; then
            log "installing the execd (first start) ..."
            write_inst_conf "$HOST"
            (cd "$SGE_ROOT" && ./inst_sge -x -noremote -auto /tmp/inst_sge.conf) \
                || hold_for_debug "execd installation failed"
        else
            log "starting the execd ..."
            "$SGE_ROOT/$SGE_CELL/common/sgeexecd" start || hold_for_debug "sgeexecd start failed"
        fi
        stop_ocs() { log "stopping the execd ..."; "$SGE_ROOT/$SGE_CELL/common/sgeexecd" stop; exit 0; }
        LOG_FILE="$SGE_ROOT/$SGE_CELL/spool/$HOST/messages"
        ;;
    *)
        hold_for_debug "OCS_ROLE must be 'master' or 'execd' (got: $ROLE)"
        ;;
esac

trap stop_ocs TERM INT

if [ "$ROLE" = master ]; then
    log "OCS qmaster is up."
else
    pgrep -x sge_execd >/dev/null || hold_for_debug "sge_execd is not running"
    log "sge_execd is up (qmaster: $MASTER_HOST)."
fi

# Follow the log and wait
tail -n 0 -F "$LOG_FILE" 2>/dev/null &
wait $!
