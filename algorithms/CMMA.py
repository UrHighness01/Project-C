import numpy as np
from collections import deque
import time
from typing import List, Dict

class ContextualMemory:
    def __init__(self, stm_capacity=5, ltm_capacity=100, embedding_model=None):
        """
        Initializes the ContextualMemory.

        Args:
            stm_capacity: Capacity of the short-term memory.
            ltm_capacity: Capacity of the long-term memory.
            embedding_model:  Model to generate embeddings for semantic similarity.
        """
        self.stm = deque(maxlen=stm_capacity)
        self.ltm = []  # List of tuples: (timestamp, information, embedding)
        self.ltm_capacity = ltm_capacity
        self.embedding_model = embedding_model  # e.g., SentenceTransformer
        self.forgetting_rate = 0.95  # Example forgetting rate

    def get_turn_embedding(self, turn):
        if self.embedding_model:
            return self.embedding_model.encode(turn)
        return None

    def update_stm(self, turn):
        """
        Updates the short-term memory with a new turn.

        Args:
            turn: The new turn in the conversation (string).
        """
        self.stm.append(turn)

    def update_ltm(self, info):
        """
        Updates the long-term memory with new information.

        Args:
            info: The information to add to the LTM (string).
        """
        if len(self.ltm) >= self.ltm_capacity:
            self.ltm.pop(0)  # Remove the oldest entry
        embedding = self.get_turn_embedding(info)
        self.ltm.append((time.time(), info, embedding))

    def retrieve_context(self, current_turn, num_relevant_ltm=3):
        """
        Retrieves relevant context from STM and LTM.

        Args:
            current_turn: The current turn in the conversation (string).
            num_relevant_ltm:  Number of relevant LTM entries to retrieve.

        Returns:
            A list of strings representing the combined context from STM and LTM.
        """
        stm_context = list(self.stm)
        ltm_context = self.retrieve_relevant_ltm(current_turn, num_relevant_ltm)
        return stm_context + ltm_context

    def calculate_similarity(self, embedding1, embedding2):
        """Calculates cosine similarity between two embeddings."""
        if embedding1 is None or embedding2 is None:
            return 0.0
        return np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))

    def retrieve_relevant_ltm(self, current_turn, num_relevant_ltm):
        """
        Retrieves relevant information from LTM based on semantic similarity.

        Args:
            current_turn: The current turn in the conversation (string).
             num_relevant_ltm:  Number of relevant LTM entries to retrieve.

        Returns:
            A list of strings representing the relevant information from LTM.
        """
        if not self.ltm or not self.embedding_model:
            return []  # Return empty list if LTM is empty or no embedding model

        current_embedding = self.get_turn_embedding(current_turn)
        scored_ltm = []
        for timestamp, info, embedding in self.ltm:
            similarity = self.calculate_similarity(current_embedding, embedding)
            scored_ltm.append((timestamp, info, similarity))

        # Sort by similarity (most similar first)
        scored_ltm.sort(key=lambda x: x[2], reverse=True)
        return [info for timestamp, info, similarity in scored_ltm[:num_relevant_ltm]]

    def generate_response(self, current_turn, model):
        """
        Generates a response based on the retrieved context.

        Args:
            current_turn: The current turn in the conversation (string).
            model: The language model to use for response generation.

        Returns:
            A string representing the generated response.
        """
        context = self.retrieve_context(current_turn)
        # Use a language model with the context to generate a response.
        prompt = "Context: " + " ".join(context) + "\nUser: " + current_turn + "\nAI: "
        response = model(prompt)  # Replace with actual model call
        return response

    def memory_maintenance(self):
        """
        Performs memory maintenance operations, such as summarizing STM and removing outdated information from LTM.
        """
        # 1. Summarize STM and add it to LTM (Conceptual)
        if len(self.stm) > 3:  # Example: Only summarize if STM has more than 3 turns
            summary = self.summarize_stm()  #  Replace with a summarization function
            self.update_ltm(summary)

        # 2. Remove outdated information from LTM
        self.ltm = [(t, i, e) for t, i, e in self.ltm if t > time.time() - 3600]  # Keep last hour
        self.ltm = [(t, i, e) for t, i, e in self.ltm if np.random.default_rng(13).random() > self.forgetting_rate]

    def summarize_stm(self):
        """
        Summarizes the short-term memory.  This is a placeholder.

        Returns:
           A string summarizing the short term memory
        """
        return "Summary of previous turns: " + " ".join(self.stm)  # Replace with actual summarization

