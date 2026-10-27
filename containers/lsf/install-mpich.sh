#!/bin/bash
set -e

echo "$0: Installing MPICH"

if [[ -f /shared/mpich-4.2.3-$(uname -m)-install.tgz ]]; then
    cd /opt
    tar zxfv /shared/mpich-4.2.3-$(uname -m)-install.tgz
else
    # Build/install MPICH
    cd /shared
    rm -f mpich-4.2.3.tar.gz
    wget -nv https://www.mpich.org/static/downloads/4.2.3/mpich-4.2.3.tar.gz
    tar xzf mpich-4.2.3.tar.gz
    cd mpich-4.2.3
    ./configure --disable-fortran --prefix=/opt/mpich
    make -j 6
    make install
fi

# Configure environment for all users
cat > /etc/profile.d/mpich.sh <<EOF
export PATH=/opt/mpich/bin:\$PATH
export LD_LIBRARY_PATH=/opt/mpich/lib:\$LD_LIBRARY_PATH
EOF

chmod 644 /etc/profile.d/mpich.sh
