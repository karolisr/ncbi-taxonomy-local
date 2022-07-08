"""NCBI taxonomy databases outside of the ENTREZ system."""

import functools
import os
import zipfile
from functools import partial
from itertools import dropwhile
from itertools import takewhile
from itertools import zip_longest
from operator import eq
from operator import ne
from os.path import abspath
from os.path import expanduser

from ncbi_taxonomy_local.misc import download_file
from ncbi_taxonomy_local.misc import extract_md5_hash
from ncbi_taxonomy_local.misc import generate_md5_hash_for_file
from ncbi_taxonomy_local.misc import make_dirs

TAX_BASE_URL = 'https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/'

# Files expected to be in taxdmp.zip MD5 file should be first
TAXDMP_FILES = ['taxdmp.zip.md5', 'readme.txt', 'nodes.dmp',
                'names.dmp', 'merged.dmp', 'gencode.dmp', 'gc.prt',
                'division.dmp', 'delnodes.dmp', 'citations.dmp']
TAXDMP_ARCHIVE = 'taxdmp.zip'

# Files expected to be in taxcat.zip MD5 file should be first
TAXCAT_FILES = ['taxcat.zip.md5', 'categories.dmp']
TAXCAT_ARCHIVE = 'taxcat.zip'

NAME_CLASS_SET = {'acronym', 'teleomorph', 'scientific name', 'synonym',
                  'blast name', 'misspelling', 'in-part', 'includes',
                  'genbank acronym', 'misnomer', 'common name',
                  'equivalent name', 'type material', 'authority',
                  'genbank common name', 'genbank synonym', 'anamorph',
                  'genbank anamorph'}


class Log:
    @classmethod
    def inf(cls, s=''):
        print(s)

    @classmethod
    def msg(cls, m, s=''):
        print(m, s)

    @classmethod
    def wrn(cls, w, s=''):
        print(w, s)

    @classmethod
    def err(cls, e, s=''):
        print(e, s)


def download_ncbi_taxonomy_data(directory_path,
                                archive_url,
                                md5_url,
                                archive_path,
                                md5_path,
                                logger=Log):
    download_file(archive_url, archive_path)
    download_file(md5_url, md5_path)

    md5_reported = extract_md5_hash(file_path=md5_path)
    logger.msg('MD5 hash reported:', md5_reported)
    md5_actual = generate_md5_hash_for_file(file_path=archive_path)
    logger.msg('  MD5 hash actual:', md5_actual)

    if md5_reported != md5_actual:
        # message = ('The MD5 hash for the file {f} does not match '
        #            'the reported hash in the file {r}.')
        # message = message.format(f=archive_path, r=md5_path)
        message = ('The MD5 hash does not match the expected value:')
        logger.err(message, 'retrying.')
        download_ncbi_taxonomy_data(directory_path, archive_url, md5_url,
                                    archive_path, md5_path, logger)
        # raise Exception(message)
    else:
        z = zipfile.ZipFile(file=archive_path, mode='r')
        z.extractall(path=directory_path)
        return True


