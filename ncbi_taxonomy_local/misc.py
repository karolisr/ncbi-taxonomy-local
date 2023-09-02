"""Miscellaneous helper functions."""

import hashlib
from os import makedirs
from os.path import abspath
from os.path import exists as ope
from os.path import expanduser
from subprocess import run as subp_run, CalledProcessError, CompletedProcess
from urllib.request import urlretrieve


def run(cmd, in_txt=None, capture=True, cwd=None, do_not_raise=False) -> CompletedProcess[str]:
    """
    Execute a command in a subprocess.

    Parameters:
    cmd (list): The command to run.
    in_txt (str, optional): The input text to pass to the command. Defaults to None.
    capture (bool, optional): Whether to capture the command's output. Defaults to True.
    cwd (str, optional): The working directory to run the command in. Defaults to None.
    do_not_raise (bool, optional): Whether to suppress errors. If False, an exception is raised when the command returns a non-zero exit code. Defaults to False.

    Returns:
    subprocess.CompletedProcess: The result of the command execution.
    """
    result = subp_run(cmd, input=in_txt, capture_output=capture, cwd=cwd,
                      text=True)
    if do_not_raise is False and result.returncode > 0:
        raise CalledProcessError(result.returncode, cmd, output=result.stdout,
                                 stderr=result.stderr)
    return result


def download_file(url, local_path):
    """
    Download a file from a given URL to a local path using different methods.

    Parameters:
    url (str): The URL of the file to download.
    local_path (str): The local path where the file should be saved.

    Returns:
    None
    """
    local_path = abspath(expanduser(local_path))

    download_funcs = [
        lambda: urlretrieve(url, local_path),
        lambda: run(['curl', '-L', '-o', local_path, url]),
        lambda: run(['wget', '-O', local_path, url])
    ]

    for i, method in enumerate(download_funcs):
        try:
            method()
            break
        except Exception as e:
            if i == len(download_funcs) - 1:
                print(e)


def make_dirs(path):
    """
    Create directories for the given path if they do not exist.

    Parameters:
    path (str): The path for which directories should be created.

    Returns:
    str: The absolute path after expanding user home directories.
    """
    path = abspath(expanduser(path))
    if not ope(path):
        try:
            makedirs(path)
        except OSError as e:
            print(f"Error creating directories: {e}")
    return path


def generate_md5_hash_for_file(file_path):
    """
    Generate an MD5 hash for a file.

    Parameters:
    file_path (str): Path to the file.

    Returns:
    str: The MD5 hash of the file content.
    """
    md5_hash = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    except IOError as e:
        print(f"Error opening or reading file: {e}")
        return ""


def extract_md5_hash(file_path):
    """
    Extract the MD5 hash from a file.

    Parameters:
    file_path (str): Path to the file.

    Returns:
    str: The MD5 hash reported in the file.
    """
    try:
        with open(file_path, 'r') as f_md5:
            line = f_md5.readline()
            if line:
                parts = line.split(' ')
                if parts:
                    return parts[0]
    except IOError as e:
        print(f"Error opening or reading file: {e}")
    return ""
