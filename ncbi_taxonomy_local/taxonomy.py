# -*- coding: utf-8 -*-

"""
NCBI taxonomy databases outside of the ENTREZ system.
"""

from __future__ import print_function

import os
import zipfile

from ncbi_taxonomy_local.helpers import download_file
from ncbi_taxonomy_local.helpers import extract_md5_hash
from ncbi_taxonomy_local.helpers import generate_md5_hash_for_file
from ncbi_taxonomy_local.helpers import make_dir

TAX_BASE_URL = 'https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/'

# Files expected to be in taxdmp.zip MD5 file should be first
TAXDMP_FILES = ['taxdmp.zip.md5', 'readme.txt', 'nodes.dmp',
                'names.dmp', 'merged.dmp', 'gencode.dmp', 'gc.prt',
                'division.dmp', 'delnodes.dmp', 'citations.dmp']
TAXDMP_ARCHIVE = 'taxdmp.zip'

# Files expected to be in taxcat.zip MD5 file should be first
TAXCAT_FILES = ['taxcat.zip.md5', 'categories.dmp']
TAXCAT_ARCHIVE = 'taxcat.zip'


NAME_CLASS_SET = set([
    'acronym', 'teleomorph', 'scientific name', 'synonym', 'blast name',
    'misspelling', 'in-part', 'includes', 'genbank acronym', 'misnomer',
    'common name', 'equivalent name', 'type material', 'authority',
    'genbank common name', 'genbank synonym', 'anamorph', 'genbank anamorph'])


def download_ncbi_taxonomy_data(directory_path,  # noqa
                                archive_url,
                                md5_url,
                                archive_path,
                                md5_path):

    download_file(archive_url, archive_path)
    download_file(md5_url, md5_path)

    md5_reported = extract_md5_hash(file_path=md5_path)
    print('\n\t\tmd5_reported:', md5_reported)
    md5_actual = generate_md5_hash_for_file(file_path=archive_path)
    print('\t\t  md5_actual:', md5_actual)

    if md5_reported != md5_actual:
        message = (
            'MD5 hash of the file {f} does not match the reported '
            'hash in file {r}')
        message = message.format(f=archive_path, r=md5_path)
        raise Exception(message)
    else:
        z = zipfile.ZipFile(file=archive_path, mode='r')
        z.extractall(path=directory_path)
        return True


def update_ncbi_taxonomy_data(taxdmp_path, taxcat_path,  # noqa
                              force_redownload=False,
                              check_for_updates=True):

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

                print('\n\t\ttaxdmp old_md5:', old_md5)
                print('\t\ttaxdmp new_md5:', new_md5)

                if old_md5 != new_md5:
                    download_taxdmp = True

            if not download_taxcat:
                download_file(taxcat_md5_url, taxcat_md5_path_new)

                old_md5 = extract_md5_hash(file_path=taxcat_md5_path)
                new_md5 = extract_md5_hash(file_path=taxcat_md5_path_new)

                os.remove(taxcat_md5_path_new)

                print('\n\t\ttaxcat old_md5:', old_md5)
                print('\t\ttaxcat new_md5:', new_md5)

                if old_md5 != new_md5:
                    download_taxcat = True

    else:
        download_taxdmp = True
        download_taxcat = True

    print('\n\t\tDownload taxdmp:', download_taxdmp)
    print('\t\tDownload taxcat:', download_taxcat)

    if download_taxdmp:
        download_ncbi_taxonomy_data(
            directory_path=taxdmp_path,
            archive_url=TAX_BASE_URL + TAXDMP_ARCHIVE,
            md5_url=taxdmp_md5_url,
            archive_path=taxdmp_archive_path,
            md5_path=taxdmp_md5_path)

        os.remove(taxdmp_archive_path)

    if download_taxcat:
        download_ncbi_taxonomy_data(
            directory_path=taxcat_path,
            archive_url=TAX_BASE_URL + TAXCAT_ARCHIVE,
            md5_url=taxcat_md5_url,
            archive_path=taxcat_archive_path,
            md5_path=taxcat_md5_path)

        os.remove(taxcat_archive_path)

    return [download_taxdmp, download_taxcat]


