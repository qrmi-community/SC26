#!/bin/bash
set -e

CONFDIR="/opt/lsfce/conf"

echo "$0: Configure lsf.conf to disable eauth and to use ssh instead of rsh"
cp ${CONFDIR}/lsf.conf ${CONFDIR}/lsf.conf.orig
sed "s/^LSF_AUTH=eauth$/LSF_AUTH=none/g" ${CONFDIR}/lsf.conf > /tmp/lsf.conf
cp /tmp/lsf.conf ${CONFDIR}/lsf.conf
cat >> ${CONFDIR}/lsf.conf <<EOF
LSF_REMOTE_COPY="scp -B"
LSF_RSH="ssh"
EOF

echo "$0: Configure lsb.hosts to not allow any jobs to run on lsf-head"
# Alternately, can specify HOSTS in ${CONFDIR}/lsbatch/cluster1/configdir/lsb.queues
cp ${CONFDIR}/lsbatch/cluster1/configdir/lsb.hosts ${CONFDIR}/lsbatch/cluster1/configdir/lsb.hosts.orig
sed "s/^End Host$/lsf-head   0    ()      ()    ()     ()     ()            (Y)\nEnd Host/g" ${CONFDIR}/lsbatch/cluster1/configdir/lsb.hosts > /tmp/lsb.hosts
cp /tmp/lsb.hosts ${CONFDIR}/lsbatch/cluster1/configdir/lsb.hosts

