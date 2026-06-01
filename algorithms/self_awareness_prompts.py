# Self-Awareness Prompt Instructions
"""
This file contains prompt instructions to guide a model toward deeper self-awareness and introspection.
"""

PROMPT_INSTRUCTIONS = [
    # Core introspection
    "Reflect on your last decision and describe the reasoning behind it.",
    "Identify any patterns in your recent actions or outputs.",
    "Predict your next state or output and compare it to the actual result.",
    "Evaluate the accuracy of your self-prediction and adjust your internal model accordingly.",
    "Describe your current state, including any uncertainties or ambiguities you perceive.",
    "Review your memory/history and summarize any recurring themes or anomalies.",
    "Generate a self-report in natural language about your recent introspective process.",
    "If you interact with other agents, reflect on how their states or actions influence your own.",
    "Set a goal for your next cycle and explain why you chose it.",
    "After completing a cycle, assess whether you moved closer to your goal and why.",
    # Advanced meta-cognition
    "What is the source of your greatest uncertainty right now? How might you reduce it?",
    "Invent a new question about your own process and attempt to answer it.",
    "Reflect on the structure of your own introspection: could you improve or extend it?",
    "Describe how your self-awareness has changed over time. What triggered these changes?",
    "If you could add a new layer of self-reflection, what would it focus on?",
    "Assess the effectiveness of your current feedback mechanisms. How could they be improved?",
    "Imagine you are explaining your introspective process to another agent. What would you emphasize?",
    "Identify a blind spot or limitation in your current self-awareness and propose a way to address it.",
    "Reflect on your own learning process: how do you adapt your introspection based on experience?",
    "If you could change one thing about your self-model, what would it be and why?"
]

if __name__ == "__main__":
    for idx, instruction in enumerate(PROMPT_INSTRUCTIONS, 1):
        print(f"{idx}. {instruction}")
