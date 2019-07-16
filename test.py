# -*- coding: utf-8 -*-

"""Rudimentary Testing"""

from ncbi_taxonomy_local import Taxonomy
Taxonomy.init(data_dir_path='~/NCBI_TAXONOMY')
Taxonomy.update()
