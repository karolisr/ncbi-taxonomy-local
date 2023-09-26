import os
from shutil import move

from os.path import join as opj
from .utils import Log
from .utils import (download_file, extract_md5_hash, make_dirs,
                    dnld_zip_check_md5_then_extract, diff_files)


TAX_BASE_URL = 'https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/'
TAXDMP_ZIP = 'taxdmp.zip'
TAXDMP_FILES = {
    'citations': 'citations.dmp',
    'delnodes': 'delnodes.dmp',
    'division': 'division.dmp',
    'gc': 'gc.prt',
    'gencode': 'gencode.dmp',
    'images': 'images.dmp',
    'md5': 'taxdmp.zip.md5',
    'merged': 'merged.dmp',
    'names': 'names.dmp',
    'nodes': 'nodes.dmp',
    'readme': 'readme.txt'}


def update_ncbi_taxonomy_data(taxdmp_path, force_redownload=False,
                              check_for_updates=True, logger=Log):

    download_taxdmp = False
    taxdmp_zip_path = opj(taxdmp_path, TAXDMP_ZIP)
    taxdmp_md5_url = opj(TAX_BASE_URL, TAXDMP_FILES['md5'])
    taxdmp_md5_path = opj(taxdmp_path, TAXDMP_FILES['md5'])
    taxdmp_md5_path_new = taxdmp_md5_path + '_new'

    if force_redownload is True:
        download_taxdmp = True
    else:
        for file_name in tuple(TAXDMP_FILES.values()):
            file_path = opj(taxdmp_path, file_name)
            if os.path.exists(file_path) is False:
                download_taxdmp = True
                break

        if check_for_updates is True:
            if download_taxdmp is False:
                download_file(taxdmp_md5_url, taxdmp_md5_path_new)
                old_md5 = extract_md5_hash(taxdmp_md5_path)
                new_md5 = extract_md5_hash(taxdmp_md5_path_new)
                os.remove(taxdmp_md5_path_new)
                logger.msg('Previous MD5 for the taxdmp file:', old_md5)
                logger.msg('     New MD5 for the taxdmp file:', new_md5)
                if old_md5 != new_md5:
                    download_taxdmp = True

    if download_taxdmp is True:
        if os.path.exists(taxdmp_md5_path):
            logger.wrn('Backing up existing taxdmp directory.')
            move(taxdmp_path, f'{taxdmp_path}.bak')
            make_dirs(taxdmp_path)
        logger.wrn('Downloading taxdmp file from NCBI.')
        dnld_zip_check_md5_then_extract(
            directory_path=taxdmp_path,
            zip_url=f'{TAX_BASE_URL}{TAXDMP_ZIP}',
            md5_url=taxdmp_md5_url,
            zip_path=taxdmp_zip_path,
            md5_path=taxdmp_md5_path,
            logger=logger)
        os.remove(taxdmp_zip_path)

    return download_taxdmp


def rows_from_dmp_lines(lines: list[str]):
    # From the NCBI readme file:
    #   *.dmp files are bcp-like dump from GenBank taxonomy database.
    #   Field terminator is "\t|\t"
    #   Row terminator is "\t|\n"

    row_trm = '|'
    fld_trm = '\t|'

    ls = map(lambda l: l.strip(row_trm), lines)
    return map(lambda l: tuple(map(lambda f: f.strip(), l.split(fld_trm))), ls)


def rows_from_dmp_file(file_path):
    with open(file_path, 'r') as f:
        ls = f.read().splitlines()
    return rows_from_dmp_lines(ls)


def codons_from_gc_prt_file(file_path):
    base1 = base2 = base3 = ''

    base1_start = '  -- Base1  '
    base2_start = '  -- Base2  '
    base3_start = '  -- Base3  '

    with open(file_path, 'r') as f:
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
    return [''.join(x) for x in cs]


def parse_names_dump(file_path):
    rows = rows_from_dmp_file(file_path=file_path)

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
    rows = rows_from_dmp_file(file_path=file_path)
    tax_id_set = set()
    for r in rows:
        tax_id_set.add(r[0])
    return tax_id_set


def parse_merged_dump(file_path):
    rows = rows_from_dmp_file(file_path=file_path)
    new_to_old_tax_id_mapping_dict = dict()
    for r in rows:
        old_tax_id = r[0]
        new_tax_id = r[1]
        new_to_old_tax_id_mapping_dict[old_tax_id] = new_tax_id
    return new_to_old_tax_id_mapping_dict


def parse_nodes_dump(file_path):
    rows = rows_from_dmp_file(file_path=file_path)

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
    rows = rows_from_dmp_file(file_path=file_path)

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


def diff_dmp_files(old, new):

    drop_lines, add_lines = diff_files(old, new)

    with open('drop_lines.dmp', 'w') as dlf:
        dlf.writelines(drop_lines)

    with open('add_lines.dmp', 'w') as alf:
        alf.writelines(add_lines)

    list(rows_from_dmp_file('drop_lines.dmp'))
