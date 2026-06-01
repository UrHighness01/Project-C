import threading
import time

from el.stdlib import consciousness as c


def test_http_monitor_consciousness():
    c.reset()
    c.signal('a', 10.0)

    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    sock.close()

    c.start_http_monitor(port=port, path='/consciousness')
    try:
        import requests
        r = requests.get(f'http://127.0.0.1:{port}/consciousness')
        assert r.status_code == 200
        data = r.json()
        assert 'phi' in data
        assert 'event_trace' in data
        assert any(evt['type'] == 'consciousness_signal' for evt in data['event_trace'])
    finally:
        c.stop_http_monitor()


def test_get_queue_drop_count():
    c.reset()
    current = c.get_queue_drop_count()
    assert isinstance(current, int)


def test_speculative_stabilization_trigger():
    c.reset()
    # force a spike by gunning phi rapidly
    for i in range(6):
        c.signal('x', 100.0)
    assert c.get_metrics()['mode'] in ('stabilized', 'safe', 'degraded')


def test_get_backpressure_metrics():
    m = c.get_backpressure_metrics()
    assert 'queue_drop_count' in m
    assert 'backpressure_drops' in m
    assert 'queue_size' in m
    assert 'queue_capacity' in m


def test_snapshot_callback_and_state():
    c.reset()
    called = []
    def cb(payload):
        called.append(payload)

    c.set_snapshot_callback(cb)
    c.signal('x', 100.0)
    time.sleep(0.1)
    assert called, 'snapshot callback should be invoked'

    r = c.snapshot_state(path='/tmp/consciousness_snapshot_test.json')
    assert r['status'] == 'ok'
    assert c.get_queue_drop_count() >= 0
