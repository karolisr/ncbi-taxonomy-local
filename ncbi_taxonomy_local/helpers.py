# -*- coding: utf-8 -*-

"""Input/output operations."""

import hashlib
import os

from subprocess import PIPE
from subprocess import Popen

from urllib.request import urlretrieve


def call(cmd, stdout=PIPE, stderr=PIPE, cwd=None):  # noqa
    p = Popen(cmd, stdout=stdout, stderr=stderr, cwd=cwd)
    out, err = p.communicate()
    return out, err


def download_file(url, local_path):  # noqa
    try:
        urlretrieve(url, local_path)
    except Exception:
        try:
            call(['/usr/bin/curl', '-L', '-o', local_path, url])
        except Exception:
            try:
                call(['wget', '-O', local_path, url])
            except Exception:
                pass
                # print("\nDownload operation failed.")


def make_dir(path):  # noqa
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def generate_md5_hash_for_file(file_path):  # noqa
    return_value = None
    with open(file_path, 'rb') as f:
        return_value = hashlib.md5(f.read()).hexdigest()
    return return_value


def extract_md5_hash(file_path):  # noqa
    md5_reported = None
    with open(file_path, 'r') as f_md5:
        line = f_md5.readline()
        md5_reported = line.split(' ')[0]
    return md5_reported