def update_ncbi_taxonomy_data(taxdmp_path, taxcat_path,
                              force_redownload=False,
                              check_for_updates=True,
                              logger=Log):
    download_taxdmp = False
    download_taxcat = False

    taxdmp_archive_path = os.path.join(taxdmp_path, TAXDMP_ARCHIVE)
    taxcat_archive_path = os.path.join(taxcat_path, TAXCAT_ARCHIVE)

    taxdmp_md5_url = os.path.join(TAX_BASE_URL, TAXDMP_FILES[0])
    taxcat_md5_url = os.path.join(TAX_BASE_URL, TAXCAT_FILES[0])

    taxdmp_md5_path = os.path.join(taxdmp_path, TAXDMP_FILES[0])
    taxcat_md5_path = os.path.join(taxcat_path, TAXCAT_FILES[0])

    taxdmp_md5_path_new = taxdmp_md5_path + '_new'
    taxcat_md5_path_new = taxcat_md5_path + '_new'

    if not force_redownload:

        for file_name in TAXDMP_FILES:
            file_path = os.path.join(taxdmp_path, file_name)
            if not os.path.exists(file_path):
                download_taxdmp = True
                break

        for file_name in TAXCAT_FILES:
            file_path = os.path.join(taxcat_path, file_name)
            if not os.path.exists(file_path):
                download_taxcat = True
                break

        if check_for_updates:
            if not download_taxdmp:
                download_file(taxdmp_md5_url, taxdmp_md5_path_new)

                old_md5 = extract_md5_hash(file_path=taxdmp_md5_path)
                new_md5 = extract_md5_hash(file_path=taxdmp_md5_path_new)

                os.remove(taxdmp_md5_path_new)

                logger.msg('Previous MD5 for the taxdmp file:', old_md5)
                logger.msg('     New MD5 for the taxdmp file:', new_md5)

                if old_md5 != new_md5:
                    download_taxdmp = True

            if not download_taxcat:
                download_file(taxcat_md5_url, taxcat_md5_path_new)

                old_md5 = extract_md5_hash(file_path=taxcat_md5_path)
                new_md5 = extract_md5_hash(file_path=taxcat_md5_path_new)

                os.remove(taxcat_md5_path_new)

                logger.msg('Previous MD5 for the taxcat file:', old_md5)
                logger.msg('     New MD5 for the taxcat file:', new_md5)

                if old_md5 != new_md5:
                    download_taxcat = True

    else:
        download_taxdmp = True
        download_taxcat = True

    if download_taxdmp is True:
        logger.wrn('Newer version of the taxdmp file was found. Will download.')
    else:
        logger.msg('The taxdmp file does not need to be updated.')

    if download_taxcat is True:
        logger.wrn('Newer version of the taxcat file was found. Will download.')
    else:
        logger.msg('The taxcat file does not need to be updated.')

    if download_taxdmp:
        download_ncbi_taxonomy_data(
            directory_path=taxdmp_path,
            archive_url=TAX_BASE_URL + TAXDMP_ARCHIVE,
            md5_url=taxdmp_md5_url,
            archive_path=taxdmp_archive_path,
            md5_path=taxdmp_md5_path,
            logger=logger)

        os.remove(taxdmp_archive_path)

    if download_taxcat:
        download_ncbi_taxonomy_data(
            directory_path=taxcat_path,
            archive_url=TAX_BASE_URL + TAXCAT_ARCHIVE,
            md5_url=taxcat_md5_url,
            archive_path=taxcat_archive_path,
            md5_path=taxcat_md5_path,
            logger=logger)

        os.remove(taxcat_archive_path)

    return download_taxdmp, download_taxcat


def parse_ncbi_taxonomy_dump_file(file_path):
    row_terminator = '\t|'
    field_terminator = '\t|\t'
    with open(file_path, 'r') as f:
        lines = f.read().splitlines()
    lines = map(lambda l: l.strip(row_terminator), lines)
    ret_iter = map(lambda l: l.split(field_terminator), lines)
    return ret_iter


def parse_codons(tax_gencode_prt_path):
    base1 = ''
    base2 = ''
    base3 = ''

    base1_start = '  -- Base1  '
    base2_start = '  -- Base2  '
    base3_start = '  -- Base3  '

    with open(tax_gencode_prt_path, 'r') as f:
        lines = f.read().splitlines()

    for line in lines:
        line = line.strip('\n')

        if line.startswith(base1_start):
            base1 = line.strip(base1_start)
        elif line.startswith(base2_start):
            base2 = line.strip(base2_start)
        elif line.startswith(base3_start):
            base3 = line.strip(base3_start)
            break

    cs = list(zip(base1, base2, base3))
    return_value = [''.join(x) for x in cs]

    return return_value


