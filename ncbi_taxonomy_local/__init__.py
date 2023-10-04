"""Locally-cached NCBI Taxonomy Database for Python 3."""

from typing import Any, Union

from .taxonomy_base import Taxonomy
from .taxonomy_ram import TaxonomyRAM
from .taxonomy_sql import TaxonomySQL
from .utils import Log


class Tax:

    def __new__(cls,
                backend: str = 'RAM',
                data_dir: Union[str, None] = None,
                logger: Any = Log,
                db_user: str = '',
                db_pass: str = '',
                db_host_or_ip: str = 'localhost',
                db_name: str = 'taxonomy',
                check_for_updates: bool = False):

        if backend in ('RAM', 'SQLite', 'PostgreSQL'):

            if backend == 'RAM':
                return TaxonomyRAM(data_dir, logger, check_for_updates)

            elif backend == 'SQLite':
                return TaxonomySQL(data_dir, logger, backend,
                                   check_for_updates=check_for_updates)

            elif backend == 'PostgreSQL':
                return TaxonomySQL(data_dir, logger, backend,
                                   db_user, db_pass, db_host_or_ip, db_name,
                                   check_for_updates)

        else:
            raise Exception(f'Invalid backend type: {backend}')


__all__ = ['Tax', 'Taxonomy', 'TaxonomyRAM', 'TaxonomySQL']
