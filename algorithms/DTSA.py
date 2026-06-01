import threading
import time
from typing import Dict, List, Callable, Any, Optional
from collections import deque

class Task:
    """
    Represents a task to be scheduled.
    """
    def __init__(self, task_id: str, task_type: str, resource_requirements: Dict[str, int],
                 dependencies: List[str], priority: int, arrival_time: float, estimated_duration: float):
        """
        Initializes a Task object.

        Args:
            task_id: Unique identifier for the task.
            task_type: Type of task (e.g., "preprocessing", "training", "inference").
            resource_requirements: Dictionary specifying the required resources
                (e.g., {"CPU": 4, "GPU": 1, "memory": 16}).
            dependencies: List of task IDs that must be completed before this task can start.
            priority: Priority of the task (higher value = higher priority).
            arrival_time: Time at which the task arrives in the system.
            estimated_duration: Estimated execution time of the task.
        """
        self.task_id = task_id
        self.type = task_type
        self.resource_requirements = resource_requirements
        self.dependencies = dependencies
        self.priority = priority
        self.arrival_time = arrival_time
        self.estimated_duration = estimated_duration
        self.start_time: Optional[float] = None  # Set when the task starts execution
        self.end_time: Optional[float] = None    # Set when the task finishes execution
        self.state = "pending"  # "pending", "running", "completed", "failed"

    def __repr__(self):
        return f"Task(id={self.task_id}, type={self.type}, state={self.state})"

class ResourceManager:
    """
    Manages the allocation and release of resources.
    """
    def __init__(self, total_resources: Dict[str, int]):
        """
        Initializes the ResourceManager.

        Args:
            total_resources: A dictionary specifying the total available resources
                (e.g., {"CPU": 100, "GPU": 8, "memory": 256}).
        """
        self.total_resources = total_resources
        self.available_resources = total_resources.copy()
        self.resource_lock = threading.Lock()  # Lock for thread-safe resource management

    def allocate_resources(self, task: Task) -> bool:
        """
        Allocates resources to a task.

        Args:
            task: The task requesting resources.

        Returns:
            True if resources are successfully allocated, False otherwise.
        """
        with self.resource_lock:
            for resource, required in task.resource_requirements.items():
                if resource not in self.available_resources or self.available_resources[resource] < required:
                    return False  # Not enough resources
            # Allocate resources
            for resource, required in task.resource_requirements.items():
                self.available_resources[resource] -= required
            return True

    def release_resources(self, task: Task):
        """
        Releases the resources allocated to a task.

        Args:
            task: The task that has finished execution.
        """
        with self.resource_lock:
            if task.start_time is not None:  # Only release if resources were allocated
                for resource, required in task.resource_requirements.items():
                    self.available_resources[resource] += required

    def get_resource_utilization(self) -> Dict[str, float]:
        """
        Calculates the current resource utilization.

        Returns:
            A dictionary representing the percentage of each resource that is currently in use.
        """
        with self.resource_lock:
            utilization = {}
            for resource, total in self.total_resources.items():
                used = total - self.available_resources[resource]
                utilization[resource] = (used / total) * 100 if total > 0 else 0.0
            return utilization

