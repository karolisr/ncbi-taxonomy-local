from abc import ABC, abstractmethod
from collections.abc import Collection, Sequence
from functools import partial, wraps
from itertools import dropwhile, takewhile, zip_longest
from operator import eq, ne
from typing import Any, Union

from .config import init_local_storage
from .errors import NameClassInvalidError, TaxIdInvalidError, TaxIdNotInDBError
from .ncbi import (codons_from_gc_prt_file, parse_gencode_dump,
                   update_ncbi_taxonomy_data)
from .utils import Log

NAME_CLASSES = {
    'acronym',
    'anamorph',
    'authority',
    'blast name',
    'common name',
    'equivalent name',
    'genbank acronym',
    'genbank anamorph',
    'genbank common name',
    'genbank synonym',
    'in-part',
    'includes',
    'misnomer',
    'misspelling',
    'scientific name',
    'synonym',
    'teleomorph',
    'type material',
}

TAXIDS_WITH_PLASTIDS = {
    2763,
    3027,
    5752,
    33090,
    33682,
    38254,
    136087,
    554296,
    554915,
    556282,
    1401294,
    2489521,
    2598132,
    2608109,
    2608240,
    2611341,
    2611352,
    2683617,
    2686027,
    2698737,
}


def name_variations(name: str) -> set[str]:
    name_alt_1 = name[0].upper() + name[1:]
    name_alt_2 = name[0].lower() + name[1:]
    return {name, name_alt_1, name_alt_2}


def path_between_lineages(ln1: Sequence[Any], ln2: Sequence[Any]) -> list[Any]:
    shared = takewhile(lambda x: eq(x[0], x[1]), zip(ln1, ln2))
    diff = dropwhile(lambda x: eq(x[0], x[1]), zip_longest(ln1, ln2,
                                                           fillvalue=-1))
    paths = tuple(zip(*diff))
    return list(
        filter(partial(ne, -1),
               tuple(reversed(paths[0])) + (tuple(shared)[-1][0],) + paths[1]))


def _check_initialized(func):
    @wraps(func)
    def wrapper_func(cls, *args, **kwargs):
        if cls._taxonomy_initialized is False:
            print('Run the init() method first.')
            return
        return func(cls, *args, **kwargs)
    return wrapper_func


