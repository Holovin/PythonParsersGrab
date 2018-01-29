import operator
from collections import defaultdict
from functools import reduce


class StatCounter:
    TASK_TOTAL = 'tasks_total'
    TASK_FACTORY = 'task_factory'

    def __init__(self):
        self.requests = defaultdict(int)
        self.tasks = defaultdict(int)
        self.exception = defaultdict(int)

    def add(self, code: int) -> None:
        self.requests[str(code)] += 1

    def exc(self, exception_type: str) -> None:
        self.exception[exception_type] += 1

    def add_task(self, task_type: str = None) -> None:
        if task_type:
            self.tasks[task_type] += 1

        self.tasks[StatCounter.TASK_TOTAL] += 1

    def done_task(self, task_type: str = None) -> None:
        if task_type:
            self.tasks[task_type] -= 1

        self.tasks[StatCounter.TASK_TOTAL] -= 1

    def get_tasks(self) -> dict:
        return self.tasks[StatCounter.TASK_TOTAL]

    def get_factory_tasks(self) -> dict:
        return self.tasks[StatCounter.TASK_FACTORY]

    def process_stats(self) -> str:
        output = ''

        requests_sorted = sorted(self.requests.items(), key=operator.itemgetter(1), reverse=True)
        requests_total = reduce(lambda a, b: a+b, self.requests.values())

        for row in requests_sorted:
            output += f'Code: {row[0]}, count: {row[1]/requests_total * 100}% ({row[1]} / {requests_total})\n'

        exceptions_sorted = sorted(self.exception.items(), key=operator.itemgetter(1), reverse=True)

        for row in exceptions_sorted:
            output += f'Exception: {row[0]}, times {row[1]}\n'

        return output
