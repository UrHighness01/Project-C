"""Shared pytest fixtures and markers for Project-C tests."""
import numpy as np
import pytest
from runtime.state import phi_series, have_live_state


def _phi_ok() -> bool:
    """True when live telemetry is available and large enough to test on."""
    try:
        return have_live_state() and phi_series().size >= 64
    except Exception:
        return False


skip_no_telemetry = pytest.mark.skipif(
    not _phi_ok(),
    reason="live daemon telemetry not available (expected in CI without a running agent)",
)
