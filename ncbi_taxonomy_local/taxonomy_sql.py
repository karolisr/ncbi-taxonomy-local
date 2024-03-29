from collections.abc import Collection, MutableSequence
from typing import Any, Union

from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import init_db, populate_db
from .model_sql import DeletedNode, MergedNode, Name, Node
from .taxonomy_base import (Taxonomy, _check_initialized, name_variations,
                            path_between_lineages)
from .utils import Log, invert_dict


class TaxonomySQL(Taxonomy):

    _sess: Session
    _root_node: Node

    # ----------------------------------------------------------------------
    def __new__(cls,
                data_dir: Union[str, None] = None,
                logger: Any = Log,
                backend: str = 'SQLite',
                db_user: str = '',
                db_pass: str = '',
                db_host_or_ip: str = 'localhost',
                db_name: str = 'taxonomy',
                check_for_updates: bool = False):

        super().__new__(cls, data_dir=data_dir, logger=logger)

        cls.init(backend, db_user, db_pass, db_host_or_ip, db_name,
                 check_for_updates)

        return cls

    @classmethod  # --------------------------------------------------------
    def init(cls, backend, db_user, db_pass, db_host_or_ip, db_name,
             check_for_updates):
        if super().init(check_for_updates) == 1:
            return 1

        assert cls._paths is not None

        file_db = cls._paths['file_db']

        db_user = db_user.strip()
        db_host_or_ip = db_host_or_ip.strip()
        db_name = db_name.strip()

        url = ''
        if backend == 'SQLite':
            url = f'sqlite:///{file_db}'
        elif backend == 'PostgreSQL':
            db_login = ''
            if db_user != '':
                db_login += db_user
                if db_pass != '':
                    db_login += ':'
                    db_login += db_pass
                db_login += '@'
            url = f'postgresql+psycopg2://{db_login}{db_host_or_ip}/{db_name}'

        cls._sess = init_db(url)()

        try:
            stmt = select(Node).where(Node.tax_id == 1)
            nodes = cls._sess.scalars(stmt).all()
            assert len(nodes) == 1
        except AssertionError as e:
            populate_db(cls._paths, cls._sess, cls._logger)
            print()

        cls._taxonomy_initialized = True
        cls._root_node = cls.node_for_taxid(cls._root_taxid)

    @classmethod  # --------------------------------------------------------
    def update(cls, check_for_updates: bool = False):
        super().update(check_for_updates)

    # **********************************************************************
    # Operations on integer taxids.
    # **********************************************************************

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def taxid_deleted(cls, taxid: int) -> bool:
        taxid_deleted = False
        stmt = select(DeletedNode).where(DeletedNode.tax_id == taxid)
        if len(cls._sess.scalars(stmt).all()) > 0:
            taxid_deleted = True
        return taxid_deleted

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def taxid_merged(cls, taxid: int) -> bool:
        taxid_merged = False
        stmt = select(MergedNode.old_tax_id).where(
            MergedNode.old_tax_id == taxid)
        if len(cls._sess.scalars(stmt).all()) > 0:
            taxid_merged = True
        return taxid_merged

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def taxid_active(cls, taxid: int) -> bool:
        taxid_active = False
        stmt = select(Node).where(Node.tax_id == taxid)
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
            stmt = select(MergedNode.new_tax_id).where(
                MergedNode.old_tax_id == taxid)
            rslt = cls._sess.scalars(stmt).all()
            assert len(rslt) == 1
            return rslt[0]
        taxid_deleted = cls.taxid_deleted(taxid)
        if taxid_deleted is True:
            return -1
        return -2

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def lineage_of_taxids(cls, taxid: int) -> list[int]:
        # cls.taxid_valid_raise(taxid)
        nd = cls.node_for_taxid(taxid)
        ln = cls.lineage_of_nodes(nd)
        ln_taxid = [n.tax_id for n in ln]
        return ln_taxid

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def lineage_of_ranks(cls, taxid: int) -> list[str]:
        # cls.taxid_valid_raise(taxid)
        nd = cls.node_for_taxid(taxid)
        ln = cls.lineage_of_nodes(nd)
        ln_rank = [n.rank for n in ln]
        return ln_rank

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def lineage_of_names(cls, taxid: int, name_class: str = 'scientific name'
                         ) -> list[str]:
        # cls.taxid_valid_raise(taxid)
        ln_taxid = cls.lineage_of_taxids(taxid)
        ln_name = [cls.name_for_taxid(x, name_class) for x in ln_taxid]
        return ln_name

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def common_taxid(cls, taxids: Collection[int]) -> int:
        nodes = cls.nodes_for_taxids(taxids)
        node = cls.common_node(nodes)
        return node.tax_id

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def names_for_taxid(cls, taxid: int) -> dict[str, tuple[str]]:
        # cls.taxid_valid_raise(taxid)
        nd = cls.node_for_taxid(taxid)
        return cls.names_for_node(nd)

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def taxids_for_name(cls, name: str) -> list[int]:
        name = name.strip()
        if len(name) != 0:
            names = name_variations(name)
            stmt = select(Name.tax_id).where(Name.name.in_(names))
            ids = list(set(cls._sess.scalars(stmt).all()))
            ids.sort()
            return ids
        else:
            return list()

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def path_between_taxids(cls, taxid1: int, taxid2: int) -> list[int]:
        cls.taxid_valid_raise(taxid1)
        cls.taxid_valid_raise(taxid2)
        nd1 = cls.node_for_taxid(taxid1)
        nd2 = cls.node_for_taxid(taxid2)
        path_nd = cls.path_between_nodes(nd1, nd2)
        return [n.tax_id for n in path_nd]

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def rank_for_taxid(cls, taxid: int) -> str:
        # cls.taxid_valid_raise(taxid)
        nd = cls.node_for_taxid(taxid)
        return nd.rank

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def parent_taxid(cls, taxid: int) -> int:
        # cls.taxid_valid_raise(taxid)
        nd = cls.node_for_taxid(taxid)
        return nd.parent_tax_id

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def children_taxids(cls, taxid: int) -> set[int]:
        # cls.taxid_valid_raise(taxid)
        taxid = cls.updated_taxid(taxid)
        nd = cls.node_for_taxid(taxid)
        return set(cls.taxids_for_nodes(nd.children))

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def higher_rank_for_taxid(cls, taxid: int, rank: str,
                              name_class: str = 'scientific name'
                              ) -> str:
        # cls.taxid_valid_raise(taxid)
        ln_rank = cls.lineage_of_ranks(taxid)
        if rank in ln_rank:
            rank_index = ln_rank.index(rank)
        else:
            return ''
        return cls.lineage_of_names(taxid, name_class)[rank_index]

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def genetic_code_for_taxid(cls, taxid: int) -> int:
        # cls.taxid_valid_raise(taxid)
        nd = cls.node_for_taxid(taxid)
        return nd.genetic_code_id

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def mito_genetic_code_for_taxid(cls, taxid: int) -> int:
        # cls.taxid_valid_raise(taxid)
        nd = cls.node_for_taxid(taxid)
        mtgcid = nd.mitochondrial_genetic_code_id
        if mtgcid is None:
            mtgcid = 0
        return mtgcid

    # **********************************************************************
    # Operations on Node objects.
    # **********************************************************************

    _taxid_node_dict: dict[int, Node] = dict()

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def node_for_taxid(cls, taxid: int) -> Node:
        if taxid in cls._taxid_node_dict:
            return cls._taxid_node_dict[taxid]
        cls.taxid_valid_raise(taxid)
        txid = cls.updated_taxid(taxid)
        stmt = select(Node).where(Node.tax_id == txid)
        nodes = cls._sess.scalars(stmt).all()
        assert len(nodes) == 1
        node = nodes[0]
        cls._taxid_node_dict[taxid] = node
        return node

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def nodes_for_taxids(cls, taxids: Collection[int]) -> list[Node]:
        return [cls.node_for_taxid(x) for x in taxids]

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def root_node(cls) -> Node:
        return cls._root_node

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def taxids_for_nodes(cls, nodes: Collection[Node]) -> list[int]:
        return [x.tax_id for x in nodes]

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def lineage_of_nodes(cls, node: Node) -> list[Node]:
        # ------------------------------------------------------------------
        def recurse_lineage(n: Node, lineage: MutableSequence[Node]
                            ) -> list[Node]:
            lineage.append(n)
            if n != cls.root_node():
                parent_taxid = n.parent_tax_id
                if parent_taxid in cls._taxid_node_dict:
                    n = cls._taxid_node_dict[parent_taxid]
                else:
                    n = n.parent
                    cls._taxid_node_dict[n.tax_id] = n
                return recurse_lineage(n, lineage)
            else:
                return list(lineage)
        # ------------------------------------------------------------------

        lineage = list()
        lineage = recurse_lineage(node, lineage)
        lineage.reverse()
        return lineage

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def common_node(cls, nodes: Collection[Node]) -> Node:
        nodes = list(nodes)
        shared = set(cls.lineage_of_nodes(nodes[0]))
        for node in nodes[1:]:
            lineage = cls.lineage_of_nodes(node)
            shared = shared & set(lineage)
        shared_lineage = tuple()
        for node in shared:
            lineage = cls.lineage_of_nodes(node)
            if len(lineage) > len(shared_lineage):
                shared_lineage = lineage
        return shared_lineage[-1]

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def names_for_node(cls, node: Node) -> dict[str, tuple[str]]:
        names: list[Name] = list(node.names)
        return invert_dict({x.name: x.name_class for x in names}, tuple, True)

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def nodes_for_name(cls, name: str) -> list[Node]:
        return cls.nodes_for_taxids(cls.taxids_for_name(name))

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def path_between_nodes(cls, node1: Node, node2: Node) -> list[Node]:
        if node1 == node2:
            return [node1]

        ln1 = cls.lineage_of_nodes(node1)
        ln2 = cls.lineage_of_nodes(node2)

        return path_between_lineages(ln1, ln2)
