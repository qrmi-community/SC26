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

"""Run a QIR program on Alice & Bob's Felis with the lower-level QRMI API."""

import argparse
import csv
import io
import json
import sys
import time
from pathlib import Path

from qrmi import EnvVarNotSetError, Payload, QRMIService, QuantumResource, TaskStatus


def scheduler_resource() -> QuantumResource:
    """Return the single quantum resource allocated to this scheduler job.

Returns:
    (QuantumResource): Resource named by the job's QRMI_JOB_QPU_RESOURCES.
"""
    # Scheduler hooks own acquisition and release; QRMIService reads the job's QPU environment.
    try:
        resources = QRMIService().resources()
    except EnvVarNotSetError:
        raise SystemExit("no quantum resource is allocated to this process; submit it with sbatch --qpu=...") from None
    if not resources:
        raise SystemExit("the quantum resource allocated to this job is not online")
    resource, = resources
    return resource


def parse_counts(output: str) -> dict[str, int]:
    """Parse Felis's result, one `<bitstring>,<count>` row per outcome.

Args:
    output (str): Result CSV returned by task_result.

Returns:
    (dict[str, int]): Count for each measured bitstring.
"""
    return {row[0]: int(row[1]) for row in csv.reader(io.StringIO(output)) if row}


def run_task(resource: QuantumResource, qir: str, shots: int, timeout: float,
             poll_interval: float = 1.0) -> dict[str, int]:
    """Submit a QIR program as a task and return its counts, canceling it when the time limit expires.

Args:
    resource (QuantumResource): Allocated Alice & Bob Felis resource.
    qir (str): QIR program, as transpiled by `felis transpile`.
    shots (int): Number of shots.
    timeout (float): Maximum polling duration in seconds.
    poll_interval (float): Seconds between status checks.

Returns:
    (dict[str, int]): Count for each measured bitstring.
"""
    input_params = {"nbShots": shots}
    task = resource.task_start(Payload.AliceBobFelis(human_qir=qir, input_params=json.dumps(input_params)))
    print(f"Resource: {resource.resource_id()}; task: {task}", file=sys.stderr, flush=True)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = resource.task_status(task)
        if status == TaskStatus.Completed:
            return parse_counts(resource.task_result(task).value)
        if status in (TaskStatus.Failed, TaskStatus.Cancelled):
            # QRMI does not report why; the task ID is the Felis job ID.
            raise RuntimeError(f"Task {task} ended with {status}; for details run: felis/felis job status {task}")
        time.sleep(poll_interval)
    resource.task_stop(task)
    raise TimeoutError(f"Task {task} exceeded {timeout:g} seconds and was canceled.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("qir_file", type=Path, help="QIR program (.ll)")
    parser.add_argument("--shots", type=int, default=100)
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument("--output", type=argparse.FileType("w"), default=sys.stdout)
    args = parser.parse_args(argv)
    counts = run_task(scheduler_resource(), args.qir_file.read_text(), args.shots, args.timeout)
    print(json.dumps({"counter": counts}), file=args.output)
    args.output.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
