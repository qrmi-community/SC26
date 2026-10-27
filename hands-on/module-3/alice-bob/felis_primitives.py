# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright 2026 Alice and Bob. All Rights Reserved.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Qiskit Sampler V2 for Alice & Bob Felis QRMI resources.

`get_backend(resource)` returns a backend to transpile circuits for the
resource with, and `SamplerV2(resource)` runs the transpiled circuits on it.
qiskit-alice-bob-provider does not provide primitives, so they live here.

Limits from Felis:

- Felis returns counts, not individual shots, so each register's BitArray is
  rebuilt from counts: the order of its shots is not meaningful.
- Felis takes one shot count per task, so every parameter set of a pub is run
  as its own task, all with the pub's shot count.
"""

import json
import time
from collections import defaultdict
from dataclasses import dataclass, field

import numpy as np
from qiskit import QuantumCircuit
from qiskit.primitives import (
    BasePrimitiveJob,
    BitArray,
    DataBin,
    PrimitiveResult,
    SamplerPubResult,
)
from qiskit.primitives.base import BaseSamplerV2
from qiskit.primitives.containers.sampler_pub import SamplerPub
from qiskit.providers import JobStatus
from qiskit.providers.jobstatus import JOB_FINAL_STATES
from qiskit_alice_bob_provider.qir import circuit_to_qir
from qiskit_alice_bob_provider.remote.backend import AliceBobRemoteBackend

from qrmi import Payload, QuantumResource, TaskStatus

STATUS_MAP = {
    TaskStatus.Queued: JobStatus.QUEUED,
    TaskStatus.Running: JobStatus.RUNNING,
    TaskStatus.Completed: JobStatus.DONE,
    TaskStatus.Failed: JobStatus.ERROR,
    TaskStatus.Cancelled: JobStatus.CANCELLED,
}


def get_backend(resource: QuantumResource) -> AliceBobRemoteBackend:
    """Return a backend describing the resource's target, for transpilation.

Args:
    resource (QuantumResource): Alice & Bob Felis resource.

Returns:
    (AliceBobRemoteBackend): Backend built from the resource's target description.
"""
    # Built without an API client: it is used only to transpile, never to submit.
    return AliceBobRemoteBackend(None, json.loads(resource.target().value))


def split_registers(counts: dict[str, int], circuit: QuantumCircuit) -> dict[str, dict[str, int]]:
    """Split Felis counts over all classical bits into counts per register.

Args:
    counts (dict[str, int]): Counts keyed by bitstrings over all of the circuit's
        clbits, in Qiskit order (the rightmost character is clbit 0).
    circuit (QuantumCircuit): Circuit the counts were measured from.

Returns:
    (dict[str, dict[str, int]]): Counts for each classical register, by name.
