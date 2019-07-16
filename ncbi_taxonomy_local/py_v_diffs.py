# -*- coding: utf-8 -*-

"""Manages Python 2 and Python 3 differences."""

import sys


def python_version():
    """
    Determine the Python version.
    """
    py_v_hex = sys.hexversion

    py_v_1 = sys.version_info[0]
    py_v_2 = sys.version_info[1]
    py_v_3 = sys.version_info[2]

    py_v_str = '{v0}.{v1}.{v2}'.format(v0=py_v_1, v1=py_v_2, v2=py_v_3)

    return py_v_hex, py_v_str


_py_v_hex, py_v_str = python_version()

if _py_v_hex >= 0x03000000:
    from urllib.request import urlretrieve # noqa
    unicode = str

elif _py_v_hex < 0x03000000:
    from urllib import urlretrieve # noqa
