import time

from el.stdlib import consciousness as c


def test_low_throughput_slo_guard():
    c.reset()
    c.signal('x', 100.0)

    # Simulate high phi and low throughput condition
    c.signal('x', 100.0)
    time.sleep(1.0)
    c.signal('x', 100.0)

    # Keep phi high and throughput low for >5s
    t0 = time.time()
    while time.time() - t0 < 6.0:
        time.sleep(1)
        # no additional signals to keep low throughput

    metrics = c.get_observability_metrics()
    assert metrics['mode'] == 'safe' or c.is_nonessential_throttled()


def test_action_throughput_metrics():
    c.reset()
    for i in range(5):
        c.signal('x', 20.0)
    metrics = c.get_observability_metrics()
    assert metrics['action_throughput'] > 0