def parse_ncbi_taxonomy_dump_file(file_path):  # noqa

    field_terminator = '\t|\t'
    row_terminator = '\t|\n'

    f = open(file_path, 'r')

    lines = list()

    for line in f:
        line = line.strip(row_terminator)
        line = line.split(field_terminator)
        lines.append(line)

    f.close()

    return lines


def parse_codons(tax_gencode_prt_path):  # noqa

    base1 = ''
    base2 = ''
    base3 = ''

    base1_start = '  -- Base1  '
    base2_start = '  -- Base2  '
    base3_start = '  -- Base3  '

    with open(tax_gencode_prt_path, 'r') as f:
        for line in f:
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


def parse_names_dump(file_path):  # noqa

    rows = parse_ncbi_taxonomy_dump_file(file_path=file_path)
    tax_id_keyed_dict = dict()
    name_keyed_dict = dict()

    for r in rows:

        tax_id = r[0]
        name = r[1]
        unique_name = r[2]
        name_class = r[3]

        # tax_id_keyed_dict
        if tax_id not in tax_id_keyed_dict:
            tax_id_keyed_dict[tax_id] = list()

        tax_id_keyed_dict_entry = {
            'name': name,
            'unique_name': unique_name,
            'name_class': name_class}

        tax_id_keyed_dict[tax_id].append(tax_id_keyed_dict_entry)

        # name_keyed_dict
        if name not in name_keyed_dict:
            name_keyed_dict[name] = list()

        name_keyed_dict_entry = {
            'tax_id': tax_id,
            'unique_name': unique_name,
            'name_class': name_class}

        name_keyed_dict[name].append(name_keyed_dict_entry)

    return {'tax_id_keyed_dict': tax_id_keyed_dict,
            'name_keyed_dict': name_keyed_dict}


def parse_delnodes_dump(file_path):  # noqa

    rows = parse_ncbi_taxonomy_dump_file(file_path=file_path)
    tax_id_set = set()

    for r in rows:

        tax_id = r[0]
        tax_id_set.add(tax_id)

    return tax_id_set


def parse_merged_dump(file_path):  # noqa

    rows = parse_ncbi_taxonomy_dump_file(file_path=file_path)
    new_to_old_tax_id_mapping_dict = dict()

    for r in rows:

        old_tax_id = r[0]
        new_tax_id = r[1]

        new_to_old_tax_id_mapping_dict[old_tax_id] = new_tax_id

    return new_to_old_tax_id_mapping_dict


def parse_nodes_dump(file_path):  # noqa

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


def parse_gencode_dump(file_path):  # noqa

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


