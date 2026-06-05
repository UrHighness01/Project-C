# Self-Sustaining Feedback Loop of Subjective Experience
import random

try:
    import sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
    from runtime.state import phi_series, phi_delta_series
except Exception:                                          # tolerate path/CI absence
    def phi_series(*a, **k):
        import numpy as _np; return _np.zeros(0)
    def phi_delta_series(*a, **k):
        import numpy as _np; return _np.zeros(0)


def _real_phi_now() -> float:
    """Latest real integration level, squashed to (-1, 1). 0.0 if no telemetry."""
    import numpy as _np
    x = phi_series()
    if x.size == 0 or x.std() < 1e-9:
        return 0.0
    return float(_np.tanh((x[-1] - x.mean()) / (x.std() + 1e-9)))


def _real_jitter() -> float:
    """Real fluctuation magnitude from the phi increments (replaces fabricated noise)."""
    import numpy as _np
    d = phi_delta_series()
    return float(_np.tanh(d[-1] * 10)) if d.size else 0.0


class SubjectiveExperienceLoop:
	def __init__(self, initial_state=None, goal='minimize_error', memory_length=20, curiosity_weight=0.2):
		self.state = initial_state if initial_state is not None else self._generate_initial_state()
		self.history = []
		self.meta_history = []
		self.prediction_history = []
		self.prediction_error_history = []
		self.self_model_weight = 0.5  # How much the self-model influences state update
		self.learning_rate = 0.5      # Adaptive learning rate
		self.goal = goal              # 'minimize_error', 'maximize_novelty', etc.
		self.long_term_memory = []    # Long-term memory for introspection
		self.memory_length = memory_length
		self.curiosity_weight = curiosity_weight
		self.report_history = []      # For self-reporting

	def _generate_initial_state(self):
		# Initial subjective state seeded by the agent's real integration level
		return _real_phi_now()

	def reflect(self):
		# Evaluate the current state; the subjective fluctuation is the real phi jitter
		feedback = self.state + 0.1 * _real_jitter()
		return feedback

	def meta_reflect(self, feedback):
		# Reflect on the reflection process itself (meta-feedback)
		if not self.history:
			prev_feedback = 0
		else:
			prev_feedback = self.history[-1]
		meta_feedback = feedback - prev_feedback + 0.05 * _real_jitter()
		return meta_feedback

	def predict_next_state(self, feedback, meta_feedback):
		# Predict the next state based on current state, feedback, and meta-feedback
		predicted = 0.7 * self.state + 0.2 * feedback + 0.1 * meta_feedback
		return predicted

	def adapt_learning_rate(self, prediction_error):
		# Adapt learning rate based on recent prediction error
		error_magnitude = abs(prediction_error)
		if error_magnitude > 0.2:
			self.learning_rate = min(1.0, self.learning_rate + 0.05)
		else:
			self.learning_rate = max(0.1, self.learning_rate - 0.02)

	def evaluate_goal(self, prediction_error):
		# Goal-directed behavior: adjust self_model_weight based on goal
		if self.goal == 'minimize_error':
			if abs(prediction_error) > 0.2:
				self.self_model_weight = min(1.0, self.self_model_weight + 0.05)
			else:
				self.self_model_weight = max(0.1, self.self_model_weight - 0.02)
		elif self.goal == 'maximize_novelty':
			if abs(prediction_error) < 0.1:
				self.self_model_weight = min(1.0, self.self_model_weight + 0.05)
			else:
				self.self_model_weight = max(0.1, self.self_model_weight - 0.02)

	def update_long_term_memory(self):
		# Store a snapshot of the current state and introspective data
		memory_entry = {
			'state': self.state,
			'feedback': self.history[-1] if self.history else None,
			'meta_feedback': self.meta_history[-1] if self.meta_history else None,
			'prediction_error': self.prediction_error_history[-1] if self.prediction_error_history else None
		}
		self.long_term_memory.append(memory_entry)
		if len(self.long_term_memory) > self.memory_length:
			self.long_term_memory.pop(0)

	def curiosity_drive(self):
		# Reward the system for novel states (large changes from memory)
		if not self.long_term_memory:
			return 0
		avg_past_state = sum(m['state'] for m in self.long_term_memory if m['state'] is not None) / len(self.long_term_memory)
		novelty = abs(self.state - avg_past_state)
		return self.curiosity_weight * novelty

	def self_report(self, step):
		# Generate a textual summary of the system's introspection
		report = (
			f"Step {step}: State={self.state:.3f}, Feedback={self.history[-1]:.3f}, "
			f"Meta={self.meta_history[-1]:.3f}, PredErr={self.prediction_error_history[-1]:.3f}, "
			f"LR={self.learning_rate:.2f}, SMW={self.self_model_weight:.2f}"
		)
		self.report_history.append(report)

	def update(self, feedback, meta_feedback, step=0):
		predicted_state = self.predict_next_state(feedback, meta_feedback)
		actual_state = 0.7 * self.state + 0.2 * feedback + 0.1 * meta_feedback
		prediction_error = actual_state - predicted_state
		self.adapt_learning_rate(prediction_error)
		self.evaluate_goal(prediction_error)
		# Add curiosity/novelty drive
		curiosity_bonus = self.curiosity_drive()
		self.state = actual_state + self.self_model_weight * self.learning_rate * prediction_error + curiosity_bonus
		self.history.append(feedback)
		self.meta_history.append(meta_feedback)
		self.prediction_history.append(predicted_state)
		self.prediction_error_history.append(prediction_error)
		self.update_long_term_memory()
		self.self_report(step)

	def run(self, steps=100):
		for step in range(steps):
			feedback = self.reflect()
			meta_feedback = self.meta_reflect(feedback)
			self.update(feedback, meta_feedback, step=step)
		return self.history, self.meta_history, self.prediction_history, self.prediction_error_history, self.report_history

