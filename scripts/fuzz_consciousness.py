import time
import os
import json
import os
import random
import os
import threading
import os
import uuid
import os
from collections import deque

from el.stdlib import consciousness as c

FUZZ_REPLAY_DIR = 'chaos-replays'


def _normalize_qualia(q):
    if not isinstance(q, (list, tuple)) or len(q) == 0:
        raise ValueError('QUALIA_INVALID')
    for x in q:
        if not isinstance(x, (int, float)) or x != x or x in (float('inf'), float('-inf')):
            raise ValueError('QUALIA_INVALID')
    return tuple(float(x) for x in q)


def fuzz_harness(seed=0, duration=300):
    random.seed(seed)
    c.reset()
    c.get_metrics()
    c.configure_circuit_breaker('control:.*', failure_threshold=5, cooldown=30, retries=3)

    failures = []
    timeline = []
    event_store = []
    mode = 'normal'
    event_id_window = deque(maxlen=50)

    obs_stop = threading.Event()

    def observe():
        while not obs_stop.is_set():
            phi = c.phi()
            mode_current = 'safe' if c.is_nonessential_throttled() else 'degraded' if phi > 0.9 else 'normal'
            timeline.append({'t': time.time(), 'phi': phi, 'mode': mode_current})
            time.sleep(0.1)

    thread_obs = threading.Thread(target=observe, daemon=True)
    thread_obs.start()

    start = time.time()
    while time.time() - start < duration:
        # generate event
        event_type = random.choices(['signal', 'qualia', 'reset'], weights=[0.7, 0.2, 0.1])[0]
        trace_id = str(uuid.uuid4())
        event_id = str(uuid.uuid4())
        source = random.choice(['external', 'internal'])
        timestamp = time.time()

        event = {
            'event_id': event_id,
            'trace_id': trace_id,
            'source': source,
            'timestamp': timestamp,
            'type': event_type,
        }

        if event_type == 'signal':
            event['name'] = random.choice(['a', 'b', 'control:x', 'fast'])
            event['salience'] = random.uniform(-10, 120) if random.random() < 0.25 else random.uniform(0, 100)
            event['qualia'] = [random.uniform(-1, 1) for _ in range(3)]
            event['impact'] = 'critical' if random.random() < 0.1 else 'normal'
        elif event_type == 'qualia':
            event['qualia'] = [random.uniform(-1, 1) for _ in range(3)]
        else:
            event['reset_id'] = str(uuid.uuid4())

        # bus-level faults
        if random.random() < 0.5:
            # drop
            c.get_metrics()  # exercise path
            continue

        # duplication
        if random.random() < 0.5:
            event_store.append(event.copy())

        # mutation
        if random.random() < 0.2:
            if event_type == 'signal':
                event['salience'] = random.choice(['INVALID', float('nan'), float('inf')])

        # jitter
        time.sleep(random.uniform(0, 0.02))

        # reordering buffer
        event_store.append(event)
        if len(event_store) > 20 and random.random() < 0.3:
            random.shuffle(event_store)

        # process queue
        while event_store:
            e = event_store.pop(0)
            try:
                if e['type'] == 'signal':
                    c.signal(e['name'], e['salience'], trace_id=e['trace_id'])
                elif e['type'] == 'qualia':
                    c.qualia()
                elif e['type'] == 'reset':
                    c.reset()
            except Exception as ex:
                failures.append({'event': e, 'error': str(ex)})

            # queue limit check
            metrics = c.get_metrics()
            if metrics.get('backpressure_depth', 0) > 1000:
                c.set_consciousness_policy({'backpressure': 'shed_oldest'})

    obs_stop.set()
    thread_obs.join()

    # final metrics
    final_metrics = c.get_metrics()
    report = {
        'seed': seed,
        'duration': duration,
        'pass': len(failures) == 0,
        'failures': failures,
        'timeline': timeline,
        'final_metrics': final_metrics,
    }

    filename = os.path.join(FUZZ_REPLAY_DIR, f'chaos-replay-{int(time.time())}.json')
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)

    return report


if __name__ == '__main__':
    r = fuzz_harness(seed=0xBEEFCAFE, duration=300)
    print('report saved', r['final_metrics'])
