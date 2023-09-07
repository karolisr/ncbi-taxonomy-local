"""Locally-cached NCBI Taxonomy Database for Python 3."""

from datetime import datetime

from .utils import Log
from .taxonomy_ram import TaxonomyRAM
from .taxonomy_sql import TaxonomySQL

date_time = datetime.now()
y = str(date_time.year)

__version__ = '0.3.0'
__author__ = 'Karolis Ramanauskas'
__author_email__ = 'kraman2@uic.edu'
__description__ = 'Locally-cached NCBI Taxonomy Database for Python 3.'
__copyright__ = 'Copyright \u00A9 ' + __author__ + ', ' + y
__license__ = 'Creative Commons Attribution-ShareAlike 4.0 International ' \
              'License: cc-by-sa-4.0'
__url__ = 'https://github.com/karolisr/ncbi-taxonomy-local'


class Taxonomy(object):
    """
    Taxonomy.
    """

    def __new__(cls, backend='RAM', data_dir=None, logger=Log):
        backend = backend.upper()
        if backend in ('RAM', 'SQL'):
            if backend == 'RAM':
                TaxonomyRAM.init(data_dir=data_dir, logger=logger)
                return TaxonomyRAM
            elif backend == 'SQL':
                TaxonomySQL.init(data_dir=data_dir, logger=logger)
                return TaxonomySQL
        else:
            raise Exception(f'Invalid backend type: {backend}')

    # __init__ declaration is exactly the same as __new__ so Sphinx
    # docstring parser picks it up.
    def __init__(self, backend='RAM', data_dir=None, logger=Log):
        pass


__all__ = ['Taxonomy']
