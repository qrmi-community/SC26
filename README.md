# Resources for SC26 Tutorial: Workload-Manager-Agnostic QPU Integration with QRMI(tut171)

## Abstract

Integrating quantum resources into HPC workflows is complicated by two layers of fragmentation: quantum hardware vendors expose incompatible APIs, and HPC centers run diverse job schedulers. The Quantum Resource Management Interface (QRMI), an open-source project developed by a growing community of 15 national laboratories, institutions, and quantum vendors, resolves both problems by exposing quantum resources as first-class schedulable resources alongside CPUs and GPUs, independent of vendor or scheduler. This hands-on, three-hour tutorial targets HPC engineers and administrators, and gives quantum vendors concrete motivation: implement QRMI once, and your backend becomes accessible from any scheduler. 

The tutorial spans three modules covering today's HPC scheduling landscape: traditional batch schedulers, where attendees choose one of Slurm, PBS, IBM LSF, or Open Cluster Scheduler for hands-on exercises; Kubernetes, increasingly adopted for AI workloads; and the Flux Framework, a graph-based scheduler for next-generation HPC systems. In each module, participants submit real QRMI-managed jobs targeting cloud quantum resources from providers such as IBM, Pasqal, and Alice & Bob. Attendees will leave having experienced firsthand how QRMI integrates with their own workload manager to deliver quantum workloads to HPC users, giving them a concrete starting point for building quantum-ready HPC infrastructure today.

## Presenters

### Munetaka Ohtani (IBM)

Email: ohtanim@jp.ibm.com

Munetaka Ohtani is a Senior Software Engineer at IBM Quantum, specializing in distributed systems such as
Hadoop, enterprise software, cloud computing, and HPC (high-performance computing) software development.
Since 2021, he has focused on quantum-computing infrastructure software and quantum-centric supercomputing.
His work includes software development, including simulators, for integrating IBM Quantum System Two,
deployed at national laboratory HPC data centers, with HPC infrastructure; R&D on integrating quantum
computers with HPC schedulers; and building observability infrastructure for quantum systems, including the
definition of key metrics. Since 2025, he has been organizing the open-source QRMI (Quantum Resource
Management Interface) project, which he launched to provide a unified interface for integrating heterogeneous
QPU backends into HPC schedulers such as Slurm and PBS. He currently serves as the QRMI maintainer. He
has also delivered a related tutorial at SCA/HPC Asia 2026, introducing QRMI-based quantum-HPC integration to
quantum vendors and HPC communities.

### Aleksander Wennersteen (Pasqal)

Email: aleksander.wennersteen@pasqal.com

Aleksander Wennersteen is the Technical Lead for Quantum-Centric HPC at Pasqal,where he focuses on
integrating quantum processors with classical HPC systems and enabling portable hybrid quantum-classical
workflows. His work spans resource management, runtime systems, scheduling, observability, and execution
environments for cloud and on-premises quantum-HPC platforms. He is one of the core maintainers of the
Quantum Resource Management Interface (QRMI) and its integration with HPC resource managers. Previously
at Pasqal, he worked as a quantum software engineer and technical lead on quantum libraries, cloud platform
software, and numerical simulation of quantum systems. He holds a master’s degree in Mathematical Physics
from the University of Edinburgh. Before joining Pasqal, he worked in high-performance computing and artificial
intelligence.

### Yoonho Park (IBM)

Email: yoonho@us.ibm.com

Yoonho Park is a Principal Research Scientist at IBM Quantum with experience in operating systems, distributed
systems, HPC, and cloud infrastructure. He led the IBM Research software teams during the delivery of the
CORAL supercomputers, Summit and Sierra. He then led the delivery of on-premise AI cloud to IBM Research
partners. He is currently focused on workload management to support quantum-classical workflows on Quantum-
Centric Supercomputers. He has integrated QPU backends into HPC schedulers such as LSF and Flux.

### Kevin Kissell (Alice & Bob)

Email: kevin.kissell@alice-bob.com

Kevin D. Kissell is a senior technical and commercial advisor to Alice & Bob, helping turn their cat qubit
technology into deliverable and useful scientific computing power. He has been engaged in leading-edge
computer architecture for over 47 years. At Google, he developed interconnect architectures and accelerator
virtualization schemes, before joining their office of the CTO, where he led Google Cloud’s initiatives in HPC and
quantum computing. Before Google, his work in hardware and software architecture ranged from supercomputers
to smart cards: Decoupled access/execute supercomputers at ACRI, massively parallel distributed memory
computers at nCUBE, large-scale shared-memory supercomputers at Evans & Sutherland, and, at the opposite
extreme, embedded architectures for cybersecurity and multi-threaded I/O processing, for MIPS Technologies.
He holds sixty-odd patents in computer architecture and a degree in computer science from the University of
California at Berkeley.

### Jamie Machin (Alice & Bob)

Email: jamie.machin@alice-bob.com

Jamie Machin is a Software Engineer at Alice and Bob, focusing on DevOps and development in the context of
Alice and Bob's cloud stack, Felis. He has experience working on both public and private cloud platforms, builidng
out infrastructure for large scale operations. He has integrated Alice and Bob QPUs into the QRMI project.

## References
- [QRMI](https://github.com/qiskit-community/qrmi)
