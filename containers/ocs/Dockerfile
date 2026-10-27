# Image for the Open Cluster Scheduler cluster (shared by the master and the execution nodes;
# the role is selected at runtime with OCS_ROLE)
# - Rocky Linux 9, natively on arm64 (Apple silicon) or x86_64
# - The OCS binaries are unpacked into /opt/ocs at build time; /opt/ocs is a volume shared by
#   all nodes, and the cell directory /opt/ocs/default is created by the master at its first start

FROM docker.io/library/rockylinux:9

ENV LANG=C.UTF-8

# --- Runtime dependencies --------------------------------------------------
RUN dnf install -y dnf-plugins-core epel-release \
 && dnf config-manager --set-enabled crb \
 && dnf install -y \
      gcc gcc-c++ make perl hwloc-libs libtirpc munge munge-devel \
      python3.12 python3.12-devel python3.12-pip \
      sudo procps-ng which hostname findutils binutils tar gzip \
 && dnf clean all

# --- Download and unpack Open Cluster Scheduler ----------------------------
# Releases are published at https://open.clusterscheduler.io/ (versioned URLs, no login).
# To use another release, override the version at build time, e.g.
#   docker compose build --build-arg OCS_VERSION=<version>
# Releases from 9.1.6 on are published there; they also recognize Linux kernel 7.x in util/arch
# (containers report the host kernel, and 9.1.0 printed UNSUPPORTED-<release>lx-<cpu> there).
# inst_sge runs without -munge and -tls: OCS uses its default authentication, and MUNGE
# is only used by QRMI and Warden.
ARG OCS_VERSION=9.1.7
# filestat reports the owner of a file; it fails on overlay/user-namespace file systems,
# so it is replaced with a stub that always reports root (same fix as the OCS quickinstall).
# inst_sge installs SysV rc scripts; their directories are missing on Rocky Linux 9.
RUN set -euxo pipefail \
 && case "$(uname -m)" in \
      x86_64)  bin=bin-lx-amd64 ;; \
      aarch64) bin=bin-lx-arm64 ;; \
      *) echo "unsupported architecture: $(uname -m)"; exit 1 ;; \
    esac \
 && mkdir -p /opt/ocs \
 && for pkg in "$bin" common; do \
      curl -fsSL "https://open.clusterscheduler.io/download/ocs-${OCS_VERSION}/ocs-${OCS_VERSION}-${pkg}.tar.gz" | tar xzpf - -C /opt/ocs ; \
    done \
 && echo "$OCS_VERSION" > /opt/ocs/OCS_VERSION \
 && arch="$(/opt/ocs/util/arch)" \
 && test -d "/opt/ocs/utilbin/${arch}" \
 && printf '#!/bin/sh\necho root\n' > "/opt/ocs/utilbin/${arch}/filestat" \
 && chmod 755 "/opt/ocs/utilbin/${arch}/filestat" \
 && mkdir -p /etc/rc.d/rc3.d /etc/rc.d/init.d

# --- Open MPI with Grid Engine support --------------------------------------
# --with-sge enables the gridengine ras component:
#   - mpirun picks up the allocation in $PE_HOSTFILE automatically
#   - inside an OCS job, the rsh launcher starts processes on other nodes with "qrsh -inherit", not ssh
#   - requires a parallel environment with control_slaves TRUE (created by the entrypoint)
ARG OPENMPI_VERSION=4.1.8
ADD https://download.open-mpi.org/release/open-mpi/v4.1/openmpi-${OPENMPI_VERSION}.tar.gz /build-ompi/openmpi.tar.gz
RUN set -euxo pipefail \
 && cd /build-ompi \
 && tar xzf openmpi.tar.gz --strip-components=1 \
 && ./configure --prefix=/opt/openmpi \
                --with-sge \
                --enable-mpirun-prefix-by-default \
 && make -j"$(nproc)" \
 && make install \
 && cd / && rm -rf /build-ompi \
 && echo /opt/openmpi/lib > /etc/ld.so.conf.d/openmpi.conf && ldconfig \
 && /opt/openmpi/bin/ompi_info | grep 'MCA ras: gridengine'

