# module_loader.py
# Allow dynamic import functions from files
# r1

import importlib


class ModuleLoader:
    def __init__(self, file_name):
        self.code = importlib.import_module(file_name)
        self.version = getattr(self.code, 'VERSION', -1)

    def get(self, name):
        return getattr(self.code, name)

    def check_version(self, current_version):
        if current_version > self.version:
            return False

        return True
