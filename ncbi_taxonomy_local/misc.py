"""Miscellaneous helper functions."""

import hashlib
from os import makedirs
from os.path import abspath
from os.path import exists as ope
from os.path import expanduser
from subprocess import run as subp_run
from urllib.request import urlretrieve


def run(cmd, in_txt=None, capture=True, cwd=None, do_not_raise=False):
    out = subp_run(cmd, input=in_txt, capture_output=capture, cwd=cwd,
                   text=True)
    if do_not_raise is False and out.returncode > 0:
        raise Exception(out.stderr)
    return out


def download_file(url, local_path):
    local_path = abspath(expanduser(local_path))
    try:
        urlretrieve(url, local_path)
    except Exception:
        try:
            run(['curl', '-L', '-o', local_path, url])
        except Exception:
            try:
                run(['wget', '-O', local_path, url])
            except Exception as e:
                print(e)


def make_dirs(path):
    path = abspath(expanduser(path))
    if not ope(path):
        makedirs(path)
    return path


def generate_md5_hash_for_file(file_path):
    with open(file_path, 'rb') as f:
        return_value = hashlib.md5(f.read()).hexdigest()
    return return_value


def extract_md5_hash(file_path):
    with open(file_path, 'r') as f_md5:
        line = f_md5.readline()
        md5_reported = line.split(' ')[0]
    return md5_reported
