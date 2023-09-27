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


class Taxonomy:

    def __new__(cls,
                backend='RAM',
                data_dir=None,
                logger=Log,
                db_user='',
                db_pass='',
                db_host_or_ip='localhost',
                db_name='taxonomy'):

        if backend in ('RAM', 'SQLite', 'PostgreSQL'):

            if backend == 'RAM':
                return TaxonomyRAM(data_dir, logger)

            elif backend == 'SQLite':
                return TaxonomySQL(data_dir, logger, backend)

            elif backend == 'PostgreSQL':
                return TaxonomySQL(data_dir, logger, backend,
                                   db_user, db_pass, db_host_or_ip, db_name)

        else:
            raise Exception(f'Invalid backend type: {backend}')


__all__ = ['Taxonomy']