def parse_names_dump(file_path):
    rows = parse_ncbi_taxonomy_dump_file(file_path=file_path)

    txid_keyed_dict = dict()
    name_keyed_dict = dict()

    for r in rows:

        tax_id = r[0]
        name = r[1]
        unique_name = r[2]
        name_class = r[3]

        txid_keyed_dict.setdefault(tax_id, []).append({
            'name': name,
            'unique_name': unique_name,
            'name_class': name_class})

        name_keyed_dict.setdefault(name, []).append({
            'tax_id': tax_id,
            'unique_name': unique_name,
            'name_class': name_class})

    return {'tax_id_keyed_dict': txid_keyed_dict,
            'name_keyed_dict': name_keyed_dict}


def parse_delnodes_dump(file_path):
    rows = parse_ncbi_taxonomy_dump_file(file_path=file_path)
    tax_id_set = set()
    for r in rows:
        tax_id_set.add(r[0])
    return tax_id_set


def parse_merged_dump(file_path):
    rows = parse_ncbi_taxonomy_dump_file(file_path=file_path)
    new_to_old_tax_id_mapping_dict = dict()
    for r in rows:
        old_tax_id = r[0]
        new_tax_id = r[1]
        new_to_old_tax_id_mapping_dict[old_tax_id] = new_tax_id
    return new_to_old_tax_id_mapping_dict


def parse_nodes_dump(file_path):
    rows = parse_ncbi_taxonomy_dump_file(file_path=file_path)

    child_to_parent_tax_id_mapping_dict = dict()
    taxid_rank_dict = dict()
    taxid_genetic_code_id_dict = dict()
    taxid_mitochondrial_genetic_code_id_dict = dict()

    for r in rows:

        tax_id = r[0]
        parent_tax_id = r[1]
        rank = r[2]

        # embl_code = r[3]
        # division_id = r[4]
        # inherited_div_flag = r[5]
        genetic_code_id = r[6]
        # inherited_GC_flag = r[7]
        mitochondrial_genetic_code_id = r[8]
        # inherited_MGC_flag = r[9]
        # GenBank_hidden_flag = r[10]
        # hidden_subtree_root_flag = r[11]

        # not every row contains this column, and it is not needed
        # comments = r[12]

        child_to_parent_tax_id_mapping_dict[tax_id] = parent_tax_id
        taxid_rank_dict[tax_id] = rank
        taxid_genetic_code_id_dict[tax_id] = genetic_code_id
        taxid_mitochondrial_genetic_code_id_dict[tax_id] = \
            mitochondrial_genetic_code_id

    parent_tax_ids = set(child_to_parent_tax_id_mapping_dict.values())

    parent_to_children_tax_id_mapping_dict = dict()
    for ptxid in parent_tax_ids:
        parent_to_children_tax_id_mapping_dict[ptxid] = []

    for ctxid in child_to_parent_tax_id_mapping_dict:
        ptxid = child_to_parent_tax_id_mapping_dict[ctxid]
        parent_to_children_tax_id_mapping_dict[ptxid].append(ctxid)

    return_value = [
        parent_to_children_tax_id_mapping_dict,
        child_to_parent_tax_id_mapping_dict,
        taxid_rank_dict,
        taxid_genetic_code_id_dict,
        taxid_mitochondrial_genetic_code_id_dict]

    return return_value


def parse_gencode_dump(file_path):
    rows = parse_ncbi_taxonomy_dump_file(file_path=file_path)

    genetic_code_id_to_name_dict = dict()
    genetic_code_id_to_translation_table_dict = dict()
    genetic_code_id_to_start_codons_dict = dict()

    for r in rows:

        genetic_code_id = r[0]
        # abbreviation = r[1]
        name = r[2]
        translation_table = r[3].strip()
        start_codons = r[4].strip()

        genetic_code_id_to_name_dict[genetic_code_id] = name
        genetic_code_id_to_translation_table_dict[genetic_code_id] = \
            translation_table
        genetic_code_id_to_start_codons_dict[genetic_code_id] = start_codons

    return_value = [
        genetic_code_id_to_name_dict,
        genetic_code_id_to_translation_table_dict,
        genetic_code_id_to_start_codons_dict]

    return return_value