# Make Open MPI and OCS available in jobs (login shells) as well
# btl_vader_single_copy_mechanism=none : CMA (ptrace) is not available in containers and causes errors
RUN printf '%s\n' \
      'export PATH=/opt/openmpi/bin:$PATH' \
      'export MANPATH=/opt/openmpi/share/man:${MANPATH:-}' \
      'export OMPI_MCA_btl_vader_single_copy_mechanism=none' \
      > /etc/profile.d/openmpi.sh \
 && printf '%s\n' \
      '[ -f /opt/ocs/default/common/settings.sh ] && . /opt/ocs/default/common/settings.sh' \
      > /etc/profile.d/ocs.sh
ENV PATH=/opt/openmpi/bin:$PATH \
    OMPI_MCA_btl_vader_single_copy_mechanism=none

# python3 is Python 3.12, as in the Slurm containers (dnf keeps using its own platform-python)
RUN alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 \
 && python3.12 -m pip install --no-cache-dir Cython pytest

# mpi4py for python3.12, built against the Open MPI above, installed system-wide
ARG INSTALL_MPI4PY=1
RUN if [ "$INSTALL_MPI4PY" = 1 ]; then \
      MPICC=/opt/openmpi/bin/mpicc python3.12 -m pip install --no-cache-dir mpi4py ; \
    fi

# Extra Python packages (e.g. QRMI) are installed into python3.12 here
#   e.g. docker compose build --build-arg PIP_PACKAGES="qrmi"
ARG PIP_PACKAGES=""
RUN if [ -n "$PIP_PACKAGES" ]; then python3.12 -m pip install --no-cache-dir $PIP_PACKAGES; fi

# Regular user for submitting jobs
RUN useradd -m -u 1000 ocsuser

# MUNGE authentication, used by QRMI for Pasqal Local (Warden). The key is created here and
# shared by all nodes through the ocs-munge volume (same setup as the Slurm containers)
RUN /sbin/create-munge-key

# Example QRMI configuration; Module 1 installs the configuration the prolog/epilog read as /opt/ocs/qrmi-config.json
# and QRMI Load Sensor configuration (/etc/qrmi-ocs-load-sensor.yaml)
COPY qrmi_config.json.example /etc/qrmi/qrmi_config.json.example
COPY qrmi-ocs-load-sensor.yaml.example /etc/qrmi-ocs-load-sensor.yaml.example

# Allow ocsuser to use sudo without a password (for a local test cluster only; do not use in production)
RUN echo 'ocsuser ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/ocsuser \
 && chmod 440 /etc/sudoers.d/ocsuser

# --- Development and debugging tools (same set as the OpenPBS containers) ---
# plus the toolchain for the QRMI OCS hooks (hpc-gridware/qpu-resource):
#   golang, and openssl-devel / pkgconf-pkg-config for building libqrmi with cargo
RUN dnf install -y \
      golang openssl-devel pkgconf-pkg-config \
      vim-enhanced bash-completion jq less \
      gdb valgrind strace \
      iputils net-tools iproute bind-utils \
      psmisc \
      wget git bzip2 gnupg2 cmake flex clang-tools-extra \
      openblas-devel \
      dos2unix \
 && dnf clean all

# --- Rust toolchain (rustup), shared by all users under /opt/rust ------------
ENV RUSTUP_HOME=/opt/rust/rustup
RUN export CARGO_HOME=/opt/rust/cargo \
 && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --no-modify-path \
 && chmod -R a+rX /opt/rust \
 && /opt/rust/cargo/bin/rustc --version \
 && printf '%s\n' \
      'export RUSTUP_HOME=/opt/rust/rustup' \
      'export PATH=/opt/rust/cargo/bin:$PATH' \
      > /etc/profile.d/rust.sh
ENV PATH=/opt/rust/cargo/bin:$PATH

# --- Entrypoint --------------------------------------------------------------
# The trailing CR (\r) is removed in case the file was edited on Windows
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN sed -i 's/\r$//' /usr/local/bin/entrypoint.sh \
 && chmod 755 /usr/local/bin/entrypoint.sh

WORKDIR /shared
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
