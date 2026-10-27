LSF Community Edition for the tutorial can be downloaded from the following links:

* x86_64 processor (amd64): https://ibm.box.com/shared/static/9syiqq6f6casj3yvfm6yby71fcpvm3qy.z
* Apple silicon (arm64): https://ibm.box.com/shared/static/oxckd0zb3i00m09q39jx8dthwef7vjqe.z

The x86_64 processor LSF should be placed in `containers/lsf/shared/` (mounted as `/shared` in the containers) with the name `lsfsce10.2.0.15-x86_64.tar.Z`. The Apple silicon LSF should be placed in the same directory with the name `lsfsce10.2.0.15-armv8.tar.Z`. We recommend using a tool such as wget as follows:

* `wget -O lsfsce10.2.0.15-x86_64.tar.Z https://ibm.box.com/shared/static/9syiqq6f6casj3yvfm6yby71fcpvm3qy.z`
* `wget -O lsfsce10.2.0.15-armv8.tar.Z  https://ibm.box.com/shared/static/oxckd0zb3i00m09q39jx8dthwef7vjqe.z`

If the URL is a Box share link (`https://ibm.box.com/s/<id>`), `wget` saves the Box web page instead of the archive. Use the direct-download form `https://ibm.box.com/shared/static/<id>` instead, and check the result with `gzip -t <archive>`.

The MPICH installation can also be downloaded from the following links to avoid the MPICH build (perhaps the longest step):

* x86_64 processor (amd64): https://ibm.box.com/shared/static/kn4w0izhtxuomae9wmfmwcqz21z40vk8.tgz
* Apple silicon (arm64): https://ibm.box.com/shared/static/ckwu2r3070acc6q4xeyumv7tukksb1mt.tgz

The x86_64 processor MPICH should be placed in `containers/lsf/shared/` (mounted as `/shared` in the containers) with the name `mpich-4.2.3-x86_64-install.tgz`. The Apple silicon MPICH should be placed in the same directory with the name `mpich-4.2.3-aarch64-install.tgz`. The `wget` commands are as follows:

* `wget -O mpich-4.2.3-x86_64-install.tgz https://ibm.box.com/shared/static/kn4w0izhtxuomae9wmfmwcqz21z40vk8.tgz`
* `wget -O mpich-4.2.3-aarch64-install.tgz https://ibm.box.com/shared/static/ckwu2r3070acc6q4xeyumv7tukksb1mt.tgz`
