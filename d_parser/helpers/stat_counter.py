from collections import defaultdict


class StatCounter:
    TASK_TOTAL = 'tasks_total'
    TASK_FACTORY = 'task_factory'

    def __init__(self):
        self.requests = defaultdict(list)
        self.tasks = defaultdict(list)
        self.exception = defaultdict(list)

    def add(self, code: int):
        self.requests[str(code)] += 1

    def exc(self, exception_type: str):
        self.exception[exception_type] += 1

    def add_task(self, task_type: str = None):
        if task_type:
            self.tasks[task_type] += 1

        self.tasks[StatCounter.TASK_TOTAL] += 1

    def done_task(self, task_type: str = None):
        if task_type:
            self.tasks[type] -= 1

        self.tasks[StatCounter.TASK_TOTAL] -= 1
