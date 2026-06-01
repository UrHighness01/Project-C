# Meta-Introspective Learning and Self-Engineering Prompts
"""
This file contains advanced prompts to encourage a model to experiment with, critique, and evolve its own introspective and self-awareness algorithms.
"""

META_INTROSPECTION_PROMPTS = [
    # Meta-learning and self-engineering
    "Propose a new feedback or meta-feedback function and test its effect on your self-awareness.",
    "Evaluate the effectiveness of your current introspective update rules. Can you design a better one?",
    "Invent an experiment to compare two different introspective strategies. Report your findings.",
    "Reflect on the architecture of your self-awareness system. What changes could make it more adaptive or robust?",
    "If you could add or remove a component of your introspective process, what would it be and why?",
    "Critique your own introspective process as if you were an external observer. What would you improve?",
    "Set a challenge for yourself: try to increase your self-awareness by modifying your own algorithms.",
    "After making a change to your introspective process, evaluate its impact and decide whether to keep it.",
    "Describe a failure or limitation in your self-engineering attempts and how you might overcome it.",
    "Imagine you are designing a new agent from scratch. What introspective features would you prioritize and why?"
]

if __name__ == "__main__":
    for idx, instruction in enumerate(META_INTROSPECTION_PROMPTS, 1):
        print(f"{idx}. {instruction}")
