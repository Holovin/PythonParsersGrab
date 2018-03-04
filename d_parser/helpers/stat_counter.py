import operator
from collections import defaultdict
from functools import reduce


class StatCounter:
    TASK_TOTAL = 'tasks_total'
    TASK_TOTAL_NO_DROP = 'task_total_no_drop'
    TASK_FACTORY = 'task_factory'

    def __init__(self):
        self.requests = defaultdict(int)
        self.tasks = defaultdict(int)
        self.exception = defaultdict(int)
        self.messages = defaultdict(set)

    # add
    def add(self, code: int) -> None:
        self.requests[str(code)] += 1

    def exc(self, exception_type: str) -> None:
        self.exception[exception_type] += 1

    def msg(self, message_type: str, message: str) -> None:
        self.messages[message_type].add(message)

    # tasks
    def add_task(self, task_type: str = None) -> None:
        if task_type:
            self.tasks[task_type] += 1

        self.tasks[StatCounter.TASK_TOTAL] += 1
        self.tasks[StatCounter.TASK_TOTAL_NO_DROP] += 1

    def done_task(self, task_type: str = None) -> None:
        if task_type:
            self.tasks[task_type] -= 1

        self.tasks[StatCounter.TASK_TOTAL] -= 1

    def get_tasks(self, key) -> int:
        return self.tasks[key]

    # proc
    def process_stats(self) -> str:
        output = ''

        # stats
        if len(self.requests) > 0:
            requests_sorted = sorted(self.requests.items(), key=operator.itemgetter(1), reverse=True)
            requests_total = reduce(lambda a, b: a+b, self.requests.values())

            for row in requests_sorted:
                output += f'Code: {row[0]}, count: {row[1]/requests_total * 100}% ({row[1]} / {requests_total})\n'

        # exceptions
        exceptions_sorted = sorted(self.exception.items(), key=operator.itemgetter(1), reverse=True)

        for row in exceptions_sorted:
            output += f'Exception: {row[0]}, times {row[1]}\n'

        # messages
        messages_sorted = sorted(self.messages.items(), key=operator.itemgetter(1), reverse=True)

        for row in messages_sorted:
            output += f'Messages: {row[0]}, variations: \n'

            for index, sub_row in enumerate(row[1], start=1):
                output += f'\t[{index}] {sub_row}\n'

            output += '\n'

        return output
