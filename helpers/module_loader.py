# module_loader.py
# Allow dynamic import functions from files
# r1

import importlib


class ModuleLoader:
    def __init__(self, file_name):
        self.code = importlib.import_module(file_name)

    def get(self, name):
        return getattr(self.code, name)
