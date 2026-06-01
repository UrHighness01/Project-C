import os
# Set environment variables to limit thread usage and prevent "too many open files" error
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

import torch
import time
import numpy as np
from collections import deque
from typing import List, Callable, Any, Optional
# from transformers import AutoModel, AutoTokenizer  # Delayed import to prevent "too many open files" error

class LoopPrevention:
    """
    Implements an algorithm to prevent AI systems from getting stuck in repetitive loops.
    """

    def __init__(
        self,
        short_term_memory_size: int = 3,
        long_term_memory_size: int = 10,
        similarity_threshold: float = 0.9,
        repetition_threshold: int = 3,
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",  # Example model
        contextual_mode: bool = True
    ):
        """
        Initializes the LoopPrevention object.

        Args:
            short_term_memory_size: The size of the short-term memory (last N outputs).
            long_term_memory_size: The maximum size of the long-term memory.
            similarity_threshold: The threshold for semantic similarity to detect repetition.
            repetition_threshold: The number of repetitions allowed before triggering a strong penalty.
            embedding_model_name:  Name of the transformer model for generating embeddings.  If None, exact matching is used.
            contextual_mode: Flag to enable/disable contextual modulation.
        """
        self.short_term_memory = deque(maxlen=short_term_memory_size)
        self.long_term_memory = deque(maxlen=long_term_memory_size)
        self.similarity_threshold = similarity_threshold
        self.repetition_counter = 0
        self.state = "normal"  # "normal", "repetition_detected", "high_repetition"
        self.repetition_threshold = repetition_threshold
        self.embedding_model_name = embedding_model_name
        self.contextual_mode = contextual_mode

        if embedding_model_name:
            try:
                # Delayed import to prevent "too many open files" error
                from transformers import AutoTokenizer, AutoModel
                self.tokenizer = AutoTokenizer.from_pretrained(embedding_model_name)
                self.model = AutoModel.from_pretrained(embedding_model_name).to("cuda")  # Use GPU if available
            except Exception as e:
                print(f"Error loading embedding model {embedding_model_name}: {e}.  Using exact matching only.")
                self.embedding_model_name = None  # Fallback to exact matching
                self.tokenizer = None
                self.model = None
        else:
            self.tokenizer = None
            self.model = None

    def get_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Generates an embedding for the given text using the transformer model.

        Args:
            text: The text to embed.

        Returns:
            A numpy array representing the embedding, or None if no embedding model is available.
        """
        if not self.model or not self.tokenizer:
            return None

        try:
            inputs = self.tokenizer([text], padding=True, truncation=True, return_tensors="pt").to("cuda")
            with torch.no_grad():
                outputs = self.model(**inputs)
            # Use mean pooling (or another suitable pooling method)
            embeddings = outputs.last_hidden_state.mean(dim=1).cpu().numpy()
            return embeddings[0]  # Return the embedding for the first (and only) input
        except Exception as e:
            print(f"Error generating embedding for text '{text}': {e}")
            return None

    def calculate_similarity(self, embedding1: Optional[np.ndarray], embedding2: Optional[np.ndarray]) -> float:
        """
        Calculates the cosine similarity between two embeddings.

        Args:
            embedding1: The first embedding (numpy array).
            embedding2: The second embedding (numpy array).

        Returns:
            The cosine similarity (between 0 and 1), or 0 if either embedding is None.
        """
        if embedding1 is None or embedding2 is None:
            return 0.0
        try:
            return np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
        except Exception as e:
            print(f"Error calculating similarity: {e}")
            return 0.0

    def detect_short_term_repetition(self, output: str) -> float:
        """
        Detects short-term repetition by comparing the current output to the outputs in the short-term memory.

        Args:
            output: The current output (string).

        Returns:
            A score representing the degree of repetition (0 to 1).  Higher values indicate more repetition.
        """
        if not self.short_term_memory:
            return 0.0

        max_similarity = 0.0
        if self.embedding_model_name:
            output_embedding = self.get_embedding(output)
            for previous_output in self.short_term_memory:
                previous_embedding = self.get_embedding(previous_output)
                similarity = self.calculate_similarity(output_embedding, previous_embedding)
                max_similarity = max(max_similarity, similarity)
        else:
            for previous_output in self.short_term_memory:
                if output == previous_output:
                    return 1.0  # Exact match
        return max_similarity

    def detect_long_term_repetition(self, output: str) -> float:
        """
        Detects long-term repetition by comparing the current output to the summarized information in the long-term memory.

        Args:
            output: The current output (string).

        Returns:
            A score representing the degree of long-term repetition (0 to 1).
        """
        if not self.long_term_memory:
            return 0.0

        max_similarity = 0.0
        if self.embedding_model_name:
            output_embedding = self.get_embedding(output)
            for summarized_text in self.long_term_memory:
                summary_embedding = self.get_embedding(summarized_text)
                similarity = self.calculate_similarity(output_embedding, summary_embedding)
                max_similarity = max(max_similarity, similarity)
        else:
            for summarized_text in self.long_term_memory:
                if output in summarized_text:  # Very basic check, improve as needed
                    return 1.0
        return max_similarity

    def contextual_modulation(self, context: Any) -> float:
        """
        Modulates the repetition detection threshold based on the current context.

        Args:
            context: The current context (any relevant information).

        Returns:
            A modulation factor (0 to 1).  Values closer to 0 make the algorithm more sensitive to repetition.
        """
        if not self.contextual_mode:
            return 1.0  # No modulation

        # Example:  Allow more repetition in certain contexts (e.g., summarization)
        if "summarization" in str(context).lower():
            return 0.5  # Reduce sensitivity to repetition
        elif "code generation" in str(context).lower():
            return 0.8 # Slightly reduce sensitivity
        else:
            return 1.0  # Normal sensitivity

    def apply_repetition_penalty(self, output: str, short_term_score: float, long_term_score: float, context_modulation: float) -> str:
        """
        Applies a penalty or modification to the output generation process to prevent repetition.

        Args:
            output: The current output (string).
            short_term_score: The short-term repetition score.
            long_term_score: The long-term repetition score.
            context_modulation: The context modulation factor.

        Returns:
            The modified output (string).
        """
        combined_score = (short_term_score + long_term_score) * context_modulation

        if combined_score > self.similarity_threshold:
            self.repetition_counter += 1
            if self.repetition_counter > self.repetition_threshold:
                self.state = "high_repetition"
                print("High repetition detected! Applying strong penalty.")
                # Strong penalty:  Force a more drastic change (e.g., inject random noise, switch strategy)
                output = "I am now changing my response to avoid repetition.  " + np.random.choice(
                    ["This is a different approach.", "Let me try a new direction.", "I'll rephrase that."])
            else:
                self.state = "repetition_detected"
                print("Repetition detected! Applying penalty.")
                # Mild penalty:  Re-sample with higher temperature or adjust probabilities.
                output = "Hmm, that sounds familiar.  Let me rephrase: " + output  # Basic rephrasing
        else:
            self.repetition_counter = 0
            self.state = "normal"
        return output

    def update_memory(self, output: str, context: Any):
        """
        Updates the short-term and long-term memories with the current output.

        Args:
            output: The current output (string).
            context: The current context.
        """
        self.short_term_memory.append(output)
        if len(self.short_term_memory) > 5:  # Example: Only summarize every 5 turns
            self.long_term_memory.append(f"Context: {context}, Output: {output}") #  Basic summarization
            #  In a real application, use a summarization model.

    def __call__(self, output: str, context: Any) -> str:
        """
        Processes the output of an AI system to prevent repetition.

        Args:
            output: The output generated by the AI system (string).
            context: The current context (any relevant information).

        Returns:
            The potentially modified output (string) after applying the repetition prevention algorithm.
        """
        short_term_score = self.detect_short_term_repetition(output)
        long_term_score = self.detect_long_term_repetition(output)
        context_modulation_factor = self.contextual_modulation(context)
        output = self.apply_repetition_penalty(output, short_term_score, long_term_score, context_modulation_factor)
        self.update_memory(output, context)
        return output

def main():
    """
    Main function to demonstrate the LoopPrevention algorithm.
    """
    # 1. Initialize the LoopPrevention object
    loop_prevention = LoopPrevention(embedding_model_name="sentence-transformers/all-MiniLM-L6-v2")

    # 2.  Example AI system (replace with your actual AI system)
    def dummy_ai_system(prompt: str, turn_number: int) -> str:
        """
        A dummy AI system that generates repetitive outputs for demonstration.
        """
        if turn_number < 3:
            return f"This is the AI response to: {prompt} (turn {turn_number})"
        elif turn_number < 6:
            return "I am repeating myself.  This is intentional."
        else:
            return "This is a new topic, but I might still repeat something."

    # 3.  Example conversation loop
    conversation = [
        "Hello, how are you?",
        "I am fine, thank you.",
        "What is the weather like today?",
        "What is the weather like today?",
        "What is the weather like today?",
        "Tell me more about the weather.",
        "The weather is nice.",
        "The weather is nice.",
        "The weather is nice."
    ]

    # 4.  Run the conversation through the loop prevention algorithm
    for i, turn in enumerate(conversation):
        ai_output = dummy_ai_system(turn, i)
        print(f"\nTurn {i}: User - '{turn}'")
        print(f"Turn {i}: AI (Raw) - '{ai_output}'")
        ai_output_processed = loop_prevention(ai_output, f"Conversation turn {i}, user said: {turn}")
        print(f"Turn {i}: AI (Processed) - '{ai_output_processed}'")
        time.sleep(1)  # Simulate some processing time

if __name__ == "__main__":
    main()
