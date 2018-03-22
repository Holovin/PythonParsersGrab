import operator
from collections import defaultdict
from functools import reduce
from math import floor


class StatCounter:
    MSG_UNKNOWN_COUNT = 'Unknown count'
    MSG_UNKNOWN_PRICE = 'Unknown price'
    MSG_WRONG_PRICE = 'Wrong price'
    MSG_UNKNOWN_STATUS = 'Unknown status'
    MSG_UNKNOWN_STORE = 'Unknown store'
    MSG_UNKNOWN_SKU = 'Unknown sku vendor code'
    MSG_POSSIBLE_WARN = 'Possible warning?'

    TASK_TOTAL = 'tasks_total'
    TASK_TOTAL_NO_DROP = 'task_total_no_drop'
    TASK_FACTORY = 'task_factory'

    def __init__(self):
        self.requests = defaultdict(int)
        self.tasks = defaultdict(int)
        self.exceptions = defaultdict(int)
        self.messages = defaultdict(set)

    # add
    def add(self, code: int) -> None:
        self.requests[str(code)] += 1

    def exc(self, exception_type: str) -> None:
        self.exceptions[exception_type] += 1

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
        output = '\n---\t STATS \t---\n'

        # check: if spider missed some check_body_* sections - this condition will be triggered
        if self.requests['200'] < floor(self.tasks[StatCounter.TASK_TOTAL_NO_DROP] * 0.95):
            output += '\n>>> WARN: Seems you missed [if check_body_errors] section in some tasks <<<\n'

        # stats
        if len(self.requests) > 0:
            requests_sorted = sorted(self.requests.items(), key=operator.itemgetter(1), reverse=True)
            requests_total = reduce(lambda a, b: a+b, self.requests.values())

            output += 'Codes:\n'

            for row in requests_sorted:
                output += f'\t[{row[0]}] Times: {row[1]/requests_total * 100}% ({row[1]} / {requests_total})\n'

        # exceptions
        if len(self.exceptions) > 0:
            output += 'Exceptions:\n'

            exceptions_sorted = sorted(self.exceptions.items(), key=operator.itemgetter(1), reverse=True)

            for row in exceptions_sorted:
                output += f'\t[{row[0]}] Times: {row[1]}\n'

        # messages
        if len(self.messages) > 0:
            output += 'Messages:\n'

            messages_sorted = sorted(self.messages.items(), key=operator.itemgetter(1), reverse=True)

            for row in messages_sorted:
                output += f'\tType: {row[0]}, variations: \n'

                for index, sub_row in enumerate(row[1], start=1):
                    output += f'\t\t[{index}] {sub_row}\n'

        output += '---   ---   ---\n'

        return output
