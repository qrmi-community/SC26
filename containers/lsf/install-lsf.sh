#!/bin/bash
set -e

# LSF_TAR comes from --build-arg. If the image was built without it (for example
# rebuilt by "compose up --build"), use the CE package for this architecture in /shared.
if [ -z "${LSF_TAR}" ]; then
    case "$(uname -m)" in
        aarch64) LSF_TAR="lsfsce10.2.0.15-armv8.tar.Z" ;;
        x86_64)  LSF_TAR="lsfsce10.2.0.15-x86_64.tar.Z" ;;
    esac
fi

echo "$0: Installing LSF CE, LSF_TAR=${LSF_TAR} in /shared"

if [ -z "${LSF_TAR}" ] || [ ! -f "/shared/${LSF_TAR}" ]; then
    echo "ERROR: LSF CE package '${LSF_TAR}' does not exist in /shared"
    exit 1
fi

LSF_DIR="${LSF_TAR%.tar.Z}"

cd /shared

if [ ! -d "/shared/${LSF_DIR}" ];  then
    # Extract CE package
    tar --no-same-owner -xf "${LSF_TAR}"
fi

# Select installer tar based on package type
case "${LSF_TAR}" in
    *armv8.tar.Z)
        INSTALLER_TAR="lsf10.1_no_jre_lsfinstall.tar.Z"
        INSTALLER_DIR="lsf10.1_lsfinstall"
        ;;
    *x86_64.tar.Z)
        INSTALLER_TAR="lsf10.1_lsfinstall_linux_x86_64.tar.Z"
        INSTALLER_DIR="lsf10.1_lsfinstall"
        ;;
    *)
    echo "Unsupported LSF package: ${LSF_TAR}"
        exit 1
        ;;
    esac

cd "${LSF_DIR}/lsf"
if [ ! -d "${INSTALLER_DIR}" ]; then
    echo "Extracting ${INSTALLER_TAR}"
    tar --no-same-owner -xf "${INSTALLER_TAR}"
fi
cd "${INSTALLER_DIR}"
cat > install.config <<EOF
LSF_TOP="/opt/lsfce"
LSF_ADMINS="lsfuser"
LSF_CLUSTER_NAME="cluster1"
LSF_MASTER_LIST="lsf-head compute01 compute02"
LSF_TARDIR="/shared/${LSF_DIR}/lsf/"
EOF

echo 1 | ./lsfinstall -f install.config

chown -R lsfuser:lsfuser /opt/lsfce
