from functools import wraps
from sqlalchemy.orm import sessionmaker
from .config import init_local_storage, init_db
from .utils import Log


class TaxonomySQL:
    _taxonomy_initialized = False
    _Session: sessionmaker

    @classmethod
    def init(cls, data_dir=None, logger=Log):
        if cls._taxonomy_initialized is True:
            print('Already initialized.')
            return None
        if data_dir is None:
            paths = init_local_storage()
        else:
            paths = init_local_storage(dir_local_storage=data_dir)
        cls._Session = init_db(paths)
        cls._taxonomy_initialized = True

    @classmethod
    def _is_initialized(cls):
        return cls._taxonomy_initialized

    @staticmethod
    def _classmethod_check_initialized(func):
        """Is the class initialized?"""
        @classmethod
        @wraps(func)
        def wrapper_func(cls, *args, **kwargs):
            if cls._taxonomy_initialized is False:
                print('Run the init() method first.')
                return None
            value = func(cls, *args, **kwargs)
            return value
        return wrapper_func