class Taxonomy(object):

    @classmethod
    def init(cls, data_dir_path, check_for_updates=True,):

        cls._data_dir_path = make_dir(path=os.path.expanduser(data_dir_path))

        cls._tax_dmp_path = os.path.join(cls._data_dir_path, 'taxdmp')
        make_dir(path=cls._tax_dmp_path)

        cls._tax_cat_path = os.path.join(cls._data_dir_path, 'taxcat')
        make_dir(path=cls._tax_cat_path)

        cls._tax_names_dmp_path = os.path.join(cls._tax_dmp_path, 'names.dmp')
        cls._tax_nodes_dmp_path = os.path.join(cls._tax_dmp_path, 'nodes.dmp')
        cls._tax_delnodes_dmp_path = os.path.join(cls._tax_dmp_path,
                                                  'delnodes.dmp')
        cls._tax_merged_dmp_path = os.path.join(cls._tax_dmp_path,
                                                'merged.dmp')
        cls._tax_gencode_dmp_path = os.path.join(cls._tax_dmp_path,
                                                 'gencode.dmp')

        cls._tax_gencode_prt_path = os.path.join(cls._tax_dmp_path, 'gc.prt')
        cls._check_for_updates = check_for_updates

        cls._taxonomy_initialized = False

    @classmethod
    def update(cls, check_for_updates=True):

        if cls._taxonomy_initialized:
            return

        print('Updating NCBI taxonomy data if necessary or requested.')

        update_ncbi_taxonomy_data(
            taxdmp_path=cls._tax_dmp_path,
            taxcat_path=cls._tax_cat_path,
            force_redownload=False,
            check_for_updates=check_for_updates)

        print('\nLoading NCBI taxonomy data.')

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

    # class properties =================================================
    @classmethod
    def codons(cls):
        cls.update(check_for_updates=cls._check_for_updates)
        return cls._codons

    @classmethod
    def name_classes(cls):
        cls.update(check_for_updates=cls._check_for_updates)
        return cls._name_classes

    # class methods ====================================================

    @classmethod
    def taxid_valid(cls, taxid):
        taxid = str(taxid)
        cls.update(check_for_updates=cls._check_for_updates)
        taxid_valid = False
        if taxid in cls._taxids_child_parent_dict or \
           taxid in cls._taxids_merged_dict or \
           taxid in cls._taxids_deleted_set:
            taxid_valid = True
        return taxid_valid

    @classmethod
    def taxid_valid_raise(cls, taxid):
        taxid = str(taxid)
        cls.update(check_for_updates=cls._check_for_updates)
        if not cls.taxid_valid(taxid):
            message = 'TaxID: \'{t}\' is not valid.'
            message = message.format(t=taxid)
            raise Exception(message)

    @classmethod
    def taxid_deleted(cls, taxid):
        taxid = str(taxid)
        cls.update(check_for_updates=cls._check_for_updates)
        cls.taxid_valid_raise(taxid)
        taxid_deleted = False
        if taxid in cls._taxids_deleted_set:
            taxid_deleted = True
        return taxid_deleted

    @classmethod
    def taxid_merged(cls, taxid):
        taxid = str(taxid)
        cls.update(check_for_updates=cls._check_for_updates)
        cls.taxid_valid_raise(taxid)
        taxid_merged = False
        if taxid in cls._taxids_merged_dict:
            taxid_merged = cls._taxids_merged_dict[taxid]
        return taxid_merged

    @classmethod
    def updated_taxid(cls, taxid):
        taxid = str(taxid)
        cls.update(check_for_updates=cls._check_for_updates)
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

    @classmethod
    def names_for_taxid(cls, taxid):
        taxid = str(taxid)
        cls.update(check_for_updates=cls._check_for_updates)
        cls.taxid_valid_raise(taxid)
        return_dict = dict()
        return_dict['old_taxid'] = taxid
        new_taxid = cls.updated_taxid(taxid=taxid)
        return_dict['new_taxid'] = new_taxid
        return_dict['names'] = None

        if new_taxid is not None:
            return_dict['names'] = cls._taxids_names_dict[new_taxid]

        return return_dict

    @classmethod
    def taxids_for_name(cls, name):
        cls.update(check_for_updates=cls._check_for_updates)

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

    @classmethod
    def name_class_for_taxid(cls, taxid, name_class='scientific name'):
        taxid = str(taxid)
        cls.update(check_for_updates=cls._check_for_updates)
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

    @classmethod
    def name_for_taxid(cls, taxid, name_class='scientific name'):
        cls.update(check_for_updates=cls._check_for_updates)
        cls.taxid_valid_raise(taxid)
        name = cls.name_class_for_taxid(taxid, name_class)
        name = name['name']
        if name is not None:
            name = name[0]
        else:
            name = None
        return name

    @classmethod
    def scientific_name_for_taxid(cls, taxid):
        name = cls.name_for_taxid(taxid, 'scientific name')
        return name

    @classmethod
    def common_name_for_taxid(cls, taxid):
        name = cls.name_for_taxid(taxid, 'common name')
        return name

    @classmethod
    def genbank_common_name_for_taxid(cls, taxid):
        name = cls.name_for_taxid(taxid, 'genbank common name')
        return name

    @classmethod
    def rank_for_taxid(cls, taxid):
        taxid = str(taxid)
        cls.update(check_for_updates=cls._check_for_updates)
        cls.taxid_valid_raise(taxid)
        return_rank = None
        taxid = cls.updated_taxid(taxid=taxid)
        if taxid in cls._taxids_rank_dict:
            return_rank = cls._taxids_rank_dict[taxid]

        return return_rank

    @classmethod
    def parent_taxid(cls, taxid):
        taxid = str(taxid)
        cls.update(check_for_updates=cls._check_for_updates)
        cls.taxid_valid_raise(taxid)
        return_taxid = None
        taxid = cls.updated_taxid(taxid=taxid)
        if taxid in cls._taxids_child_parent_dict:
            return_taxid = cls._taxids_child_parent_dict[taxid]

        return return_taxid

    @classmethod
    def children_taxids(cls, taxid):
        taxid = str(taxid)
        cls.update(check_for_updates=cls._check_for_updates)
        cls.taxid_valid_raise(taxid)
        return_taxids = None
        taxid = cls.updated_taxid(taxid=taxid)
        if taxid in cls._taxids_parent_children_dict:
            return_taxids = cls._taxids_parent_children_dict[taxid]

        return return_taxids

    @classmethod
    def all_descending_taxids(cls, taxid):
        cls.update(check_for_updates=cls._check_for_updates)
        cls.taxid_valid_raise(taxid)
        return_taxids = cls.children_taxids(taxid)
        if return_taxids is not None:
            for chld_txid in return_taxids:
                rabbit_hole = cls.all_descending_taxids(chld_txid)
                if rabbit_hole is not None:
                    return_taxids = return_taxids + rabbit_hole

        return return_taxids

    @classmethod
    def lineage_for_taxid(cls, taxid, name_class='scientific name'):
        taxid = str(taxid)
        cls.update(check_for_updates=cls._check_for_updates)
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

    @classmethod
    def higher_rank_for_taxid(cls, taxid, rank, name_class='scientific name'):
        taxid = str(taxid)
        cls.update(check_for_updates=cls._check_for_updates)
        cls.taxid_valid_raise(taxid)
        lineage = cls.lineage_for_taxid(taxid=taxid, name_class=name_class)
        if rank in lineage['ranks']:
            rank_index = lineage['ranks'].index(rank)
        else:
            return None
        return lineage['names'][rank_index]

    @classmethod
    def tax_id_for_name_and_group_tax_id(cls, name, group_tax_id):
        group_tax_id = str(group_tax_id)
        cls.update(check_for_updates=cls._check_for_updates)
        cls.taxid_valid_raise(taxid)
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
                print('Group is too broad')
                return None
        else:
            print('Organism does not belong to this group.')
            return None

        return ids[correct_tax_node_index]

    @classmethod
    def trans_table_for_genetic_code_id(cls, gcid):
        cls.update(check_for_updates=cls._check_for_updates)
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

    @classmethod
    def genetic_code_for_taxid(cls, taxid):
        taxid = str(taxid)
        cls.update(check_for_updates=cls._check_for_updates)
        cls.taxid_valid_raise(taxid)
        gcid = cls._taxids_genetic_code_id_dict[taxid]
        return gcid

    @classmethod
    def mito_genetic_code_for_taxid(cls, taxid):
        taxid = str(taxid)
        cls.update(check_for_updates=cls._check_for_updates)
        cls.taxid_valid_raise(taxid)
        gcid = cls._taxids_mito_genetic_code_id_dict[taxid]
        return gcid

    @classmethod
    def plastid_genetic_code(cls):
        cls.update(check_for_updates=cls._check_for_updates)
        return '11'

    @classmethod
    def trans_table_for_tax_id(cls, taxid):
        taxid = str(taxid)
        cls.update(check_for_updates=cls._check_for_updates)
        cls.taxid_valid_raise(taxid)
        gcid = cls.genetic_code_for_taxid(taxid)
        tt = cls.trans_table_for_genetic_code_id(gcid)
        return tt

    @classmethod
    def mito_trans_table_for_tax_id(cls, taxid):
        taxid = str(taxid)
        cls.update(check_for_updates=cls._check_for_updates)
        cls.taxid_valid_raise(taxid)
        gcid = cls.mito_genetic_code_for_taxid(taxid)
        tt = cls.trans_table_for_genetic_code_id(gcid)
        return tt

    @classmethod
    def plastid_trans_table(cls):
        cls.update(check_for_updates=cls._check_for_updates)
        tt = cls.trans_table_for_genetic_code_id(cls.plastid_genetic_code())
        return tt


def taxonomy(data_dir_path):
    if not hasattr(Taxonomy, '_taxonomy_initialized'):
        Taxonomy.init(data_dir_path=data_dir_path, check_for_updates=True)
        Taxonomy.update(check_for_updates=True)
    return Taxonomy
