from collections.abc import Collection

from kakapo.utils.misc import invert_dict

from .ncbi import (parse_delnodes_dump, parse_merged_dump, parse_names_dump,
                   parse_nodes_dump)
from .taxonomy_base import (Taxonomy, _check_initialized, name_variations,
                            path_between_lineages)
from .utils import Log


class TaxonomyRAM(Taxonomy):

    _names_taxids_dict = dict()
    _taxids_names_dict = dict()

    _taxids_rank_dict = dict()

    _taxids_child_parent_dict = dict()
    _taxids_parent_children_dict = dict()

    _taxids_deleted_set = set()
    _taxids_merged_dict = dict()

    _taxids_genetic_code_id_dict = dict()
    _taxids_mito_genetic_code_id_dict = dict()

    # ----------------------------------------------------------------------
    def __new__(cls, data_dir=None, logger=Log):
        super().__new__(cls, data_dir=data_dir, logger=logger)
        cls.init()
        return cls

    @classmethod  # --------------------------------------------------------
    def init(cls):
        if super().init() == 1:
            return 1
        cls._taxonomy_initialized = True

    @classmethod  # --------------------------------------------------------
    def update(cls, check_for_updates=False):
        status = super().update(check_for_updates=check_for_updates)

        if status == 'not_initialized' or status == 'no_changes':
            return

        assert cls._paths is not None

        cls._logger.msg('Loading NCBI taxonomy data.')

        tax_dict = parse_names_dump(cls._paths['file_names'])
        cls._names_taxids_dict = tax_dict['name_keyed_dict']
        cls._taxids_names_dict = tax_dict['tax_id_keyed_dict']

        cls._taxids_deleted_set = parse_delnodes_dump(cls._paths['file_delnodes'])
        cls._taxids_merged_dict = parse_merged_dump(cls._paths['file_merged'])

        _ = parse_nodes_dump(cls._paths['file_nodes'])
        cls._taxids_parent_children_dict = _[0]
        cls._taxids_child_parent_dict = _[1]
        cls._taxids_rank_dict = _[2]
        cls._taxids_genetic_code_id_dict = _[3]
        cls._taxids_mito_genetic_code_id_dict = _[4]

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def taxid_deleted(cls, taxid) -> bool:
        taxid_deleted = False
        if taxid in cls._taxids_deleted_set:
            taxid_deleted = True
        return taxid_deleted

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def taxid_merged(cls, taxid) -> bool:
        taxid_merged = False
        if taxid in cls._taxids_merged_dict:
            taxid_merged = True
        return taxid_merged

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def taxid_active(cls, taxid: int) -> bool:
        taxid_active = False
        if taxid in cls._taxids_child_parent_dict:
            taxid_active = True
        return taxid_active

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def updated_taxid(cls, taxid: int) -> int:
        taxid_active = cls.taxid_active(taxid)
        if taxid_active is True:
            return taxid
        taxid_merged = cls.taxid_merged(taxid)
        if taxid_merged is True:
            return cls._taxids_merged_dict[taxid]
        taxid_deleted = cls.taxid_deleted(taxid)
        if taxid_deleted is True:
            return -1
        return -2

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def _lineage(cls, taxid: int, name_class='scientific name') -> dict[str, list]:
        cls.taxid_valid_raise(taxid)
        return_dict = dict()
        return_dict['old_taxid'] = taxid
        new_taxid = cls.updated_taxid(taxid=taxid)
        return_dict['new_taxid'] = new_taxid
        return_dict['taxids'] = []
        return_dict['ranks'] = []
        return_dict['names'] = []

        def recurse_lineage(taxid, lineage):
            lineage.append(taxid)
            if taxid != cls.root_taxid():
                taxid = cls.parent_taxid(taxid=taxid)
                return recurse_lineage(taxid, lineage)
            else:
                return lineage

        taxids = list()
        if new_taxid > 0:
            taxids = recurse_lineage(taxid=new_taxid, lineage=taxids)

        taxids.reverse()
        return_dict['taxids'] = taxids

        ranks = [cls.rank_for_taxid(taxid=x) for x in taxids]
        return_dict['ranks'] = ranks

        names = [cls.name_for_taxid(x, name_class) for x in taxids]
        return_dict['names'] = names

        return return_dict

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def lineage_of_taxids(cls, taxid: int) -> list[int]:
        ln = cls._lineage(taxid)
        return ln['taxids']

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def lineage_of_ranks(cls, taxid: int) -> list[str]:
        ln = cls._lineage(taxid)
        return ln['ranks']

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def lineage_of_names(cls, taxid: int, name_class: str = 'scientific name') -> list[str]:
        ln = cls._lineage(taxid, name_class)
        return ln['names']

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def common_taxid(cls, taxids: Collection[int]) -> int:
        taxids = list(taxids)
        shared = set(cls.lineage_of_taxids(taxids[0]))
        for taxid in taxids[1:]:
            cls.taxid_valid_raise(taxid)
            lineage = cls.lineage_of_taxids(taxid=taxid)
            shared = shared & set(lineage)
        shared_lineage = tuple()
        for taxid in shared:
            lineage = cls.lineage_of_taxids(taxid=taxid)
            if len(lineage) > len(shared_lineage):
                shared_lineage = lineage
        return shared_lineage[-1]

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def names_for_taxid(cls, taxid: int) -> dict[str, tuple[str]]:
        cls.taxid_valid_raise(taxid)
        names = cls._taxids_names_dict[cls.updated_taxid(taxid=taxid)]
        return invert_dict({x['name']: x['name_class'] for x in names}, tuple, True)

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def taxids_for_name(cls, name: str) -> list[int]:
        if len(name) != 0:
            names = name_variations(name)
            for name in names:
                if name in cls._names_taxids_dict:
                    return cls._names_taxids_dict[name]
        return list()

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def path_between_taxids(cls, taxid1: int, taxid2: int) -> list[int]:
        cls.taxid_valid_raise(taxid1)
        cls.taxid_valid_raise(taxid2)

        if taxid1 == taxid2:
            return [taxid1]

        ln1 = cls.lineage_of_taxids(taxid1)
        ln2 = cls.lineage_of_taxids(taxid2)

        return path_between_lineages(ln1, ln2)

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def rank_for_taxid(cls, taxid: int) -> str:
        cls.taxid_valid_raise(taxid)
        taxid = cls.updated_taxid(taxid)
        return cls._taxids_rank_dict[taxid]

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def parent_taxid(cls, taxid: int) -> int:
        cls.taxid_valid_raise(taxid)
        taxid = cls.updated_taxid(taxid)
        return cls._taxids_child_parent_dict[taxid]

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def children_taxids(cls, taxid: int) -> set[int]:
        cls.taxid_valid_raise(taxid)
        taxid = cls.updated_taxid(taxid)
        if taxid in cls._taxids_parent_children_dict:
            return set(cls._taxids_parent_children_dict[taxid])
        return set()

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def higher_rank_for_taxid(cls, taxid: int, rank: str,
                              name_class: str = 'scientific name'
                              ) -> str:
        cls.taxid_valid_raise(taxid)
        ln = cls._lineage(taxid, name_class)
        if rank in ln['ranks']:
            rank_index = ln['ranks'].index(rank)
        else:
            return ''
        return ln['names'][rank_index]

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def genetic_code_for_taxid(cls, taxid: int) -> int:
        cls.taxid_valid_raise(taxid)
        return cls._taxids_genetic_code_id_dict[taxid]

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def mito_genetic_code_for_taxid(cls, taxid: int) -> int:
        cls.taxid_valid_raise(taxid)
        return cls._taxids_mito_genetic_code_id_dict[taxid]