class TaskScheduler(threading.Thread):
    """
    Schedules and executes tasks dynamically.
    """
    def __init__(self, resource_manager: ResourceManager, scheduling_policy: str = "priority",
                 policy_function: Optional[Callable[[Task], float]] = None,
                 task_queue: Optional[deque] = None):
        """
        Initializes the TaskScheduler.

        Args:
            resource_manager: The ResourceManager object.
            scheduling_policy: The scheduling policy to use
                ("FCFS", "SRTF", "priority", "EDF").
            policy_function: A function that takes a Task object and returns a value
                used for scheduling (e.g., priority, remaining time, deadline).
            task_queue:  A queue to hold the tasks.
        """
        super().__init__()
        self.resource_manager = resource_manager
        self.scheduling_policy = scheduling_policy
        self.policy_function = policy_function
        self.task_queue = task_queue if task_queue is not None else deque()
        self.running_tasks = {}  # Dictionary of running tasks (task_id: Task)
        self.completed_tasks = []  # List of completed tasks
        self.shutdown_flag = False
        self.condition = threading.Condition()  # For waiting and notifying
        if scheduling_policy not in ["FCFS", "SRTF", "priority", "EDF", "LIST", "RL"]:
            raise ValueError(f"Invalid scheduling policy: {scheduling_policy}")
        if scheduling_policy in ["SRTF", "priority", "EDF", "LIST", "RL"] and policy_function is None:
            raise ValueError(f"Policy function must be provided for {scheduling_policy} scheduling.")

    def add_task(self, task: Task):
        """
        Adds a task to the task queue.

        Args:
            task: The Task object to add.
        """
        with self.condition:
            self.task_queue.append(task)
            self.condition.notify()  # Notify the scheduler thread that a new task is available

    def run(self):
        """
        Main loop of the scheduler thread.
        """
        while not self.shutdown_flag:
            with self.condition:
                if not self.task_queue:
                    self.condition.wait()  # Wait until a task arrives or shutdown
                    if self.shutdown_flag:
                        break  # Exit loop if shutdown was signaled while waiting

                # Select a task from the queue based on the scheduling policy
                task = self.select_next_task()
                if task is None:
                    continue  # No task selected (e.g., dependencies not met)

                # Check if resources are available
                if self.resource_manager.allocate_resources(task):
                    self.schedule_task(task)  # Schedule the task for execution
                #else:
                    #print(f"Task {task.task_id} waiting for resources...") #removed printing here

    def select_next_task(self) -> Optional[Task]:
        """
        Selects the next task to be executed based on the scheduling policy.

        Returns:
            The Task object to be executed, or None if no task is ready.
        """
        if not self.task_queue:
            return None

        if self.scheduling_policy == "FCFS":
            return self.task_queue.popleft()
        elif self.scheduling_policy == "SRTF":
            # Find the task with the shortest remaining time
            min_remaining_time = float('inf')
            selected_task = None
            for task in self.task_queue:
                remaining_time = task.estimated_duration - (time.time() - task.arrival_time) if task.start_time else task.estimated_duration
                if remaining_time < min_remaining_time:
                    min_remaining_time = remaining_time
                    selected_task = task
            if selected_task is not None:
                self.task_queue.remove(selected_task)  # Remove the selected task
            return selected_task
        elif self.scheduling_policy == "priority":
            # Find the task with the highest priority
            highest_priority_task = max(self.task_queue, key=self.policy_function)
            self.task_queue.remove(highest_priority_task)
            return highest_priority_task
        elif self.scheduling_policy == "EDF":
            # Find the task with the earliest deadline
            earliest_deadline_task = min(self.task_queue, key=self.policy_function)
            self.task_queue.remove(earliest_deadline_task)
            return earliest_deadline_task
        elif self.scheduling_policy == "LIST":
            #Basic List Scheduling Algorithm
            # 1. Sort the task queue based on the policy function (e.g., topological order, critical path)
            sorted_task_queue = sorted(self.task_queue, key=self.policy_function)
            # 2. Iterate through the sorted task queue
            for task in sorted_task_queue:
                # 3. Check if all dependencies are met
                dependencies_met = True
                for dependency_id in task.dependencies:
                    if dependency_id not in [t.task_id for t in self.completed_tasks]:
                        dependencies_met = False
                        break
                if dependencies_met:
                    self.task_queue.remove(task)
                    return task
            return None # Return None if no task is ready
        elif self.scheduling_policy == "RL":
            # Placeholder for Reinforcement Learning based scheduling
            # In a real implementation, an RL agent would select the task based on the current state
            # and a learned policy.  This is a complex topic and requires a separate design.
            # For this basic example, we'll just use a simple heuristic (e.g., shortest remaining time)
            min_remaining_time = float('inf')
            selected_task = None
            for task in self.task_queue:
                remaining_time = task.estimated_duration - (time.time() - task.arrival_time) if task.start_time else task.estimated_duration
                if remaining_time < min_remaining_time:
                    min_remaining_time = remaining_time
                    selected_task = task
            if selected_task is not None:
                self.task_queue.remove(selected_task)  # Remove the selected task
            return selected_task
        else:
            raise ValueError(f"Invalid scheduling policy: {self.scheduling_policy}")

    def schedule_task(self, task: Task):
        """
        Schedules a task for execution.

        Args:
            task: The Task object to schedule.
        """
        task.start_time = time.time()
        task.state = "running"
        self.running_tasks[task.task_id] = task
        print(f"Scheduled Task {task.task_id} ({task.type}) with resources {task.resource_requirements} at time {task.start_time:.2f}")

        # Create a thread to execute the task
        task_thread = threading.Thread(target=self.execute_task, args=(task,))
        task_thread.start()

    def execute_task(self, task: Task):
        """
        Simulates the execution of a task.  In a real system, this would involve
        invoking the appropriate AI model or computation.

        Args:
            task: The Task object to execute.
        """
        try:
            time.sleep(task.estimated_duration)  # Simulate task execution
            task.end_time = time.time()
            task.state = "completed"
            print(f"Task {task.task_id} ({task.type}) completed at time {task.end_time:.2f}")
            self.resource_manager.release_resources(task)
            with self.condition:
                del self.running_tasks[task.task_id]
                self.completed_tasks.append(task)
                self.condition.notify()  # Notify the scheduler thread
        except Exception as e:
            task.end_time = time.time()
            task.state = "failed"
            print(f"Task {task.task_id} ({task.type}) failed at time {task.end_time:.2f} with error: {e}")
            self.resource_manager.release_resources(task)
            with self.condition:
                del self.running_tasks[task.task_id]
                self.completed_tasks.append(task)
                self.condition.notify()  # Notify the scheduler thread
        finally:
            self.resource_manager.release_resources(task) # Ensure resources are released

    def get_running_tasks(self) -> List[Task]:
        """
        Returns a list of currently running tasks.
        """
        return list(self.running_tasks.values())

    def get_completed_tasks(self) -> List[Task]:
        """
        Returns a list of completed tasks.
        """
        return self.completed_tasks

    def shutdown(self):
        """
        Shuts down the scheduler thread.
        """
        with self.condition:
            self.shutdown_flag = True
            self.condition.notify()  # Wake up the scheduler thread
        self.join()  # Wait for the thread to terminate

