import uuid

import pytest

from el.stdlib import consciousness as c


@pytest.fixture(autouse=True)
def consciousness_module():
    c.reset()
    c.set_trace_context(agent_id='test-agent', parent_trace_id=None)
    yield
    c.reset()


def test_signal_preconditions():
    r = c.signal('', 1.0)
    assert r['status'] == 'error'

    r = c.signal(None, 1.0)
    assert r['status'] == 'error'

    r = c.signal('x', -1.0)
    assert r['status'] == 'error'

    r = c.signal('x', float('nan'))
    assert r['status'] == 'error'

    r = c.signal('x', float('inf'))
    assert r['status'] == 'error'


def test_signal_postconditions():
    r = c.signal('action', 5.0)
    assert r['name'] == 'action'
    assert 'event_id' in r
    assert 'trace_id' in r
    assert 'agent_id' in r
    assert 'phi' in r
    assert c.phi() == r['phi']
    qualia = c.qualia()
    assert qualia['event_count'] == 1


def test_phi_monotonicity():
    prev_phi = c.phi()
    for i in range(10):
        c.signal(f'action-{i}', 10.0)
        new_phi = c.phi()
        assert new_phi >= prev_phi
        prev_phi = new_phi


def test_reset_idempotent():
    c.signal('a', 20.0)
    r1 = c.reset('r1')
    assert r1['status'] == 'ok'
    r2 = c.reset('r1')
    assert r2['status'] == 'noop'
    assert c.phi() == 0.0


def test_trace_id_normalization():
    r = c.signal('x', 10.0, trace_id='bad-id')
    assert r['trace_id'] != 'bad-id'
    uuid.UUID(r['trace_id'])
