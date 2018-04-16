# Copyright 2017 Kensho Technologies, LLC.
import os


def in_same_dir(as_file, target_file):
    """Return an absolute path to a target file that is located in the same directory as as_file

    Args:
        as_file: File name (including __file__)
            Use the directory path of this file
        target_file: Name of the target file
    """
    return os.path.abspath(os.path.join(os.path.dirname(as_file), target_file))