def evaluate_memory(memory, turns, model, num_relevant_ltm=3):
    """
    Evaluates the performance of the memory management algorithm.

    Args:
        memory: The ContextualMemory object.
        turns: A list of turns in the conversation (list of strings).
        model:  The language model used for response generation.
        num_relevant_ltm: Number of relevant LTM entries to retrieve.

    Returns:
        A dictionary containing evaluation metrics.
    """
    metrics = {
        "coherence": [],
        "relevance": [],
        "context_recall": [],
        "response_lengths": [],
    }

    #  A list to store the dialogue history
    dialogue_history = []

    for i, turn in enumerate(turns):
        memory.update_stm(turn)
        memory.update_ltm(turn)  #  Update LTM with relevant info, not just the turn
        response = memory.generate_response(turn, model) #  Pass the model.
        dialogue_history.append((turn, response))  # Keep history

        #  Coherence metric (example: average similarity of consecutive responses)
        if i > 0:
            previous_response = dialogue_history[i-1][1]
            response_embedding = memory.get_turn_embedding(response)
            previous_response_embedding = memory.get_turn_embedding(previous_response)
            similarity = memory.calculate_similarity(response_embedding, previous_response_embedding)
            metrics["coherence"].append(similarity)

        # Relevance metric (example: similarity of response to current turn)
        response_embedding = memory.get_turn_embedding(response)
        turn_embedding = memory.get_turn_embedding(turn)
        relevance = memory.calculate_similarity(response_embedding, turn_embedding)
        metrics["relevance"].append(relevance)

        #  Context recall (example: check if response uses information from LTM)
        context = memory.retrieve_context(turn, num_relevant_ltm)
        context_recall = 0
        for item in context:
            if item in response:  # Very basic check, improve as needed
                context_recall = 1
                break
        metrics["context_recall"].append(context_recall)
        metrics["response_lengths"].append(len(response))

        memory.memory_maintenance()

    #  Calculate averages for the metrics
    for key in metrics:
        for key in metrics:
            metrics[key] = [np.mean(metrics[key])] if metrics[key] else [0.0]

    return metrics

def main():
    """
    Main function to demonstrate and evaluate the contextual memory management algorithm.
    """
    # 1. Initialize a dummy language model (replace with your actual model)
    class DummyModel:
        def __call__(self, prompt):
            return "This is a dummy response to: " + prompt
    dummy_model = DummyModel()

    # 2. Initialize the contextual memory
    memory = ContextualMemory(embedding_model=None) #  You can replace None with a real embedding model

    # 3. Define a sample conversation
    turns = [
        "Hello, how are you today?",
        "I'm doing well, thank you. What can you do?",
        "I can answer questions and have conversations. What is the capital of France?",
        "The capital of France is Paris. Can you tell me about its history?",
        "Paris has a rich history dating back to the Roman Empire...",
        "What is the current population of Paris?",
        "The population of Paris is approximately 2.1 million.",
        "Thank you for the information.",
        "You're welcome. Is there anything else I can help you with?",
        "No, that's all for now. Goodbye.",
    ]

    # 4. Evaluate the memory management
    print("Evaluating Memory...")
    start_time = time.time()
    evaluation_metrics = evaluate_memory(memory, turns, dummy_model) #  Pass the dummy model
    end_time = time.time()
    print(f"Evaluation took {end_time - start_time:.2f} seconds")

    # 5. Print the evaluation metrics
    print("\nEvaluation Metrics:")
    for key, value in evaluation_metrics.items():
        print(f"  {key}: {value:.4f}")

    # Example of a longer conversation
    long_turns = [
        "Hi, I'd like to book a flight to London.",
        "Sure, what date would you like to travel?",
        "I'd like to leave on July 10th.",
        "Okay, and what is your departure city?",
        "I'll be leaving from New York.",
        "Do you have a preferred airline?",
        "Yes, I'd prefer to fly with British Airways.",
        "Okay, let me check availability for British Airways flights from New York to London on July 10th.",
        "Great, thank you.",
        "Okay, there are three British Airways flights available. One departs at 8 AM, one at 12 PM, and one at 4 PM.",
        "I'll take the 12 PM flight.",
        "Okay, and what is your name and date of birth for the booking?",
        "My name is John Smith and my date of birth is January 1, 1990.",
        "Okay, John Smith, I have booked you on the British Airways flight from New York to London departing on July 10th at 12 PM.",
        "Can I also book a hotel room in London?",
        "Certainly, what dates will you need the hotel room?",
        "I will need it from July 10th to July 13th.",
        "Okay, and what part of London would you like to stay in?",
        "I would like to stay in the city center.",
        "Okay, let me check availability for hotels in London city center from July 10th to July 13th.",
        "Great.",
        "Okay, I have found several hotels. There is The Ritz, The Savoy, and The Churchill Hotel.",
        "I will stay at The Savoy.",
        "Okay, John Smith, I have booked you a room at The Savoy Hotel in London from July 10th to July 13th.",
        "Excellent. How much is the total cost for the flight and hotel?",
        "The total cost is $2000.",
        "Okay, that sounds good. Please proceed with the booking.",
        "Okay, your flight and hotel are booked. You will receive a confirmation email shortly.",
        "Thank you for your help.",
        "You're welcome. Have a great trip!",
    ]
    print("\n\nLonger Conversation Evaluation")
    memory = ContextualMemory(embedding_model=None)
    long_evaluation_metrics = evaluate_memory(memory, long_turns, dummy_model, num_relevant_ltm=5)
    print("Longer Conversation Metrics")
    for key, value in long_evaluation_metrics.items():
        print(f"{key}: {value:.4f}")

if __name__ == "__main__":
    main()
