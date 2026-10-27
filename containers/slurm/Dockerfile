FROM rockylinux:9

LABEL org.opencontainers.image.source="https://github.com/giovtorres/slurm-docker-cluster" \
      org.opencontainers.image.title="slurm-docker-cluster" \
      org.opencontainers.image.description="Slurm Docker cluster on Rocky Linux 9" \
      org.label-schema.docker.cmd="docker-compose up -d" \
      maintainer="Giovanni Torres"

RUN set -ex \
    && yum makecache \
    && yum -y update \
    && yum -y install dnf-plugins-core \
    && yum config-manager --set-enabled crb \
    && yum -y install \
       wget \
       bzip2 \
       perl \
       gcc \
       gcc-c++ \
       gdb \
       git \
       gnupg \
       make \
       munge \
       munge-devel \
       python3.12-devel \
       python3.12-pip \
       mariadb-server \
       mariadb-devel \
       psmisc \
       bash-completion \
       vim-enhanced \
       http-parser-devel \
       json-c-devel \
       cmake \
       clang-tools-extra \
       procps \
       iputils \
       net-tools \
       openblas-devel \
       jq \
       libyaml-devel \
       lua-devel \
       autoconf \
       libtool \
       flex \
       libevent-devel \
       hwloc-devel \
       valgrind \
    && yum clean all \
    && rm -rf /var/cache/yum

RUN alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1

RUN pip3.12 install Cython pytest

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

ARG GOSU_VERSION=1.17

RUN set -ex \
    && arch="$(uname -m | sed -e s/x86_64/amd64/ -e s/aarch64/arm64/)" \
    && wget -O /usr/local/bin/gosu "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$arch" \
    && wget -O /usr/local/bin/gosu.asc "https://github.com/tianon/gosu/releases/download/$GOSU_VERSION/gosu-$arch.asc" \
    && export GNUPGHOME="$(mktemp -d)" \
    && gpg --batch --keyserver hkps://keys.openpgp.org --recv-keys B42F6819007F00F88E364FD4036A9C25BF357DD4 \
    && gpg --batch --verify /usr/local/bin/gosu.asc /usr/local/bin/gosu \
    && rm -rf "${GNUPGHOME}" /usr/local/bin/gosu.asc \
    && chmod +x /usr/local/bin/gosu \
    && gosu nobody true

ARG OPENPMIx_VERSION=4.1.3

RUN set -euxo pipefail \
    && wget -nv -O pmix-${OPENPMIx_VERSION}.tar.gz https://github.com/openpmix/openpmix/releases/download/v${OPENPMIx_VERSION}/pmix-${OPENPMIx_VERSION}.tar.gz \
    && tar -xvf pmix-${OPENPMIx_VERSION}.tar.gz \
    && pushd pmix-${OPENPMIx_VERSION} \
    && ./configure --prefix=/usr/local/pmix-${OPENPMIx_VERSION} \
    && make all install \
    && popd

ARG SLURM_TAG

RUN set -x \
    && git clone -b ${SLURM_TAG} --single-branch --depth=1 https://github.com/SchedMD/slurm.git \
    && pushd slurm \
    && ./configure --enable-debug --prefix=/usr --sysconfdir=/etc/slurm \
        --with-mysql_config=/usr/bin  --libdir=/usr/lib64 \
        --with-pmix=/usr/local/pmix-${OPENPMIx_VERSION} \
    && make install \
    && install -D -m644 etc/cgroup.conf.example /etc/slurm/cgroup.conf.example \
    && install -D -m644 etc/slurm.conf.example /etc/slurm/slurm.conf.example \
    && install -D -m644 etc/slurmdbd.conf.example /etc/slurm/slurmdbd.conf.example \
    && install -D -m644 contribs/slurm_completion_help/slurm_completion.sh /etc/bash_completion.d/slurm_completion.sh \
    && popd \
    && groupadd -r --gid=990 slurm \
    && useradd -r -g slurm --uid=990 slurm \
    && mkdir /etc/sysconfig/slurm \
        /var/spool/slurmd \
        /var/run/slurmd \
        /var/run/slurmdbd \
        /var/lib/slurmd \
        /var/log/slurm \
        /data \
    && touch /var/lib/slurmd/node_state \
        /var/lib/slurmd/front_end_state \
        /var/lib/slurmd/job_state \
        /var/lib/slurmd/resv_state \
        /var/lib/slurmd/trigger_state \
        /var/lib/slurmd/assoc_mgr_state \
        /var/lib/slurmd/assoc_usage \
        /var/lib/slurmd/qos_usage \
        /var/lib/slurmd/fed_mgr_state \
    && chown -R slurm:slurm /var/*/slurm* \
    && /sbin/create-munge-key

ARG OPENMPI_VERSION=4.1.8

RUN set -euxo pipefail \
    && wget -nv -O openmpi-${OPENMPI_VERSION}.tar.gz https://download.open-mpi.org/release/open-mpi/v4.1/openmpi-${OPENMPI_VERSION}.tar.gz \
    && tar -xvf openmpi-${OPENMPI_VERSION}.tar.gz \
    && pushd openmpi-${OPENMPI_VERSION} \
    && ./configure --with-slurm --with-pmix="/usr/local/pmix-${OPENPMIx_VERSION}" --prefix="/usr/local/openmpi/${OPENMPI_VERSION}-pmix" \
    && make -j"$(nproc)" \
    && make install \
    && popd

ENV PATH="${PATH}:/usr/local/openmpi/${OPENMPI_VERSION}-pmix/bin" \
    LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:/usr/local/openmpi/${OPENMPI_VERSION}-pmix/lib"

COPY slurm.conf /etc/slurm/slurm.conf
COPY slurmdbd.conf /etc/slurm/slurmdbd.conf
COPY cgroup.conf /etc/slurm/cgroup.conf
COPY plugstack.conf.example /etc/slurm/plugstack.conf.example
COPY qrmi_config.json.example /etc/slurm/qrmi_config.json.example
RUN set -x \
    && chown slurm:slurm /etc/slurm/slurmdbd.conf \
    && chmod 600 /etc/slurm/slurmdbd.conf
RUN python3.12 -m venv ~/venv \
    && source ~/venv/bin/activate \
    && pip install --upgrade pip

ARG USERNAME=user
ARG GROUPNAME=user
ARG UID=1000
ARG GID=1000
RUN groupadd -g $GID $GROUPNAME && \
    useradd -m -s /bin/bash -u $UID -g $GID $USERNAME

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

CMD ["slurmdbd"]
