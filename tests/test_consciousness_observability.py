import time

from el.stdlib import consciousness as c


def test_observability_metrics_keys():
    c.reset()
    c.signal('x', 10.0)
    metrics = c.get_observability_metrics()
    for key in ['phi', 'phi_rate', 'mode', 'action_throughput', 'throttle_engaged', 'backpressure_drops', 'event_drops', 'cycle_alerts', 'quarantine_count', 'anomaly_count', 'trace_missing_count']:
        assert key in metrics


def test_http_monitor_includes_event_trace():
    c.reset()
    c.signal('x', 10.0)
    # bind a random port
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
        assert 'event_trace' in data
        assert isinstance(data['event_trace'], list)
    finally:
        c.stop_http_monitor()
