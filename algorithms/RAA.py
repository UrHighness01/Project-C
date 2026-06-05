import torch
import torch.nn as nn
import time
import os
from typing import Dict, List, Callable, Any, Optional, Mapping
from collections import deque


def real_system_resources() -> Dict[str, float]:
    """The host's actual capacity, so allocation runs against real resources by default."""
    try:
        import sys as _sys
        from pathlib import Path as _Path
        _sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))
        from runtime.resources import resource_sample
        s = resource_sample()
        free_mem = s.get("mem_used_gb", 0.0) / max(s.get("mem_percent", 1.0) / 100.0, 1e-6)
    except Exception:
        free_mem = 8.0
    return {"CPU": float(os.cpu_count() or 1) * 100.0,
            "GPU": float(torch.cuda.device_count()) if torch.cuda.is_available() else 0.0,
            "memory": float(round(free_mem, 1))}


class ResourceAllocator:
    def __init__(
        self,
        total_resources: Optional[Mapping[str, float]] = None,
        strategy: str = "priority_based",
        priority_function: Optional[Callable[[Dict[str, Any]], float]] = None,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
    ):
        # Default to the host's real capacity when none is supplied
        if total_resources is None:
            total_resources = real_system_resources()
        """
        Initializes the ResourceAllocator.

        Args:
            total_resources: A mapping specifying the total available resources,
                e.g., {"CPU": 100, "GPU": 8, "memory": 256}.
            strategy: The resource allocation strategy to use.
                Options: "priority_based", "round_robin", "ml_based", "optimization_based"
            priority_function: A function that takes a task description and returns its priority
                (only used for "priority_based" strategy).
            device: The device to use for computations (e.g., "cpu", "cuda").
        """
        # Ensure all resource values are floats
        self.total_resources = {k: float(v) for k, v in total_resources.items()}
        self.available_resources = self.total_resources.copy()
        self.strategy = strategy
        self.priority_function = priority_function
        # Use deque for round robin, else list
        self.tasks = deque() if strategy == "round_robin" else []
        self.device = device
        self.resource_history = []  # Keep track of resource allocation over time

        if strategy not in ["priority_based", "round_robin", "ml_based", "optimization_based"]:
            raise ValueError(f"Invalid allocation strategy: {strategy}")

        if strategy == "priority_based" and priority_function is None:
            raise ValueError("Priority function must be provided for priority-based allocation.")

        # For ML-based allocation (simplified for this example)
        if strategy == "ml_based":
            self.model = self._create_ml_model().to(device)
            self.model.eval()  # Set to evaluation mode
            self.feature_scaler = self._create_feature_scaler()  # For scaling input features

        # For optimization-based allocation
        if strategy == "optimization_based":
            pass  #  Optimization is handled within allocate_resources

    def _create_ml_model(self) -> nn.Module:
        """
        Creates a simple neural network for ML-based resource prediction.
        (Simplified for demonstration purposes)

        Returns:
            A PyTorch nn.Module.
        """
        # Define a simple neural network architecture
        model = nn.Sequential(
            nn.Linear(3, 16),  # Example: 3 input features (CPU, GPU, Memory)
            nn.ReLU(),
            nn.Linear(16, 8),
            nn.ReLU(),
            nn.Linear(8, 3),  # Output: predicted CPU, GPU, Memory usage
        )
        return model

    def _create_feature_scaler(self):
        """
        Creates a scaler for input features for the ML model.
        (Simplified for demonstration)
        """
        # In a real scenario, you would fit a scaler (e.g., StandardScaler)
        # on your training data.  For this example, we just return a dummy scaler.
        class DummyScaler:
            def transform(self, x):
                return x  # Returns the input unchanged

            def inverse_transform(self, x):
                return x
        return DummyScaler()

    def add_task(self, task: Dict[str, Any]):
        """
        Adds a task to the list of pending tasks.

        Args:
            task: A dictionary describing the task, including its resource requirements
                and any other relevant information (e.g., priority, deadline).
                Example: {"id": "task1", "CPU": 10, "GPU": 2, "memory": 32, "priority": 2, "type": "training"}
        """
        if isinstance(self.tasks, deque):
            self.tasks.append(task)
        else:
            self.tasks.append(task)

    def allocate_resources(self) -> List[Dict[str, Any]]:
        """
        Allocates resources to the pending tasks based on the selected strategy.

        Returns:
            A list of dictionaries, where each dictionary represents an allocation
            for a task.  Returns an empty list if no tasks can be allocated.
            Example:
            [
                {"task_id": "task1", "CPU": 10, "GPU": 2, "memory": 32},
                {"task_id": "task2", "CPU": 5, "GPU": 1, "memory": 16},
            ]
        """
        allocations = []
        if not self.tasks:
            return allocations

        if self.strategy == "priority_based":
            # Sort tasks by priority (lower value means higher priority)
            sorted_tasks = sorted(self.tasks, key=self.priority_function)
            for task in sorted_tasks:
                allocation = self._allocate_task_resources(task)
                if allocation:
                    allocations.append(allocation)

        elif self.strategy == "round_robin":
            # Implement round-robin allocation (simplified)
            for _ in range(len(self.tasks)):
                task = self.tasks[0]
                allocation = self._allocate_task_resources(task)
                if allocation:
                    allocations.append(allocation)
                from collections import deque
                if not isinstance(self.tasks, deque):
                    self.tasks = deque(self.tasks)
                self.tasks.rotate(-1)  # Rotate the task list for the next allocation cycle

        elif self.strategy == "ml_based":
            # ML-based allocation (simplified)
            for task in list(self.tasks):
                allocation = self._allocate_task_resources_ml(task)
                if allocation:
                    allocations.append(allocation)

        elif self.strategy == "optimization_based":
            allocations = self._allocate_resources_optimization()

        else:  # Should not happen, but included for completeness
            raise ValueError(f"Invalid allocation strategy: {self.strategy}")
        self.resource_history.append(
            {
                "time": time.time(),
                "available_resources": self.available_resources.copy(),
                "allocations": allocations,
            }
        )
        return allocations

    def _allocate_task_resources(self, task: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """
        Helper function to allocate resources to a single task.  Checks for resource availability.

        Args:
            task: The task to allocate resources to.

        Returns:
            A dictionary representing the allocation for the task, or None if
            resources are insufficient.
        """
        allocation = {}
        for resource, required in task.items():
            if resource in self.total_resources and resource in self.available_resources:
                if self.available_resources[resource] >= float(required):
                    allocation[resource] = float(required)
                else:
                    return None  # Not enough resources for this task
            # Ignore resources not defined in total_resources
        if allocation:
            for resource, allocated in allocation.items():
                self.available_resources[resource] -= allocated
            allocation["task_id"] = task["id"]  # Add task ID to allocation
            if isinstance(self.tasks, deque):
                self.tasks.remove(task)
            else:
                self.tasks.remove(task)  # Remove the task from the pending list
            return allocation
        return None

    def _allocate_task_resources_ml(self, task: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """
        Allocates resources to a task using a machine learning model
        to predict resource usage.  Simplified for demonstration.

        Args:
            task: The task to allocate resources to.

        Returns:
            A dictionary representing the allocation, or None if resources are insufficient.
        """
        # 1. Prepare input features for the ML model (simplified example)
        task_features = torch.tensor(
            [task["CPU"], task["GPU"], task["memory"]], dtype=torch.float32
        ).to(self.device)
        # Scale the features (in a real scenario, use a trained scaler)
        scaled_features = self.feature_scaler.transform(task_features.unsqueeze(0))

        # 2. Predict resource usage using the ML model
        with torch.no_grad():
            predicted_usage = self.model(scaled_features).squeeze()
            predicted_usage = torch.clamp(predicted_usage, min=0)  # Ensure non-negative

        # Convert the prediction to a dictionary
        predicted_allocation = {
            "CPU": predicted_usage[0].item(),
            "GPU": predicted_usage[1].item(),
            "memory": predicted_usage[2].item(),
        }

        # 3. Check resource availability and allocate
        allocation = {}
        for resource, predicted in predicted_allocation.items():
            if (
                resource in self.total_resources
                and resource in self.available_resources
                and self.available_resources[resource] >= predicted
            ):
                allocation[resource] = predicted
            else:
                return None  # Not enough resources

        if allocation:
            for resource, allocated in allocation.items():
                self.available_resources[resource] -= allocated
            allocation["task_id"] = task["id"]
            self.tasks.remove(task)
            return allocation
        return None

    def _allocate_resources_optimization(self) -> List[Dict[str, Any]]:
        """
        Allocates resources using an optimization-based approach (simplified).
        This example uses a very basic greedy approach for demonstration.
        In a real-world scenario, you'd use a proper optimization library
        (e.g., scipy.optimize) and formulate an appropriate objective function
        and constraints.

        Returns:
            A list of allocations.
        """
        allocations = []
        # Sort tasks by some criteria (e.g., shortest job first, highest priority)
        sorted_tasks = sorted(list(self.tasks), key=lambda t: t["CPU"])  # Example: Sort by CPU需求
        for task in sorted_tasks:
            allocation = self._allocate_task_resources(task)  # Reuse the helper
            if allocation:
                allocations.append(allocation)
        return allocations

    def get_resource_utilization(self) -> Dict[str, float]:
        """
        Calculates the current resource utilization.

        Returns:
            A dictionary representing the percentage of each resource that is currently in use.
        """
        utilization = {}
        for resource, total in self.total_resources.items():
            if resource in self.available_resources:
                utilized = total - self.available_resources[resource]
                utilization[resource] = (utilized / total) * 100
            else:
                utilization[resource] = 0.0  # Or raise an error?
        return utilization

    def display_resource_status(self):
        """
        Displays the current resource status (available and utilization).
        """
        print("Current Resource Status:")
        for resource, total in self.total_resources.items():
            print(f"  {resource}: Available = {self.available_resources[resource]:.2f}, Total = {total:.2f}")
        utilization = self.get_resource_utilization()
        print("  Utilization:")
        for resource, utilization_percent in utilization.items():
            print(f"    {resource}: {utilization_percent:.2f}%")

    def get_resource_history(self) -> List[Dict[str, Any]]:
        """
        Returns the history of resource allocation.

        Returns:
            A list of dictionaries, where each dictionary represents the resource
            allocation state at a given time.
        """
        return self.resource_history

def main():
    """
    Main function to demonstrate the ResourceAllocator.
    """
    # 1. Define total resources
    total_resources = {"CPU": 100.0, "GPU": 8.0, "memory": 256.0}  # Example resources

    # 2. Create a ResourceAllocator instance
    # Example: Using priority-based allocation with a simple priority function
    def task_priority(task):
        # Lower number = higher priority.  Example: prioritize training jobs.
        if task["type"] == "training":
            return 1
        elif task["type"] == "inference":
            return 2
        else:
            return 3

    allocator = ResourceAllocator(
        total_resources, strategy="priority_based", priority_function=task_priority
    )

    # 3. Define some example tasks
    tasks = [
        {"id": "task1", "CPU": 10, "GPU": 2, "memory": 32, "type": "training"},
        {"id": "task2", "CPU": 5, "GPU": 1, "memory": 16, "type": "inference"},
        {"id": "task3", "CPU": 20, "GPU": 3, "memory": 64, "type": "training"},
        {"id": "task4", "CPU": 8, "GPU": 1, "memory": 24, "type": "inference"},
        {"id": "task5", "CPU": 12, "GPU": 0, "memory": 40, "type": "batch"},
    ]

    # 4. Add tasks to the allocator
    for task in tasks:
        allocator.add_task(task)

    # 5. Allocate resources
    allocations = allocator.allocate_resources()

    # 6. Display the allocations
    print("Allocations:")
    if allocations:
        for allocation in allocations:
            print(f"  Allocated to task {allocation['task_id']}: {allocation}")
    else:
        print("  No resources could be allocated.")

    # 7. Display resource status
    allocator.display_resource_status()

    # 8. Get resource history
    history = allocator.get_resource_history()
    print("\nResource Allocation History:")
    for record in history:
        print(f"  Time: {record['time']:.2f}")
        print(f"    Available Resources: {record['available_resources']}")
        print(f"    Allocations: {record['allocations']}")

    # Example using ML-based allocation (requires a trained model and data)
    # 9.  Create a new allocator with ML strategy
    ml_allocator = ResourceAllocator(total_resources, strategy="ml_based")
    for task in tasks:
        ml_allocator.add_task(task)
    ml_allocations = ml_allocator.allocate_resources()
    print("\nML Allocations")
    if ml_allocations:
        for allocation in ml_allocations:
            print(f"  Allocated to task {allocation['task_id']}: {allocation}")
    else:
        print("No resources could be allocated.")
    ml_allocator.display_resource_status()

if __name__ == "__main__":
    main()
