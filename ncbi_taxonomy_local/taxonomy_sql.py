from collections.abc import Collection
from typing import Union
from functools import partial, wraps
from itertools import dropwhile, takewhile, zip_longest
from operator import eq, ne
from sqlalchemy.orm import Session
from sqlalchemy import select
from .config import init_local_storage, init_db
from .utils import Log
from .model_sql import NCBINode, NCBIName, NCBIMergedNode, NCBIDeletedNode
from kakapo.utils.misc import invert_dict
from .errors import TaxIdInvalidError, TaxIdNotInDBError


class TaxonomySQL:
    _taxonomy_initialized = False
    _sess: Session
    _root: NCBINode

    def __new__(cls, data_dir=None, logger=Log):  # -----------------------
        super().__new__(cls)
        cls.init(data_dir=data_dir, logger=logger)
        return cls

    @staticmethod  # ------------------------------------------------------
    def _check_initialized(func):
        """Is the class initialized?"""
        @wraps(func)
        def wrapper_func(cls, *args, **kwargs):
            if cls._taxonomy_initialized is False:
                print('Run the init() method first.')
                return None
            return func(cls, *args, **kwargs)
        return wrapper_func

    @classmethod  # --------------------------------------------------------
    def init(cls, data_dir=None, logger=Log):
        if cls._taxonomy_initialized is True:
            print('Already initialized.')
            return None
        if data_dir is None:
            paths = init_local_storage()
        else:
            paths = init_local_storage(dir_local_storage=data_dir)
        cls._sess = init_db(paths)()
        cls._taxonomy_initialized = True
        cls._root = cls.node(1)  # type: ignore

    # Validation ===========================================================

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def taxid_deleted(cls, taxid: int) -> bool:
        taxid_deleted = False
        stmt = select(NCBIDeletedNode).where(NCBIDeletedNode.tax_id == taxid)
        if len(cls._sess.scalars(stmt).all()) > 0:
            taxid_deleted = True
        return taxid_deleted

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def taxid_merged(cls, taxid: int) -> bool:
        taxid_merged = False
        stmt = select(NCBIMergedNode.old_tax_id).where(
            NCBIMergedNode.old_tax_id == taxid)
        if len(cls._sess.scalars(stmt).all()) > 0:
            taxid_merged = True
        return taxid_merged

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def taxid_active(cls, taxid: int) -> bool:
        taxid_active = False
        stmt = select(NCBINode).where(NCBINode.tax_id == taxid)
        if len(cls._sess.scalars(stmt).all()) > 0:
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
            stmt = select(NCBIMergedNode.new_tax_id).where(
                NCBIMergedNode.old_tax_id == taxid)
            rslt = cls._sess.scalars(stmt).all()
            assert len(rslt) == 1
            return rslt[0]
        taxid_deleted = cls.taxid_deleted(taxid)
        if taxid_deleted is True:
            return -1
        return -2

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

    # ======================================================================

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def root(cls) -> NCBINode:
        return cls._root

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def root_taxid(cls) -> int:
        return cls._root.tax_id

    # ======================================================================

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def node(cls, taxid: int) -> NCBINode:
        cls.taxid_valid_raise(taxid)
        txid = cls.updated_taxid(taxid)
        stmt = select(NCBINode).where(NCBINode.tax_id == txid)
        node = cls._sess.scalars(stmt).all()
        assert len(node) == 1
        return node[0]

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def nodes(cls, taxids: Collection[int]) -> list[NCBINode]:
        return [cls.node(x) for x in taxids]

    # ======================================================================

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def lineage(cls, node: NCBINode) -> list[NCBINode]:

        @staticmethod  # ---------------------------------------------------
        def recurse_lineage(n: NCBINode, lineage: list[NCBINode]) -> list[NCBINode]:
            lineage.append(n)
            if n != cls.root():
                n = n.parent
                return recurse_lineage(n, lineage)
            else:
                return lineage
        # ------------------------------------------------------------------

        lineage = list()
        lineage = recurse_lineage(node, lineage)
        lineage.reverse()
        return lineage

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def lineage_taxid(cls, taxid: int) -> list[int]:
        nd = cls.node(taxid)
        ln = cls.lineage(nd)
        l_taxid = [n.tax_id for n in ln]
        return l_taxid

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def lineage_rank(cls, taxid: int) -> list[str]:
        nd = cls.node(taxid)
        ln = cls.lineage(nd)
        l_rank = [n.rank for n in ln]
        return l_rank

    # ======================================================================

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def common(cls, nodes: Collection[NCBINode]) -> NCBINode:
        nodes = list(nodes)
        shared = set(cls.lineage(nodes[0]))
        for node in nodes[1:]:
            lineage = cls.lineage(node)
            shared = shared & set(lineage)
        shared_lineage = tuple()
        for node in shared:
            lineage = cls.lineage(node)
            if len(lineage) > len(shared_lineage):
                shared_lineage = lineage
        return shared_lineage[-1]

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def common_taxid(cls, taxids: Collection[int]) -> int:
        nodes = cls.nodes(taxids)
        node = cls.common(nodes)
        return node.tax_id

    # ======================================================================

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def path(cls, node1: NCBINode, node2: NCBINode):

        if node1 == node2:
            return (node1,)

        nodes1 = cls.lineage(node1)
        nodes2 = cls.lineage(node2)

        shared = takewhile(lambda x: eq(x[0], x[1]), zip(nodes1, nodes2))
        diff = dropwhile(lambda x: eq(x[0], x[1]),
                         zip_longest(nodes1, nodes2, fillvalue=-1))

        paths = tuple(zip(*diff))

        path = tuple(filter(partial(ne, -1),
                            tuple(reversed(paths[0]))
                            + (tuple(shared)[-1][0],) + paths[1]))
        return path

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def path_taxid(cls, taxid1: int, taxid2: int) -> list[int]:
        nd1 = cls.node(taxid1)
        nd2 = cls.node(taxid2)
        path_nd = cls.path(nd1, nd2)
        path_taxid = [n.tax_id for n in path_nd]
        return path_taxid

    # ======================================================================

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def rank_taxid(cls, taxid: int) -> str:
        nd = cls.node(taxid)
        return nd.rank

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def parent_taxid(cls, taxid: int) -> int:
        nd = cls.node(taxid)
        return nd.parent_tax_id  # type: ignore

    # ======================================================================

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def names(cls, node: NCBINode) -> dict[str, tuple[str]]:
        names: list[NCBIName] = list(node.names)
        return invert_dict({x.name: x.name_class for x in names}, tuple, True)

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def names_taxid(cls, taxid: int) -> dict[str, tuple[str]]:
        nd = cls.node(taxid)
        return cls.names(nd)

    # ======================================================================

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def taxids_for_name(cls, name: str) -> list[int]:
        name = name.strip()
        if len(name) != 0:
            name_alt_1 = name[0].upper() + name[1:]
            name_alt_2 = name[0].lower() + name[1:]
            names = set([name, name_alt_1, name_alt_2])
            stmt = select(NCBIName.tax_id).where(NCBIName.name.in_(names))
            return list(set(cls._sess.scalars(stmt).all()))
        else:
            return []

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def nodes_for_name(cls, name: str) -> list[NCBINode]:
        return cls.nodes(cls.taxids_for_name(name))

    # ======================================================================

    # ======================================================================