def main():
    """
    Main function to demonstrate the dynamic task scheduling algorithm.
    """
    # 1. Define total resources
    total_resources = {"CPU": 100, "GPU": 8, "memory": 256}

    # 2. Create a ResourceManager
    resource_manager = ResourceManager(total_resources)

    # 3. Define a scheduling policy and policy function
    scheduling_policy = "LIST" #  "FCFS", "SRTF", "priority", "EDF", "LIST", "RL"
    def list_policy_function(task: Task) -> tuple[float, float]:
        """
        Example policy function for List Scheduling:  Sort by earliest arrival time, then longest duration
        """
        return (task.arrival_time, -task.estimated_duration)  # Sort by arrival, then descending duration

    # 4. Create a TaskScheduler
    # Ensure the policy_function returns a float, not a tuple
    def float_policy_function(task):
        result = list_policy_function(task)
        if isinstance(result, tuple):
            return float(result[0])  # or another logic to select the float value
        return float(result)
    scheduler = TaskScheduler(resource_manager, scheduling_policy, policy_function=float_policy_function)
    scheduler.start()  # Start the scheduler thread

    # 5. Create some example tasks
    tasks = [
        Task("task1", "training", {"CPU": 10, "GPU": 2, "memory": 32}, [], 3, time.time() + 1, 10),
        Task("task2", "inference", {"CPU": 5, "GPU": 1, "memory": 16}, [], 2, time.time() + 2, 5),
        Task("task3", "preprocessing", {"CPU": 20, "GPU": 0, "memory": 64}, [], 1, time.time() + 3, 8),
        Task("task4", "training", {"CPU": 15, "GPU": 2, "memory": 48}, ["task1"], 3, time.time() + 4, 12),  # Depends on task1
        Task("task5", "inference", {"CPU": 8, "GPU": 1, "memory": 24}, ["task2"], 2, time.time() + 5, 6),    # Depends on task2
        Task("task6", "postprocessing", {"CPU": 12, "GPU": 0, "memory": 32}, ["task3", "task4"], 1, time.time() + 6, 4), #Depends on task3 and task4
    ]

    # 6. Add tasks to the scheduler
    for task in tasks:
        scheduler.add_task(task)

    # 7. Wait for a while (simulate tasks being processed)
    time.sleep(30)

    # 8. Print running and completed tasks
    print("\nRunning Tasks:", scheduler.get_running_tasks())
    print("Completed Tasks:", scheduler.get_completed_tasks())

    # 9. Print resource utilization
    resource_utilization = resource_manager.get_resource_utilization()
    print("\nResource Utilization:")
    for resource, utilization in resource_utilization.items():
        print(f"  {resource}: {utilization:.2f}%")

    # 10. Shutdown the scheduler
    scheduler.shutdown()

if __name__ == "__main__":
    main()
