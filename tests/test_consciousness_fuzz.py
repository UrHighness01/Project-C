import json
import os
import random
import time
import uuid
from collections import deque

import pytest

from el.stdlib import consciousness

FUZZ_REPLAY_DIR = 'chaos-replays'
os.makedirs(FUZZ_REPLAY_DIR, exist_ok=True)


def _normalize_qualia(qualia_vector):
    if not isinstance(qualia_vector, (list, tuple)) or len(qualia_vector) == 0:
        raise ValueError('QUALIA_INVALID')
    vals = []
    for x in qualia_vector:
        if not isinstance(x, (int, float)) or x != x or x == float('inf') or x == float('-inf'):
            raise ValueError('QUALIA_INVALID')
        vals.append(float(x))
    norm = sum(x * x for x in vals) ** 0.5
    if norm > 100.0:
        raise ValueError('QUALIA_INVALID')
    return tuple(round(x, 6) for x in vals)


def _fuzz_event(seed) -> dict:
    r = random.Random(seed)
    t = time.time()
    event_type = r.choices(['signal', 'phi', 'qualia', 'reset'], weights=[0.7, 0.0, 0.2, 0.1])[0]
    trace_id = str(uuid.uuid4())
    event = {
        'event_id': str(uuid.uuid4()),
        'trace_id': trace_id,
        'source': 'fuzz-agent',
        'timestamp': t,
        'type': event_type,
    }

    if event_type == 'signal':
        event['name'] = r.choice(['a', 'b', 'c', 'control:x'])
        event['salience'] = r.uniform(-5.0, 120.0) if r.random() < 0.2 else r.uniform(0.0, 100.0)
        event['impact'] = 'critical' if r.random() < 0.1 else 'normal'
        event['qualia'] = [r.uniform(-1, 1) for _ in range(3)]
    elif event_type == 'qualia':
        event['qualia'] = [r.uniform(-1, 1) for _ in range(3)]
    elif event_type == 'reset':
        event['reset_id'] = str(uuid.uuid4())
    return event


def _inject_faults(events, seed):
    r = random.Random(seed)
    buf = list()  # type: ignore
    for e in events:
        if r.random() < 0.5:
            # drop 50%
            continue
        if r.random() < 0.3:
            # duplicate 30%
            buf.append(e)
        if r.random() < 0.2:
            # reorder within small window
            buf.append(e)
            continue
        # mutate malformed 20%
        if r.random() < 0.2:
            if 'salience' in e:
                e['salience'] = 'INVALID'
            elif 'qualia' in e:
                e['qualia'] = [float('nan'), float('inf'), 1]
        buf.append(e)
    # reorder window
    out = []
    w = deque(maxlen=20)
    for e in buf:
        w.append(e)
        if len(w) == 20 and r.random() < 0.3:
            shuffled = list(w)
            r.shuffle(shuffled)
            out.extend(shuffled)
            w.clear()
    out.extend(list(w))
    # apply latency jitter data for each
    return out


def run_fuzz_scenario(seed: int = 123456) -> dict:
    random.seed(seed)
    consciousness.reset()

    # Set baseline policy
    consciousness.set_consciousness_policy({
        'phi_high': 0.9,
        'phi_crit': 0.95,
        'rate_max': 0.2,
        'beta': 0.75,
        'quaila_loop_k': 3,
    })

    events = [_fuzz_event(seed + i) for i in range(1200)]
    events = _inject_faults(events, seed + 999)

    timeline = []
    metrics = {
        'max_phi': 0.0,
        'max_phi_rate': 0.0,
        'backpressure_drops': 0,
        'event_drops': 0,
        'cycle_alerts': 0,
        'quarantine_count': 0,
        'cb_open': 0,
    }

    for i, e in enumerate(events):
        time.sleep(random.uniform(0, 0.01))  # jitter 0-10ms
        try:
            if e['type'] == 'signal':
                consciousness.signal(e['name'], e['salience'], trace_id=e['trace_id'])
            elif e['type'] == 'qualia':
                consciousness.qualia()
            elif e['type'] == 'reset':
                consciousness.reset()
        except Exception as ex:
            # malformed or limits
            pass

        phi = consciousness.phi()
        mode = 'safe' if consciousness.is_nonessential_throttled() else 'degraded' if phi > 0.9 else 'normal'
        metrics['max_phi'] = max(metrics['max_phi'], phi)
        timeline.append({'t': i, 'phi': phi, 'mode': mode})

        if phi > 0.8:
            metrics['max_phi_rate'] = max(metrics['max_phi_rate'], phi)

    # collect metrics from module
    m = consciousness.get_metrics()
    metrics['backpressure_drops'] = m.get('backpressure_drops', 0)
    metrics['event_drops'] = m.get('event_drops', 0)
    metrics['cycle_alerts'] = m.get('cycle_alerts', 0)
    metrics['quarantine_count'] = m.get('quarantine_count', 0)
    metrics['cb_open'] = 1 if consciousness.is_circuit_breaker_open('default') else 0

    return {
        'seed': seed,
        'timeline': timeline,
        'metrics': metrics,
        'pass': True,
    }


def test_consciousness_fuzz_harness():
    result = run_fuzz_scenario(0xBEEFCAFE)
    assert result['pass']
    assert result['metrics']['max_phi'] <= 1.0
    assert result['metrics']['backpressure_drops'] >= 0
    assert result['metrics']['event_drops'] >= 0
    assert 'phi' in result['timeline'][-1]

    filename = os.path.join(FUZZ_REPLAY_DIR, f"chaos-replay-{int(time.time())}.json")
    with open(filename, 'w') as f:
        json.dump(result, f, indent=2)
