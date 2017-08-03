class Output:
    def __init__(self, can_write):
        if can_write:
            Output.print = print

    def print(*args):
        pass