"""
    split = {creg.name: defaultdict(int) for creg in circuit.cregs}
    for key, count in counts.items():
        key = key.zfill(circuit.num_clbits)
        for creg in circuit.cregs:
            bits = "".join(key[-1 - circuit.find_bit(bit).index] for bit in reversed(creg))
            split[creg.name][bits] += count
    return {name: dict(register_counts) for name, register_counts in split.items()}


@dataclass
class Options:
    """Options for :class:`SamplerV2`."""

    default_shots: int = 1024
    """Shots per pub when neither `run` nor the pub sets them."""

    input_params: dict = field(default_factory=dict)
    """Felis input parameters for every task, e.g. `{"averageNbPhotons": 4}`."""

    poll_interval: float = 1.0
    """Seconds between task status checks while waiting for results."""


class FelisSamplerJob(BasePrimitiveJob[PrimitiveResult[SamplerPubResult], JobStatus]):
    """The Felis tasks of one `SamplerV2.run` call, one or more per pub."""

    def __init__(self, resource: QuantumResource, pubs: list[SamplerPub],
                 tasks: list[list[str]], poll_interval: float) -> None:
        super().__init__(tasks[0][0])
        self._resource = resource
        self._pubs = pubs
        self._tasks = tasks
        self._poll_interval = poll_interval
        self._statuses: dict[str, TaskStatus] = {}
        self._result = None

    @property
    def task_ids(self) -> list[str]:
        """The Felis job IDs of every task, in submission order."""
        return [task for pub_tasks in self._tasks for task in pub_tasks]

    def _task_status(self, task: str) -> TaskStatus:
        # A task in a final state is not polled again.
        if STATUS_MAP.get(self._statuses.get(task)) not in JOB_FINAL_STATES:
            self._statuses[task] = self._resource.task_status(task)
        return self._statuses[task]

    def status(self) -> JobStatus:
        """Return the job's status, aggregated over its tasks."""
        statuses = [STATUS_MAP[self._task_status(task)] for task in self.task_ids]
        for status in (JobStatus.ERROR, JobStatus.CANCELLED):
            if status in statuses:
                return status
        if all(status == JobStatus.DONE for status in statuses):
            return JobStatus.DONE
        if JobStatus.RUNNING in statuses:
            return JobStatus.RUNNING
        return JobStatus.QUEUED

    def result(self) -> PrimitiveResult[SamplerPubResult]:
        """Wait for every task and return the results, one per pub."""
        if self._result is not None:
            return self._result
        while not self.in_final_state():
            time.sleep(self._poll_interval)
        unsuccessful = [task for task in self.task_ids
                        if STATUS_MAP[self._statuses[task]] != JobStatus.DONE]
        if unsuccessful:
            details = "; ".join(f"{task} ended {self._statuses[task]} (felis job status {task})"
                                for task in unsuccessful)
            raise RuntimeError(f"Felis tasks did not complete: {details}")
        self._result = PrimitiveResult(
            [self._pub_result(pub, tasks) for pub, tasks in zip(self._pubs, self._tasks)],
            metadata={"version": 2},
        )
        return self._result

    def _pub_result(self, pub: SamplerPub, tasks: list[str]) -> SamplerPubResult:
        splits = [split_registers(_parse_counts(self._resource.task_result(task).value), pub.circuit)
                  for task in tasks]
        data = {
            creg.name: BitArray.from_counts([split[creg.name] for split in splits],
                                            num_bits=creg.size).reshape(pub.shape)
            for creg in pub.circuit.cregs
        }
        return SamplerPubResult(DataBin(**data, shape=pub.shape),
                                metadata={"shots": pub.shots, "task_ids": tasks})

    def cancel(self) -> None:
        """Cancel every task."""
        for task in self.task_ids:
            self._resource.task_stop(task)

    def done(self) -> bool:
        return self.status() == JobStatus.DONE

    def running(self) -> bool:
        return self.status() == JobStatus.RUNNING

    def cancelled(self) -> bool:
        return self.status() == JobStatus.CANCELLED

    def errored(self) -> bool:
        return self.status() == JobStatus.ERROR

    def in_final_state(self) -> bool:
        return self.status() in JOB_FINAL_STATES


class SamplerV2(BaseSamplerV2):
    """Sampler V2 that runs circuits on an Alice & Bob Felis QRMI resource.

    Circuits must already be transpiled for the resource, for example with
    `transpile(circuit, get_backend(resource))`: they are converted to QIR as
    they are.
    """

    def __init__(self, resource: QuantumResource, *, options: dict | None = None) -> None:
        self._resource = resource
        self._options = Options(**options) if options else Options()

    def run(self, pubs, *, shots: int | None = None) -> FelisSamplerJob:
        if shots is None:
            shots = self._options.default_shots
        coerced = [SamplerPub.coerce(pub, shots) for pub in pubs]
        for pub in coerced:
            if not pub.circuit.cregs:
                raise ValueError(f"circuit {pub.circuit.name!r} has no classical registers to sample")
        tasks: list[list[str]] = []
        try:
            for pub in coerced:
                tasks.append([])
                input_params = json.dumps({**self._options.input_params, "nbShots": pub.shots})
                for loc in np.ndindex(pub.shape):
                    circuit = pub.parameter_values.bind(pub.circuit, loc)
                    payload = Payload.AliceBobFelis(human_qir=circuit_to_qir(circuit),
                                                    input_params=input_params)
                    tasks[-1].append(self._resource.task_start(payload))
        except BaseException:
            # Don't leave tasks running for a run() that never returned a job.
            for task in (task for pub_tasks in tasks for task in pub_tasks):
                self._resource.task_stop(task)
            raise
        return FelisSamplerJob(self._resource, coerced, tasks, self._options.poll_interval)


def _parse_counts(output: str) -> dict[str, int]:
    """Parse Felis's result, one `<bitstring>,<count>` row per outcome."""
    return {bits: int(count) for bits, count in
            (line.split(",") for line in output.splitlines() if line.strip())}
