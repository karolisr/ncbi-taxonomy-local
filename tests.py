#!/usr/bin/env python3

"""Rudimentary Testing"""

from ncbi_taxonomy_local import Taxonomy
tax = Taxonomy()
tax.init(data_dir_path='NCBI_TAXONOMY')