class Taxonomy:
    _data_dir_path = None
    _tax_dmp_path = None
    _tax_cat_path = None
    _tax_names_dmp_path = None
    _tax_nodes_dmp_path = None
    _tax_delnodes_dmp_path = None
    _tax_merged_dmp_path = None
    _tax_gencode_dmp_path = None
    _tax_gencode_prt_path = None

    _taxonomy_initialized = False

    _taxids_child_parent_dict = None

    _codons = None
    _name_classes = None
    _taxids_merged_dict = None
    _taxids_deleted_set = None
    _taxids_names_dict = None
    _names_taxids_dict = None
    _taxids_rank_dict = None
    _taxids_parent_children_dict = None
    _gen_code_id_translation_table_dict = None
    _gen_code_id_start_codons_dict = None
    _taxids_genetic_code_id_dict = None
    _taxids_mito_genetic_code_id_dict = None
    plastid_genetic_code = None

    @classmethod
    def init(cls, data_dir_path, logger=Log):
        if cls._taxonomy_initialized is True:
            print('Already initialized.')
            return
        cls._data_dir_path = make_dirs(abspath(expanduser(data_dir_path)))
        cls.update(logger=logger)

    @classmethod
    def is_initialized(cls):
        return cls._taxonomy_initialized

    def initialized(func):
        """Is the class initialized?"""
        @classmethod
        @functools.wraps(func)
        def wrapper_func(cls, *args, **kwargs):
            if cls._taxonomy_initialized is False:
                print('Run the init(data_dir_path=\'DB_PATH\') method first.')
                return
            value = func(cls, *args, **kwargs)
            return value

        return wrapper_func

    @classmethod
    def update(cls, logger=Log):

        if cls._data_dir_path is None:
            logger.wrn('Run the init(data_dir_path=\'DB_PATH\') method first.')
            return

        cls._tax_dmp_path = os.path.join(cls._data_dir_path, 'taxdmp')
        make_dirs(path=cls._tax_dmp_path)

        cls._tax_cat_path = os.path.join(cls._data_dir_path, 'taxcat')
        make_dirs(path=cls._tax_cat_path)

        cls._tax_names_dmp_path = os.path.join(cls._tax_dmp_path, 'names.dmp')
        cls._tax_nodes_dmp_path = os.path.join(cls._tax_dmp_path, 'nodes.dmp')
        cls._tax_delnodes_dmp_path = os.path.join(cls._tax_dmp_path, 'delnodes.dmp')
        cls._tax_merged_dmp_path = os.path.join(cls._tax_dmp_path, 'merged.dmp')
        cls._tax_gencode_dmp_path = os.path.join(cls._tax_dmp_path, 'gencode.dmp')

        cls._tax_gencode_prt_path = os.path.join(cls._tax_dmp_path, 'gc.prt')

        logger.inf('Updating NCBI taxonomy data if necessary or requested.')

        download_taxdmp, download_taxcat = update_ncbi_taxonomy_data(
            taxdmp_path=cls._tax_dmp_path,
            taxcat_path=cls._tax_cat_path,
            force_redownload=False,
            check_for_updates=True,
            logger=logger)

        if download_taxdmp is False and download_taxcat is False:
            if cls._taxonomy_initialized:
                return

        logger.msg('Loading NCBI taxonomy data.')

        cls._codons = parse_codons(
            tax_gencode_prt_path=cls._tax_gencode_prt_path)

        cls._tax_dict = parse_names_dump(file_path=cls._tax_names_dmp_path)
        cls._taxids_names_dict = cls._tax_dict['tax_id_keyed_dict']
        cls._names_taxids_dict = cls._tax_dict['name_keyed_dict']

        cls._taxids_deleted_set = parse_delnodes_dump(
            file_path=cls._tax_delnodes_dmp_path)

        cls._taxids_merged_dict = parse_merged_dump(
            file_path=cls._tax_merged_dmp_path)

        parse_nodes_dump_result = parse_nodes_dump(
            file_path=cls._tax_nodes_dmp_path)

        cls._taxids_parent_children_dict = parse_nodes_dump_result[0]
        cls._taxids_child_parent_dict = parse_nodes_dump_result[1]
        cls._taxids_rank_dict = parse_nodes_dump_result[2]
        cls._taxids_genetic_code_id_dict = parse_nodes_dump_result[3]
        cls._taxids_mito_genetic_code_id_dict = parse_nodes_dump_result[4]

        parse_gencode_dump_result = parse_gencode_dump(
            file_path=cls._tax_gencode_dmp_path)

        cls._gen_code_id_name_dict = parse_gencode_dump_result[0]
        cls._gen_code_id_translation_table_dict = parse_gencode_dump_result[1]
        cls._gen_code_id_start_codons_dict = parse_gencode_dump_result[2]

        cls._name_classes = list(NAME_CLASS_SET)
        cls._name_classes.sort()

        cls._taxonomy_initialized = True

    # class properties =======================================================
    @initialized
    def codons(cls):
        return cls._codons

    @initialized
    def name_classes(cls):
        return cls._name_classes

    # class methods ==========================================================
    @initialized
    def taxid_valid(cls, taxid):
        taxid = str(taxid)
        taxid_valid = False
        if taxid in cls._taxids_child_parent_dict or \
                taxid in cls._taxids_merged_dict or \
                taxid in cls._taxids_deleted_set:
            taxid_valid = True
        return taxid_valid

    @initialized
    def taxid_valid_raise(cls, taxid):
        taxid = str(taxid)
        if not cls.taxid_valid(taxid):
            message = 'TaxID: \'{t}\' is not valid.'
            message = message.format(t=taxid)
            raise Exception(message)

    @initialized
    def taxid_deleted(cls, taxid):
        taxid = str(taxid)
        cls.taxid_valid_raise(taxid)
        taxid_deleted = False
        if taxid in cls._taxids_deleted_set:
            taxid_deleted = True
        return taxid_deleted

    @initialized
    def taxid_merged(cls, taxid):
        taxid = str(taxid)
        cls.taxid_valid_raise(taxid)
        taxid_merged = False
        if taxid in cls._taxids_merged_dict:
            taxid_merged = cls._taxids_merged_dict[taxid]
        return taxid_merged

    @initialized
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

    @initialized
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

    @initialized
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

    @initialized
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

    @initialized
    def name_for_taxid(cls, taxid, name_class='scientific name'):
        cls.taxid_valid_raise(taxid)
        name = cls.name_class_for_taxid(taxid, name_class)
        name = name['name']
        if name is not None:
            name = name[0]
        else:
            name = None
        return name

    @initialized
    def scientific_name_for_taxid(cls, taxid):
        name = cls.name_for_taxid(taxid, 'scientific name')
        return name

    @initialized
    def common_name_for_taxid(cls, taxid):
        name = cls.name_for_taxid(taxid, 'common name')
        return name

    @initialized
    def genbank_common_name_for_taxid(cls, taxid):
        name = cls.name_for_taxid(taxid, 'genbank common name')
        return name

    @initialized
    def rank_for_taxid(cls, taxid):
        taxid = str(taxid)
        cls.taxid_valid_raise(taxid)
        return_rank = None
        taxid = cls.updated_taxid(taxid=taxid)
        if taxid in cls._taxids_rank_dict:
            return_rank = cls._taxids_rank_dict[taxid]

        return return_rank

    @initialized
    def parent_taxid(cls, taxid):
        taxid = str(taxid)
        cls.taxid_valid_raise(taxid)
        return_taxid = None
        taxid = cls.updated_taxid(taxid=taxid)
        if taxid in cls._taxids_child_parent_dict:
            return_taxid = cls._taxids_child_parent_dict[taxid]

        return return_taxid

    @initialized
    def children_taxids(cls, taxid):
        taxid = str(taxid)
        cls.taxid_valid_raise(taxid)
        return_taxids = None
        taxid = cls.updated_taxid(taxid=taxid)
        if taxid in cls._taxids_parent_children_dict:
            return_taxids = cls._taxids_parent_children_dict[taxid]

        return return_taxids

    @initialized
    def all_descending_taxids(cls, taxid):
        cls.taxid_valid_raise(taxid)
        return_taxids = cls.children_taxids(taxid)
        if return_taxids is not None:
            for chld_txid in return_taxids:
                rabbit_hole = cls.all_descending_taxids(chld_txid)
                if rabbit_hole is not None:
                    return_taxids = return_taxids + rabbit_hole

        return return_taxids

    @initialized
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

    @initialized
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
                            tuple(reversed(paths[0])) +
                            (tuple(shared)[-1][0],) + paths[1]))

        return path

    @initialized
    def higher_rank_for_taxid(cls, taxid, rank, name_class='scientific name'):
        taxid = str(taxid)
        cls.taxid_valid_raise(taxid)
        lineage = cls.lineage_for_taxid(taxid=taxid, name_class=name_class)
        if rank in lineage['ranks']:
            rank_index = lineage['ranks'].index(rank)
        else:
            return None
        return lineage['names'][rank_index]

    @initialized
    def shared_taxid_for_taxids(cls, taxids):
        assert type(taxids) in (list, tuple, set)
        if len(taxids) == 0:
            return None
        shared = None
        for taxid in taxids:
            cls.taxid_valid_raise(taxid)
            lineage = cls.lineage_for_taxid(taxid=taxid)['taxids']
            if shared is None:
                shared = set(lineage)
            else:
                shared = shared & set(lineage)

        shared_lineage = tuple()
        for taxid in shared:
            lineage = cls.lineage_for_taxid(taxid=taxid)['taxids']
            if len(lineage) > len(shared_lineage):
                shared_lineage = lineage
        return int(shared_lineage[-1])

    @initialized
    def all_descending_taxids_for_taxids(cls, taxids):
        shared = cls.shared_taxid_for_taxids(taxids)
        if shared is None:
            return None
        taxids = cls.all_descending_taxids(taxid=shared)
        if taxids is None:
            taxids = [shared]
        taxids = [int(x) for x in taxids]
        return taxids

    @initialized
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

    @initialized
    def is_eukaryote(cls, taxid):
        taxid = str(taxid)
        cls.taxid_valid_raise(taxid)
        euk_taxid = 2759
        shared_taxid = cls.shared_taxid_for_taxids([euk_taxid, taxid])
        if shared_taxid == euk_taxid:
            return True
        else:
            return False

    @initialized
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

    @initialized
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

    @initialized
    def genetic_code_for_taxid(cls, taxid):
        taxid = str(taxid)
        cls.taxid_valid_raise(taxid)
        gcid = cls._taxids_genetic_code_id_dict[taxid]
        return gcid

    @initialized
    def mito_genetic_code_for_taxid(cls, taxid):
        taxid = str(taxid)
        cls.taxid_valid_raise(taxid)
        gcid = cls._taxids_mito_genetic_code_id_dict[taxid]
        return gcid

    @initialized
    def plastid_genetic_code_for_taxid(cls, taxid):
        taxid = str(taxid)
        cls.taxid_valid_raise(taxid)
        # --------------------------------------------
        # ToDo: Balanophoraceae uses 32 instead of 11?
        # Check this, NCBI taxonomy DB reports 11.
        # https://www.ncbi.nlm.nih.gov/pubmed/30598433
        # --------------------------------------------
        return '11'

    @initialized
    def trans_table_for_tax_id(cls, taxid):
        taxid = str(taxid)
        cls.taxid_valid_raise(taxid)
        gcid = cls.genetic_code_for_taxid(taxid)
        tt = cls.trans_table_for_genetic_code_id(gcid)
        return tt

    @initialized
    def mito_trans_table_for_tax_id(cls, taxid):
        taxid = str(taxid)
        cls.taxid_valid_raise(taxid)
        gcid = cls.mito_genetic_code_for_taxid(taxid)
        tt = cls.trans_table_for_genetic_code_id(gcid)
        return tt

    @initialized
    def plastid_trans_table_for_tax_id(cls, taxid):
        taxid = str(taxid)
        cls.taxid_valid_raise(taxid)
        tt = cls.trans_table_for_genetic_code_id(cls.plastid_genetic_code(taxid))
        return tt
