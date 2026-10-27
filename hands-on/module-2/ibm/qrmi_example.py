"""Run a Qiskit primitive program with the lower-level QRMI API."""

import json
import argparse
from contextlib import contextmanager
from pathlib import Path
import sys
import time
from typing import Iterator

# pylint: disable=no-name-in-module
from qrmi import (
    Payload,
    QRMIService,
    QuantumResource,
    TaskStatus,
)


@contextmanager
def resource_context() -> Iterator[QuantumResource]:
    """Use the resource the scheduler allocated to this job.

    Yields:
        (QuantumResource): Resource used for the task.
    """
    resource, = QRMIService().resources()
    yield resource


def run_task(resource: QuantumResource, input_json: dict, timeout: float) -> str:
    """Submit a task and return its result, canceling it when the time limit expires.

    Args:
        resource (QuantumResource): Allocated IBM Quantum Compute or Quantum System resource.
        input_json (dict): Qiskit Primitive input.
        timeout (float): Maximum polling duration in seconds.

    Returns:
        (str): Backend result JSON containing a bitstring counter.
    """
    try:
        # pylint: disable=import-outside-toplevel
        from qiskit_ibm_runtime.decoders.result_decoder import (
            ResultDecoder,
        )
    except ImportError:  # qiskit-ibm-runtime < 0.48
        # pylint: disable=import-outside-toplevel
        from qiskit_ibm_runtime.utils.result_decoder import (
            ResultDecoder,
        )

    # QiskitPrimitive is the payload format for both IBM Quantum Compute Service
    # and IBM Quantum System Service resources.
    primitive_input = json.dumps(input_json["parameters"])
    program_id = input_json["program_id"]
    task = resource.task_start(
        Payload.QiskitPrimitive(input=primitive_input, program_id=program_id)
    )
    print(
        f"Resource: {resource.resource_id()}; task: {task}", file=sys.stderr, flush=True
    )
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        status = resource.task_status(task)
        if status == TaskStatus.Completed:
            result = ResultDecoder.decode(resource.task_result(task).value)
            pub_result = result[0]
            return json.dumps({"counter": pub_result.data.meas.get_counts()})
        if status in (TaskStatus.Failed, TaskStatus.Cancelled):
            raise RuntimeError(f"Task ended with {status}: {resource.task_logs(task)}")
        time.sleep(1)
    resource.task_stop(task)
    raise TimeoutError(f"Task {task} exceeded {timeout:g} seconds and was canceled.")


def _main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="primitive input file", type=Path)
    parser.add_argument("--timeout", type=float, default=300)
    args = parser.parse_args()
    with resource_context() as resource:
        with open(args.input, "r", encoding="utf-8") as input_file:
            input_json = json.load(input_file)
            print(run_task(resource, input_json, args.timeout))


if __name__ == "__main__":
    _main()
