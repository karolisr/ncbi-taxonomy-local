import os
import zipfile

from ncbi_taxonomy_local.misc import Log
from ncbi_taxonomy_local.misc import download_file
from ncbi_taxonomy_local.misc import extract_md5_hash
from ncbi_taxonomy_local.misc import generate_md5_hash_for_file


TAX_BASE_URL = 'https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/'

# Files expected to be in taxdmp.zip MD5 file should be first
TAXDMP_FILES = ['taxdmp.zip.md5', 'readme.txt', 'nodes.dmp',
                'names.dmp', 'merged.dmp', 'gencode.dmp', 'gc.prt',
                'division.dmp', 'delnodes.dmp', 'citations.dmp']
TAXDMP_ARCHIVE = 'taxdmp.zip'

# Files expected to be in taxcat.zip MD5 file should be first
TAXCAT_FILES = ['taxcat.zip.md5', 'categories.dmp']
TAXCAT_ARCHIVE = 'taxcat.zip'


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
