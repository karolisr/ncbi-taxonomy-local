"""NCBI taxonomy database in RAM."""

from functools import partial, wraps
from itertools import dropwhile, takewhile, zip_longest
from operator import eq, ne

from .config import NAME_CLASS_SET, init_local_storage
from .utils import Log
from .ncbi import (
    update_ncbi_taxonomy_data,
    codons_from_gc_prt_file,
    parse_names_dump,
    parse_delnodes_dump,
    parse_merged_dump,
    parse_nodes_dump,
    parse_gencode_dump
)


class TaxonomyRAM:
    _taxonomy_initialized = False
    _paths = None
    _name_classes = None
    _codons = list()
    _gen_code_id_start_codons_dict = dict()
    _gen_code_id_translation_table_dict = dict()
    _taxids_deleted_set = set()
    _taxids_genetic_code_id_dict = dict()
    _taxids_merged_dict = dict()
    _taxids_mito_genetic_code_id_dict = dict()
    _taxids_names_dict = dict()
    _names_taxids_dict = dict()
    _taxids_child_parent_dict = dict()
    _taxids_parent_children_dict = dict()
    _taxids_rank_dict = dict()

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
        cls._paths = paths
        cls._update(logger=logger)

    @classmethod  # --------------------------------------------------------
    def _update(cls, logger=Log):

        if cls._paths is None:
            logger.wrn('Run the init() method first.')
            return None

        # logger.inf('Updating NCBI taxonomy data.')

        download_taxdmp = update_ncbi_taxonomy_data(
            taxdmp_path=cls._paths['dir_taxdmp'],
            force_redownload=False,
            check_for_updates=False,
            logger=logger)

        if download_taxdmp is False:
            if cls._taxonomy_initialized:
                return None

        logger.msg('Loading NCBI taxonomy data.')

        cls._codons = codons_from_gc_prt_file(cls._paths['file_gc'])

        cls._tax_dict = parse_names_dump(file_path=cls._paths['file_names'])
        cls._taxids_names_dict = cls._tax_dict['tax_id_keyed_dict']
        cls._names_taxids_dict = cls._tax_dict['name_keyed_dict']

        cls._taxids_deleted_set = parse_delnodes_dump(
            file_path=cls._paths['file_delnodes'])

        cls._taxids_merged_dict = parse_merged_dump(
            file_path=cls._paths['file_merged'])

        parse_nodes_dump_result = parse_nodes_dump(
            file_path=cls._paths['file_nodes'])

        cls._taxids_parent_children_dict = parse_nodes_dump_result[0]
        cls._taxids_child_parent_dict = parse_nodes_dump_result[1]
        cls._taxids_rank_dict = parse_nodes_dump_result[2]
        cls._taxids_genetic_code_id_dict = parse_nodes_dump_result[3]
        cls._taxids_mito_genetic_code_id_dict = parse_nodes_dump_result[4]

        parse_gencode_dump_result = parse_gencode_dump(
            file_path=cls._paths['file_gencode'])

        cls._gen_code_id_name_dict = parse_gencode_dump_result[0]
        cls._gen_code_id_translation_table_dict = parse_gencode_dump_result[1]
        cls._gen_code_id_start_codons_dict = parse_gencode_dump_result[2]

        cls._name_classes = list(NAME_CLASS_SET)
        cls._name_classes.sort()

        cls._taxonomy_initialized = True

    # Class properties *******************************************************

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def codons(cls):
        return cls._codons

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def name_classes(cls):
        return cls._name_classes

    # Class methods **********************************************************

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def taxid_in_db(cls, taxid):
        taxid = str(taxid)
        taxid_in_db = False
        if taxid in cls._taxids_child_parent_dict or \
                taxid in cls._taxids_merged_dict or \
                taxid in cls._taxids_deleted_set:
            taxid_in_db = True
        return taxid_in_db

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def taxid_valid(cls, taxid):
        taxid = str(taxid)
        taxid_valid = False
        if taxid in cls._taxids_child_parent_dict or \
                taxid in cls._taxids_merged_dict:
            taxid_valid = True
        return taxid_valid

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def taxid_in_db_raise(cls, taxid):
        taxid = str(taxid)
        if not cls.taxid_in_db(taxid):
            message = 'TaxID: \'{t}\' is not in the database.'
            message = message.format(t=taxid)
            raise Exception(message)

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def taxid_valid_raise(cls, taxid):
        taxid = str(taxid)
        if not cls.taxid_valid(taxid):
            message = 'TaxID: \'{t}\' is not valid.'
            message = message.format(t=taxid)
            raise Exception(message)

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def taxid_deleted(cls, taxid):
        taxid = str(taxid)
        cls.taxid_in_db_raise(taxid)
        taxid_deleted = False
        if taxid in cls._taxids_deleted_set:
            taxid_deleted = True
        return taxid_deleted

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def taxid_merged(cls, taxid):
        taxid = str(taxid)
        cls.taxid_valid_raise(taxid)
        taxid_merged = False
        if taxid in cls._taxids_merged_dict:
            taxid_merged = cls._taxids_merged_dict[taxid]
        return taxid_merged

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def updated_taxid(cls, taxid):
        taxid = str(taxid)
        cls.taxid_valid_raise(taxid)
        return_taxid = taxid
        taxid_deleted = cls.taxid_deleted(taxid=taxid)
        taxid_merged = cls.taxid_merged(taxid=taxid)

        if taxid_deleted is False:
            if taxid_merged is not False:
                return_taxid = taxid_merged
        else:
            return_taxid = None

        return return_taxid

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def names_for_taxid(cls, taxid):
        taxid = str(taxid)
        cls.taxid_valid_raise(taxid)
        return_dict = dict()
        return_dict['old_taxid'] = taxid
        new_taxid = cls.updated_taxid(taxid=taxid)
        return_dict['new_taxid'] = new_taxid
        return_dict['names'] = None

        if new_taxid is not None:
            return_dict['names'] = cls._taxids_names_dict[new_taxid]

        return return_dict

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def taxids_for_name(cls, name):
        return_dict = dict()

        return_dict['name'] = name
        return_dict['tax_ids'] = None

        if len(name) != 0:
            name_alt_1 = name[0].upper() + name[1:]
            name_alt_2 = name[0].lower() + name[1:]
            names = [name, name_alt_1, name_alt_2]
            for name in names:
                if name in cls._names_taxids_dict:
                    return_dict['tax_ids'] = cls._names_taxids_dict[name]
                    return_dict['name'] = name
                    break
                else:
                    continue

        return return_dict

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def name_class_for_taxid(cls, taxid, name_class='scientific name'):
        taxid = str(taxid)
        cls.taxid_valid_raise(taxid)

        if name_class not in NAME_CLASS_SET:
            message = 'Name class \'{n}\' is not valid.'
            message = message.format(n=name_class)
            raise Exception(message)

        all_names_dict = cls.names_for_taxid(taxid=taxid)

        return_dict = dict()
        return_dict['old_taxid'] = all_names_dict['old_taxid']
        return_dict['new_taxid'] = all_names_dict['new_taxid']
        return_dict['name'] = None

        names = all_names_dict['names']

        if names is not None:
            for n in names:
                if n['name_class'] == name_class:
                    if return_dict['name'] is None:
                        return_dict['name'] = list()
                    return_dict['name'].append(n['name'])

        return return_dict

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def name_for_taxid(cls, taxid, name_class='scientific name'):
        cls.taxid_valid_raise(taxid)
        name = cls.name_class_for_taxid(taxid, name_class)
        name = name['name']
        if name is not None:
            name = name[0]
        else:
            name = None
        return name

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def scientific_name_for_taxid(cls, taxid):
        name = cls.name_for_taxid(taxid, 'scientific name')
        return name

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def common_name_for_taxid(cls, taxid):
        name = cls.name_for_taxid(taxid, 'common name')
        return name

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def genbank_common_name_for_taxid(cls, taxid):
        name = cls.name_for_taxid(taxid, 'genbank common name')
        return name

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def rank_for_taxid(cls, taxid):
        taxid = str(taxid)
        cls.taxid_valid_raise(taxid)
        return_rank = None
        taxid = cls.updated_taxid(taxid=taxid)
        if taxid in cls._taxids_rank_dict:
            return_rank = cls._taxids_rank_dict[taxid]
        return return_rank

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def parent_taxid(cls, taxid):
        taxid = str(taxid)
        cls.taxid_valid_raise(taxid)
        return_taxid = None
        taxid = cls.updated_taxid(taxid=taxid)
        if taxid in cls._taxids_child_parent_dict:
            return_taxid = cls._taxids_child_parent_dict[taxid]
        return return_taxid

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def children_taxids(cls, taxid):
        taxid = str(taxid)
        cls.taxid_valid_raise(taxid)
        return_taxids = None
        taxid = cls.updated_taxid(taxid=taxid)
        if taxid in cls._taxids_parent_children_dict:
            return_taxids = cls._taxids_parent_children_dict[taxid]
        return return_taxids

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def all_descending_taxids(cls, taxid):
        cls.taxid_valid_raise(taxid)
        return_taxids = cls.children_taxids(taxid)
        if return_taxids is not None:
            for chld_txid in return_taxids:
                rabbit_hole = cls.all_descending_taxids(chld_txid)
                if rabbit_hole is not None:
                    return_taxids = return_taxids + rabbit_hole
        return return_taxids

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def lineage_for_taxid(cls, taxid, name_class='scientific name'):
        taxid = str(taxid)
        cls.taxid_valid_raise(taxid)
        return_dict = dict()
        return_dict['old_taxid'] = taxid
        new_taxid = cls.updated_taxid(taxid=taxid)
        return_dict['new_taxid'] = new_taxid
        return_dict['taxids'] = None
        return_dict['ranks'] = None
        return_dict['names'] = None

        def recurse_lineage(taxid, lineage):
            lineage.append(taxid)
            if taxid != '1':
                taxid = cls.parent_taxid(taxid=taxid)
                return recurse_lineage(taxid, lineage)
            else:
                return lineage

        taxids = list()
        if new_taxid is not None:
            taxids = recurse_lineage(
                taxid=new_taxid, lineage=taxids)

        taxids.reverse()
        return_dict['taxids'] = taxids

        ranks = [cls.rank_for_taxid(taxid=x) for x in taxids]
        return_dict['ranks'] = ranks

        names = [cls.name_class_for_taxid(
            taxid=x, name_class=name_class)['name'][0] for x in taxids]
        return_dict['names'] = names

        return return_dict

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def path_between_taxids(cls, taxid1, taxid2):
        cls.taxid_valid_raise(taxid1)
        cls.taxid_valid_raise(taxid2)

        taxid1 = int(taxid1)
        taxid2 = int(taxid2)

        if taxid1 == taxid2:
            return (taxid1,)

        taxids1 = tuple(map(int, cls.lineage_for_taxid(taxid1)['taxids']))
        taxids2 = tuple(map(int, cls.lineage_for_taxid(taxid2)['taxids']))

        shared = takewhile(lambda x: eq(x[0], x[1]), zip(taxids1, taxids2))
        diff = dropwhile(lambda x: eq(x[0], x[1]),
                         zip_longest(taxids1, taxids2, fillvalue=-1))

        paths = tuple(zip(*diff))

        path = tuple(filter(partial(ne, -1),
                            tuple(reversed(paths[0]))
                            + (tuple(shared)[-1][0],) + paths[1]))
        return path

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def higher_rank_for_taxid(cls, taxid, rank, name_class='scientific name'):
        taxid = str(taxid)
        cls.taxid_valid_raise(taxid)
        lineage = cls.lineage_for_taxid(taxid=taxid, name_class=name_class)
        if rank in lineage['ranks']:
            rank_index = lineage['ranks'].index(rank)
        else:
            return None
        return lineage['names'][rank_index]

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def shared_taxid_for_taxids(cls, taxids):
        assert type(taxids) in (list, tuple, set)
        if len(taxids) == 0:
            return None
        shared = set(cls.lineage_for_taxid(taxid=taxids[0])['taxids'])
        for taxid in taxids[1:]:
            cls.taxid_valid_raise(taxid)
            lineage = cls.lineage_for_taxid(taxid=taxid)['taxids']
            shared = shared & set(lineage)
        shared_lineage = tuple()
        for taxid in shared:
            lineage = cls.lineage_for_taxid(taxid=taxid)['taxids']
            if len(lineage) > len(shared_lineage):
                shared_lineage = lineage
        return int(shared_lineage[-1])

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def all_descending_taxids_for_taxids(cls, taxids):
        shared = cls.shared_taxid_for_taxids(taxids)
        if shared is None:
            return None
        taxids = cls.all_descending_taxids(taxid=shared)
        if taxids is None:
            taxids = [shared]
        taxids = [int(x) for x in taxids]
        return taxids

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def tax_id_for_name_and_group_tax_id(cls, name, group_tax_id):
        group_tax_id = str(group_tax_id)
        cls.taxid_valid_raise(group_tax_id)
        tax_nodes = cls.taxids_for_name(name=name)['tax_ids']
        if tax_nodes is None:
            return None
        ids = [x['tax_id'] for x in tax_nodes]
        lcas = [group_tax_id in
                cls.lineage_for_taxid(x)['taxids'] for x in ids]

        if True in lcas:
            group_too_broad = lcas.count(True) > 1
            if not group_too_broad:
                correct_tax_node_index = lcas.index(True)
            else:
                # print('Group is too broad')
                return None
        else:
            # print('Organism does not belong to this group.')
            return None

        return ids[correct_tax_node_index]

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def is_eukaryote(cls, taxid):
        taxid = str(taxid)
        cls.taxid_valid_raise(taxid)
        euk_taxid = 2759
        shared_taxid = cls.shared_taxid_for_taxids([euk_taxid, taxid])
        if shared_taxid == euk_taxid:
            return True
        else:
            return False

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def contains_plastid(cls, taxid):
        taxid = str(taxid)
        cls.taxid_valid_raise(taxid)
        taxids_with_plastids = [33090, 554915, 2686027, 554296, 1401294,
                                2608240, 3027, 2611352, 33682, 38254,
                                2608109, 2489521, 5752, 556282, 136087,
                                2611341, 2598132, 2763, 2698737, 2683617]
        for taxid_w_plastid in taxids_with_plastids:
            shared_taxid = cls.shared_taxid_for_taxids([taxid_w_plastid, taxid])
            if shared_taxid == taxid_w_plastid:
                return True
        return False

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def trans_table_for_genetic_code_id(cls, gcid):
        gcid = str(gcid)

        codons = cls.codons()
        tt = list(cls._gen_code_id_translation_table_dict[gcid])
        sc = list(cls._gen_code_id_start_codons_dict[gcid])

        idx_start = [i for i, x in enumerate(sc) if x == 'M']
        start_codons = [codons[i] for i in idx_start]

        idx_stop = [i for i, x in enumerate(sc) if x == '*']
        stop_codons = [codons[i] for i in idx_stop]

        idx_aa = [i for i, x in enumerate(tt) if x != '*']
        aa_codons = [codons[i] for i in idx_aa]
        aas = [tt[i] for i in idx_aa]
        coding_tbl = dict(zip(aa_codons, aas))
        stop_tbl = dict(zip(stop_codons, ['*'] * len(stop_codons)))

        tbl = {}
        tbl.update(coding_tbl)
        tbl.update(stop_tbl)

        ret_val = {'trans_table': tbl,
                   'start_codons': start_codons,
                   'stop_codons': stop_codons}
        return ret_val

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def genetic_code_for_taxid(cls, taxid):
        taxid = str(taxid)
        cls.taxid_valid_raise(taxid)
        gcid = cls._taxids_genetic_code_id_dict[taxid]
        return gcid

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def mito_genetic_code_for_taxid(cls, taxid):
        taxid = str(taxid)
        cls.taxid_valid_raise(taxid)
        gcid = cls._taxids_mito_genetic_code_id_dict[taxid]
        return gcid

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def plastid_genetic_code_for_taxid(cls, taxid):
        taxid = str(taxid)
        cls.taxid_valid_raise(taxid)
        if cls.contains_plastid(taxid) is False:
            return '0'
        # --------------------------------------------
        # Balanophoraceae uses 32 instead of 11?
        # Check this, NCBI taxonomy DB reports 11.
        # https://www.ncbi.nlm.nih.gov/pubmed/30598433
        taxid_bala = cls.updated_taxid('25673')
        if str(cls.shared_taxid_for_taxids([taxid_bala, taxid])) == taxid_bala:
            return '32'
        # --------------------------------------------
        return '11'

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def trans_table_for_tax_id(cls, taxid):
        taxid = str(taxid)
        cls.taxid_valid_raise(taxid)
        gcid = cls.genetic_code_for_taxid(taxid)
        tt = cls.trans_table_for_genetic_code_id(gcid)
        return tt

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def mito_trans_table_for_tax_id(cls, taxid):
        taxid = str(taxid)
        cls.taxid_valid_raise(taxid)
        gcid = cls.mito_genetic_code_for_taxid(taxid)
        tt = cls.trans_table_for_genetic_code_id(gcid)
        return tt

    @classmethod  # --------------------------------------------------------
    @_check_initialized
    def plastid_trans_table_for_tax_id(cls, taxid):
        taxid = str(taxid)
        cls.taxid_valid_raise(taxid)
        tt = cls.trans_table_for_genetic_code_id(
            cls.plastid_genetic_code_for_taxid(taxid))
        return tt
