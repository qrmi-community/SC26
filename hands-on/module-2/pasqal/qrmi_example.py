"""Run a serialized Pulser program with the lower-level QRMI API."""

import argparse
from contextlib import contextmanager
from pathlib import Path
import sys
import time
from typing import Iterator

from qrmi import Payload, QRMIService, QuantumResource, ResourceType, TaskStatus


@contextmanager
def resource_context(standalone: str | None) -> Iterator[QuantumResource]:
    """Use a scheduler allocation or acquire a standalone Cloud resource.

Args:
    standalone (str | None): Cloud backend name, or None for a scheduler job.

Yields:
    (QuantumResource): Resource used for the task.
"""
    if standalone is None:
        resource, = QRMIService().resources()
        yield resource
    else:
        resource = QuantumResource(standalone, ResourceType.PasqalCloud)
        session = resource.acquire()
        try:
            yield resource
        finally:
            resource.release(session)


def run_task(resource: QuantumResource, sequence: str, runs: int, timeout: float) -> str:
    """Submit a task and return its result, canceling it when the time limit expires.

Args:
    resource (QuantumResource): Allocated Pasqal Cloud or Local resource.
    sequence (str): Pulser abstract representation JSON.
    runs (int): Number of measurement samples.
    timeout (float): Maximum polling duration in seconds.

Returns:
    (str): Backend result JSON containing a bitstring counter.
"""
    # PasqalCloud is the payload format for both Cloud and Local resources.
    task = resource.task_start(Payload.PasqalCloud(sequence=sequence, job_runs=runs))
    print(f"Resource: {resource.resource_id()}; task: {task}", file=sys.stderr, flush=True)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = resource.task_status(task)
        if status == TaskStatus.Completed:
            return resource.task_result(task).value
        if status in (TaskStatus.Failed, TaskStatus.Cancelled):
            raise RuntimeError(f"Task ended with {status}: {resource.task_logs(task)}")
        time.sleep(1)
    resource.task_stop(task)
    raise TimeoutError(f"Task {task} exceeded {timeout:g} seconds and was canceled.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sequence", type=Path)
    parser.add_argument("--runs", type=int, default=1000)
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument("--output", type=argparse.FileType("w"), default=sys.stdout)
    parser.add_argument("--standalone", metavar="CLOUD_BACKEND", help="Acquire Cloud without a scheduler")
    args = parser.parse_args()
    with resource_context(args.standalone) as resource:
        print(run_task(resource, args.sequence.read_text(), args.runs, args.timeout), file=args.output)
