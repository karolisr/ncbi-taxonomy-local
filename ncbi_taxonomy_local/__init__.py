# -*- coding: utf-8 -*-

"""Locally-cached NCBI Taxonomy Database for Python 3."""

from datetime import datetime
from ncbi_taxonomy_local.taxonomy import Taxonomy, taxonomy

date_time = datetime.now()
y = str(date_time.year)

__version__ = '0.1.1'
__author__ = 'Karolis Ramanauskas'
__author_email__ = 'kraman2@uic.edu'
__description__ = 'Locally-cached NCBI Taxonomy Database for Python 3.'
__copyright__ = 'Copyright \u00A9 ' + __author__ + ', ' + y
__license__ = 'Creative Commons Attribution-ShareAlike 4.0 International ' \
              'License: cc-by-sa-4.0'
__url__ = 'https://github.com/karolisr/ncbi-taxonomy-local'

__all__ = ['Taxonomy', 'taxonomy']
