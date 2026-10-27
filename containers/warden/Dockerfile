# Warden with a simulated QPU, for Pasqal Local. Shared by all scheduler tracks.
# The image has no MUNGE key: compose mounts the cluster's MUNGE volume, which the head node fills
# first. dnf creates the munge account; on this base image it gets UID/GID 998, as in the cluster images.
FROM docker.io/library/rockylinux:9
ARG WARDEN_REF=7e4ea4e3194692e492a2a108535b9b71f2d90bdf
RUN dnf install -y munge python3.12 && dnf clean all
RUN mkdir -p /opt/warden /var/lib/warden \
 && curl -fsSL "https://github.com/pasqal-io/warden/archive/${WARDEN_REF}.tar.gz" \
    | tar xz --strip-components=1 -C /opt/warden \
 && python3.12 -m venv /opt/warden-env \
 && /opt/warden-env/bin/pip install --no-deps --require-hashes -r /opt/warden/requirements.txt \
 && /opt/warden-env/bin/pip install --no-deps /opt/warden \
 && /opt/warden-env/bin/pip check
COPY warden-entrypoint.sh warden_mock.py /opt/warden/
RUN printf '%s\n' \
    'api: {port: 4207, admin_users: ["0"]}' \
    'database: {backend: sqlite, name: /var/lib/warden/warden.db}' \
    'qpu: {uri: "http://127.0.0.1:8005"}' \
    > /opt/warden/config.yaml
ENV PATH=/opt/warden-env/bin:$PATH \
    PYTHONPATH=/opt/warden/tests:/opt/warden \
    MOCK_QPU_API_EMUL=1 \
    MOCK_QPU_API_SHOT_DURATION_S=0.001
WORKDIR /opt/warden
ENTRYPOINT ["bash", "/opt/warden/warden-entrypoint.sh"]
