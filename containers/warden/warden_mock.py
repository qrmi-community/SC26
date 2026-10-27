"""Serve Warden's Qutip test QPU with the tutorial's two-atom device."""

import json

from pulser.devices import DigitalAnalogDevice
from mock_qpu_api.app import create_app
from mock_qpu_api.routes import system

# The stock FRESNEL fixture requires a much larger register. Keep the real mock
# job implementation, but advertise the device used by these small examples.
system.DUMMY_QPU_SPECS = json.loads(DigitalAnalogDevice.to_abstract_repr())
app = create_app()
