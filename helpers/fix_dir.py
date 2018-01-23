# r1

import os


def fix_dirs(output_dir, log_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    log_dir = os.path.join(output_dir, log_dir)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
