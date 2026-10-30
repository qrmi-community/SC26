LSF Community Edition for the tutorial can be downloaded through a web browser using the links below. The files are password protected. Contact Yoonho Park (yoonho@us.ibm.com) or Munetaka Ohtani (ohtanim@jp.ibm.com) for the password.

* x86_64 processor (amd64): https://ibm.box.com/s/2em7lrbtf50alqtkx7k2d4dcejc7m4uk
* Apple silicon (arm64): https://ibm.box.com/s/ncwzht2tij1lww9n77rkfihham1yv60l

The x86_64 processor LSF should be placed in `containers/lsf/shared/` (mounted as `/shared` in the containers) with the name `lsfsce10.2.0.15-x86_64.tar.Z`. The Apple silicon LSF should be placed in the same directory with the name `lsfsce10.2.0.15-armv8.tar.Z`. Use `tar ztf <filename>` to check the contents.

The MPICH installation can also be downloaded through a web browser using the links below to avoid the MPICH build (perhaps the longest step).

* x86_64 processor (amd64): https://ibm.box.com/s/m86y7cefyc7mmb3apavohmshfm0szg55
* Apple silicon (arm64): https://ibm.box.com/s/t6haxng4xskdzj1tygoo92so67let7t2

The x86_64 processor MPICH should be placed in `containers/lsf/shared/` (mounted as `/shared` in the containers) with the name `mpich-4.2.3-x86_64-install.tgz`. The Apple silicon MPICH should be placed in the same directory with the name `mpich-4.2.3-aarch64-install.tgz`. Use `tar ztf <filename>` to check the contents.
