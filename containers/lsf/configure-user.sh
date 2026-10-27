#!/bin/bash
set -e

CONFDIR="/opt/lsfce/conf"

echo "$0: Copy the MPI examples to lsfuser's home"
cp -r /distribution/examples /home/lsfuser
chown -R lsfuser:lsfuser /home/lsfuser/examples

echo "$0: Configure lsfuser to source profile.lsf in .bashrc"
cat >> /home/lsfuser/.bashrc <<EOF

# LSF and MPICH
if [ -f /opt/lsfce/conf/profile.lsf ]; then . /opt/lsfce/conf/profile.lsf; fi
export PATH=/opt/mpich/bin:\$PATH
export LD_LIBRARY_PATH=/opt/mpich/lib:\$LD_LIBRARY_PATH
EOF