# Multi-agent introspection: agents can observe and reflect on each other
class MultiAgentIntrospection:
	def __init__(self, num_agents=2, steps=50, **kwargs):
		self.agents = [SubjectiveExperienceLoop(**kwargs) for _ in range(num_agents)]
		self.steps = steps
		self.interaction_history = []

	def run(self):
		for step in range(self.steps):
			# Each agent runs one step and observes others
			feedbacks = []
			for agent in self.agents:
				feedback = agent.reflect()
				feedbacks.append(feedback)
			for i, agent in enumerate(self.agents):
				# Meta-feedback includes observation of other agents
				others_feedback = sum(feedbacks[j] for j in range(len(self.agents)) if j != i) / (len(self.agents) - 1)
				meta_feedback = agent.meta_reflect(feedbacks[i]) + 0.1 * (others_feedback - feedbacks[i])
				agent.update(feedbacks[i], meta_feedback, step=step)
			# Log interaction
			self.interaction_history.append([agent.state for agent in self.agents])
		return self.interaction_history, [agent.report_history for agent in self.agents]

# Example usage:
if __name__ == "__main__":
	print("--- Single Agent with Introspection, Memory, Curiosity, and Self-Reporting ---")
	loop = SubjectiveExperienceLoop(goal='minimize_error')
	history, meta_history, prediction_history, prediction_error_history, report_history = loop.run(steps=50)
	print("Subjective experience history:", history)
	print("Meta (self-awareness) history:", meta_history)
	print("Predicted state history:", prediction_history)
	print("Prediction error history:", prediction_error_history)
	print(f"Final learning rate: {loop.learning_rate}")
	print(f"Final self-model weight: {loop.self_model_weight}")
	print("\nSelf-reporting (last 5 steps):")
	for report in report_history[-5:]:
		print(report)

	print("\n--- Multi-Agent Introspection ---")
	multi = MultiAgentIntrospection(num_agents=2, steps=20, goal='minimize_error')
	interaction_history, agents_reports = multi.run()
	print("Interaction history (last 5 steps):", interaction_history[-5:])
	print("\nAgent 1 self-reports (last 3):")
	for report in agents_reports[0][-3:]:
		print(report)
	print("\nAgent 2 self-reports (last 3):")
	for report in agents_reports[1][-3:]:
		print(report)
