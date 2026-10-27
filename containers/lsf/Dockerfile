FROM ubuntu:24.04

ARG LSF_TAR
ENV LSF_TAR=${LSF_TAR}

ENV DEBIAN_FRONTEND=noninteractive

# MUNGE authenticates Pasqal Local users to Warden. The munge account gets the same
# UID/GID (998) as in the Warden image, which shares this cluster's key (compose.warden.yaml).
RUN groupadd -r -g 998 munge && \
    useradd -r -u 998 -g 998 -d /nonexistent -s /usr/sbin/nologin munge

RUN apt-get update && \
    apt-get install -y \
        openssh-server \
        openssh-client \
        sudo \
        vim \
        curl \
        wget \
        rsync \
        net-tools \
        iproute2 \
        iputils-ping \
        procps \
        python3 \
        python3-pip \
        python3-venv \
        default-jre \
        ed \
        munge \
        less && \
    rm -rf /var/lib/apt/lists/* && \
    rm -f /etc/munge/munge.key

RUN mkdir -p /var/run/sshd
RUN ssh-keygen -A

RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config

RUN echo "    StrictHostKeyChecking no" >> /etc/ssh/ssh_config && \
    echo "    UserKnownHostsFile /dev/null" >> /etc/ssh/ssh_config

# Create lsfuser with explicit UID/GID 1002
RUN groupadd -g 1002 lsfuser && \
    useradd -u 1002 -g 1002 -m -s /bin/bash lsfuser
RUN echo 'lsfuser ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/lsfuser \
 && chmod 440 /etc/sudoers.d/lsfuser

RUN echo "root:root" | chpasswd

# Login shells load LSF and MPICH settings (works on every node, independent of /home)
RUN echo 'if [ -f /opt/lsfce/conf/profile.lsf ]; then . /opt/lsfce/conf/profile.lsf; fi' > /etc/profile.d/lsf.sh && \
    printf '%s\n' 'export PATH=/opt/mpich/bin:$PATH' 'export LD_LIBRARY_PATH=/opt/mpich/lib:$LD_LIBRARY_PATH' > /etc/profile.d/mpich.sh

COPY entrypoint.sh /usr/local/bin
COPY install-lsf.sh /usr/local/bin
COPY install-mpich.sh /usr/local/bin
COPY configure-lsf.sh /usr/local/bin
COPY configure-user.sh /usr/local/bin

# Scripts saved with Windows line endings (CRLF) would not run
RUN sed -i 's/\r$//' /usr/local/bin/*.sh && chmod +x \
    /usr/local/bin/entrypoint.sh \
    /usr/local/bin/install-lsf.sh \
    /usr/local/bin/install-mpich.sh \
    /usr/local/bin/configure-lsf.sh \
    /usr/local/bin/configure-user.sh

COPY examples/ /distribution/examples/

CMD ["/usr/local/bin/entrypoint.sh"]