class Taxonomy(ABC):

    _logger = Log
    _taxonomy_initialized: bool = False
    _data_dir: Union[str, None] = None
    _paths: Union[dict[str, str], None] = None
    _root_taxid: int = 1
    _name_classes = NAME_CLASSES
    _codons = list()

    _gen_code_id_name_dict = dict()
    _gen_code_id_translation_table_dict = dict()
    _gen_code_id_start_codons_dict = dict()

    # ----------------------------------------------------------------------
    def __new__(cls, data_dir=None, logger=Log):
        super().__new__(cls)
        cls._data_dir = data_dir
        cls._logger = logger
        return cls

    @classmethod  # --------------------------------------------------------
    def init(cls):
        if cls._taxonomy_initialized is True:
            cls._logger.inf('Already initialized.')
            return 1
        if cls._data_dir is None:
            paths = init_local_storage()
        else:
            paths = init_local_storage(dir_local_storage=cls._data_dir)
        cls._paths = paths
        cls.update()
        return 0

    @classmethod  # --------------------------------------------------------
    def update(cls, check_for_updates=False):

        if cls._paths is None:
            cls._logger.inf('Run the init() method first.')
            return 'not_initialized'

        download_taxdmp = update_ncbi_taxonomy_data(
            taxdmp_path=cls._paths['dir_taxdmp'],
            force_redownload=False,
            check_for_updates=check_for_updates,
            logger=cls._logger)

        if download_taxdmp is False:
            if cls._taxonomy_initialized is True:
                return 'no_changes'

        cls._codons = codons_from_gc_prt_file(cls._paths['file_gc'])

        parse_gencode_dump_result = parse_gencode_dump(
            cls._paths['file_gencode'])

        cls._gen_code_id_name_dict = parse_gencode_dump_result[0]
        cls._gen_code_id_translation_table_dict = parse_gencode_dump_result[1]
        cls._gen_code_id_start_codons_dict = parse_gencode_dump_result[2]

    @classmethod  # --------------------------------------------------------
    def name_classes(cls):
        return cls._name_classes

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def codons(cls):
        return cls._codons

    # **********************************************************************
    # Operations on integer taxids.
    # **********************************************************************

    @classmethod  # --------------------------------------------------------
    @abstractmethod
    def taxid_deleted(cls, taxid: int) -> bool:
        ...

    @classmethod  # --------------------------------------------------------
    @abstractmethod
    def taxid_merged(cls, taxid: int) -> bool:
        ...

    @classmethod  # --------------------------------------------------------
    @abstractmethod
    def taxid_active(cls, taxid: int) -> bool:
        ...

    @classmethod  # --------------------------------------------------------
    @abstractmethod
    def updated_taxid(cls, taxid: int) -> int:
        ...

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def taxid_in_db(cls, taxid: int):
        taxid_in_db = False
        if cls.updated_taxid(taxid) >= -1:
            taxid_in_db = True
        return taxid_in_db

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def taxid_in_db_raise(cls, taxid: int):
        if cls.taxid_in_db(taxid) is False:
            message = f'{taxid}'
            raise TaxIdNotInDBError(message)

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def taxid_valid(cls, taxid: int) -> bool:
        taxid_valid = False
        if cls.updated_taxid(taxid) >= 0:
            taxid_valid = True
        return taxid_valid

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def taxid_valid_raise(cls, taxid: int):
        if cls.taxid_valid(taxid) is False:
            message = f'{taxid}'
            raise TaxIdInvalidError(message)

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def root_taxid(cls) -> int:
        return cls._root_taxid

    @classmethod  # --------------------------------------------------------
    @abstractmethod
    def lineage_of_taxids(cls, taxid: int) -> list[int]:
        ...

    @classmethod  # --------------------------------------------------------
    @abstractmethod
    def lineage_of_ranks(cls, taxid: int) -> list[str]:
        ...

    @classmethod  # --------------------------------------------------------
    @abstractmethod
    def lineage_of_names(cls, taxid: int, name_class: str) -> list[str]:
        ...

    @classmethod  # --------------------------------------------------------
    @abstractmethod
    def common_taxid(cls, taxids: Collection[int]) -> int:
        ...

    @classmethod  # --------------------------------------------------------
    @abstractmethod
    def names_for_taxid(cls, taxid: int) -> dict[str, tuple[str]]:
        ...

    @classmethod  # --------------------------------------------------------
    @abstractmethod
    def taxids_for_name(cls, name: str) -> list[int]:
        ...

    @classmethod  # --------------------------------------------------------
    @abstractmethod
    def path_between_taxids(cls, taxid1: int, taxid2: int) -> list[int]:
        ...

    @classmethod  # --------------------------------------------------------
    @abstractmethod
    def rank_for_taxid(cls, taxid: int) -> str:
        ...

    @classmethod  # --------------------------------------------------------
    @abstractmethod
    def parent_taxid(cls, taxid: int) -> int:
        ...

    @classmethod  # --------------------------------------------------------
    @abstractmethod
    def children_taxids(cls, taxid: int) -> set[int]:
        ...

    @classmethod  # --------------------------------------------------------
    @abstractmethod
    def higher_rank_for_taxid(cls, taxid: int, rank: str, name_class: str
                              ) -> str:
        ...

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def all_descending_taxids(cls, taxid: int) -> set[int]:
        cls.taxid_valid_raise(taxid)
        return_taxids = cls.children_taxids(taxid)
        for chld_txid in return_taxids.copy():
            rabbit_hole = cls.all_descending_taxids(chld_txid)
            return_taxids |= rabbit_hole
        return return_taxids

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def all_descending_taxids_for_taxids(cls, taxids: Collection[int]
                                         ) -> set[int]:
        lca_taxid = cls.common_taxid(taxids)
        taxids = cls.all_descending_taxids(lca_taxid)
        taxids.add(lca_taxid)
        return taxids

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def taxid_for_name_and_group_taxid(cls, name: str, grp_taxid: int) -> int:
        cls.taxid_valid_raise(grp_taxid)
        grp_name = cls.name_for_taxid(grp_taxid)
        taxids = cls.taxids_for_name(name)
        if len(taxids) == 0:
            return -2
        lcas = [grp_taxid in cls.lineage_of_taxids(x) for x in taxids]

        if True in lcas:
            if lcas.count(True) > 1:
                print(f'Group {grp_taxid} ({grp_name}) is too broad; multiple '
                      f'taxa with the name "{name}" were found.')
                return -2
            else:
                idx = lcas.index(True)
                return taxids[idx]
        else:
            print(f'{name} does not belong to the group {grp_taxid} '
                  f'({grp_name}).')
            return -2

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def names_of_class_for_taxid(cls, taxid: int, name_class: str
                                 ) -> tuple[str]:
        cls.taxid_valid_raise(taxid)
        if name_class not in cls.name_classes():
            raise NameClassInvalidError(name_class)
        all_names_dict = cls.names_for_taxid(taxid=taxid)
        if name_class not in all_names_dict:
            return tuple()
        return all_names_dict[name_class]

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def name_for_taxid(cls, taxid: int, name_class: str = 'scientific name'
                       ) -> str:
        cls.taxid_valid_raise(taxid)
        names = cls.names_of_class_for_taxid(taxid, name_class)
        if len(names) > 0:
            return names[0]
        else:
            return ''

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def scientific_name_for_taxid(cls, taxid: int) -> str:
        return cls.name_for_taxid(taxid, 'scientific name')

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def common_name_for_taxid(cls, taxid: int) -> str:
        return cls.name_for_taxid(taxid, 'common name')

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def genbank_common_name_for_taxid(cls, taxid: int) -> str:
        return cls.name_for_taxid(taxid, 'genbank common name')

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def trans_table_for_genetic_code_id(cls, gcid: int
                                        ) -> dict[str, Union[dict, list]]:
        codons = cls.codons()
        tt = cls._gen_code_id_translation_table_dict[gcid]
        sc = cls._gen_code_id_start_codons_dict[gcid]

        idx_start = [i for i, x in enumerate(sc) if x == 'M']
        start_codons: list[str] = [codons[i] for i in idx_start]
        start_codons.sort()

        idx_stop = [i for i, x in enumerate(sc) if x == '*']
        stop_codons: list[str] = [codons[i] for i in idx_stop]
        stop_codons.sort()

        idx_aa = [i for i, x in enumerate(tt) if x != '*']
        aa_codons = [codons[i] for i in idx_aa]
        aas = [tt[i] for i in idx_aa]
        coding_tbl = dict(zip(aa_codons, aas))
        stop_tbl = dict(zip(stop_codons, ['*'] * len(stop_codons)))

        tbl: dict[str, str] = {}
        tbl.update(coding_tbl)
        tbl.update(stop_tbl)

        rv = {'trans_table': tbl,
              'start_codons': start_codons,
              'stop_codons': stop_codons}

        return rv

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def is_eukaryote(cls, taxid: int) -> bool:
        cls.taxid_valid_raise(taxid)
        euk_taxid = 2759
        shared_taxid = cls.common_taxid([euk_taxid, taxid])
        if shared_taxid == euk_taxid:
            return True
        else:
            return False

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def contains_plastid(cls, taxid: int) -> bool:
        cls.taxid_valid_raise(taxid)
        for taxid_w_plastid in TAXIDS_WITH_PLASTIDS:
            shared_taxid = cls.common_taxid([taxid_w_plastid, taxid])
            if shared_taxid == taxid_w_plastid:
                return True
        return False

    @classmethod  # --------------------------------------------------------
    @abstractmethod
    def genetic_code_for_taxid(cls, taxid: int) -> int:
        ...

    @classmethod  # --------------------------------------------------------
    @abstractmethod
    def mito_genetic_code_for_taxid(cls, taxid: int) -> int:
        ...

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def plastid_genetic_code_for_taxid(cls, taxid):
        cls.taxid_valid_raise(taxid)
        if cls.contains_plastid(taxid) is False:
            return 0
        # --------------------------------------------
        # Balanophoraceae uses 32 instead of 11?
        # Check this, NCBI taxonomy DB reports 11.
        # https://www.ncbi.nlm.nih.gov/pubmed/30598433
        taxid_bala = cls.updated_taxid(25673)
        if str(cls.common_taxid([taxid_bala, taxid])) == taxid_bala:
            return 32
        # --------------------------------------------
        return 11

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def trans_table_for_tax_id(cls, taxid):
        cls.taxid_valid_raise(taxid)
        gcid = cls.genetic_code_for_taxid(taxid)
        tt = cls.trans_table_for_genetic_code_id(gcid)
        return tt

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def mito_trans_table_for_tax_id(cls, taxid):
        cls.taxid_valid_raise(taxid)
        gcid = cls.mito_genetic_code_for_taxid(taxid)
        tt = cls.trans_table_for_genetic_code_id(gcid)
        return tt

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def plastid_trans_table_for_tax_id(cls, taxid):
        cls.taxid_valid_raise(taxid)
        tt = cls.trans_table_for_genetic_code_id(
            cls.plastid_genetic_code_for_taxid(taxid))
        return tt
