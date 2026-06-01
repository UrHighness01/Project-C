# Surprise-About-Own-Surprise (SAS)
"""
Detects higher-order blindness by tracking surprise and meta-surprise, triggering a meta-surprise alert if needed.
"""
import math
from collections import deque

class SurpriseAboutSurprise:
    def __init__(self, window=30):
        self.surprise_log = []
        self.auto_surprise_log = []
        self.window = window
        self.meta_alert = False

    def log_surprise(self, prob):
        S_t = -math.log(prob + 1e-8)
        self.surprise_log.append(S_t)
        if len(self.surprise_log) > 1:
            A_t = abs(S_t - self.surprise_log[-2])
            self.auto_surprise_log.append(A_t)
        else:
            self.auto_surprise_log.append(0.0)
        self.check_meta_surprise()

    def check_meta_surprise(self):
        if len(self.auto_surprise_log) < self.window:
            return
        windowed = self.auto_surprise_log[-self.window:]
        mean_A = sum(windowed) / len(windowed)
        historical = sorted(self.auto_surprise_log)
        threshold = historical[max(1, int(0.05 * len(historical))) - 1]
        if mean_A < threshold:
            self.meta_alert = True

if __name__ == "__main__":
    sas = SurpriseAboutSurprise()
    import random
    for _ in range(100):
        sas.log_surprise(random.uniform(0.01, 1.0))
    print("Meta-surprise alert:", sas.meta_alert)
