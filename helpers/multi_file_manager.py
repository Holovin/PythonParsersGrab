from contextlib import contextmanager


@contextmanager
def multi_file_manager(files, mode, newline, encoding):
    # https://stackoverflow.com/a/21683192

    files = [open(file, mode, newline, encoding) for file in files]
    yield files

    for file in files:
        file.close()
