from os.path import join as opj
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from .utils import Log, make_dirs
from .ncbi import TAXDMP_FILES, update_ncbi_taxonomy_data
from .model_sql import BaseSQLModel
from .populate_sql import (
    populate_citations_table, populate_codons_table,
    populate_deleted_nodes_table, populate_divisions_table,
    populate_genetic_codes_table, populate_images_table,
    populate_merged_nodes_table, populate_names_table, populate_nodes_table)


NAME_CLASS_SET = {'acronym', 'teleomorph', 'scientific name', 'synonym',
                  'blast name', 'misspelling', 'in-part', 'includes',
                  'genbank acronym', 'misnomer', 'common name',
                  'equivalent name', 'type material', 'authority',
                  'genbank common name', 'genbank synonym', 'anamorph',
                  'genbank anamorph'}


DIR_BASE = opj('~', '.local', 'share', 'ncbi-taxonomy-local')


def init_local_storage(dir_local_storage=DIR_BASE, force_redownload=False,
                       check_for_updates=False, logger=Log):

    dir_base = make_dirs(dir_local_storage)
    dir_cache = make_dirs(opj(dir_base, 'cache'))
    dir_images = make_dirs(opj(dir_cache, 'images'))
    dir_db = make_dirs(opj(dir_base, 'database'))
    dir_ncbi = make_dirs(opj(dir_base, 'ncbi-files'))
    dir_taxdmp = make_dirs(opj(dir_ncbi, 'taxdmp'))

    file_citations = opj(dir_taxdmp, TAXDMP_FILES['citations'])
    file_delnodes = opj(dir_taxdmp, TAXDMP_FILES['delnodes'])
    file_division = opj(dir_taxdmp, TAXDMP_FILES['division'])
    file_gc = opj(dir_taxdmp, TAXDMP_FILES['gc'])
    file_gencode = opj(dir_taxdmp, TAXDMP_FILES['gencode'])
    file_images = opj(dir_taxdmp, TAXDMP_FILES['images'])
    file_merged = opj(dir_taxdmp, TAXDMP_FILES['merged'])
    file_names = opj(dir_taxdmp, TAXDMP_FILES['names'])
    file_nodes = opj(dir_taxdmp, TAXDMP_FILES['nodes'])

    file_db = opj(dir_db, 'taxonomy.db')

    update_ncbi_taxonomy_data(taxdmp_path=dir_taxdmp,
                              force_redownload=force_redownload,
                              check_for_updates=check_for_updates,
                              logger=logger)

    paths = {
        'dir_base': dir_base,
        'dir_cache': dir_cache,
        'dir_images': dir_images,
        'dir_db': dir_db,
        'dir_ncbi': dir_ncbi,
        'dir_taxdmp': dir_taxdmp,
        'file_citations': file_citations,
        'file_delnodes': file_delnodes,
        'file_division': file_division,
        'file_gc': file_gc,
        'file_gencode': file_gencode,
        'file_images': file_images,
        'file_merged': file_merged,
        'file_names': file_names,
        'file_nodes': file_nodes,
        'file_db': file_db}

    return paths


def init_db(paths: dict[str, str]):
    file_db = paths['file_db']
    engine = create_engine(f'sqlite:///{file_db}')
    BaseSQLModel.metadata.create_all(engine)
    Session = sessionmaker(engine)
    return Session


def populate_db(paths: dict[str, str], session: Session):
    file_citations = paths['file_citations']
    file_delnodes = paths['file_delnodes']
    file_division = paths['file_division']
    file_gc = paths['file_gc']
    file_gencode = paths['file_gencode']
    file_images = paths['file_images']
    file_merged = paths['file_merged']
    file_names = paths['file_names']
    file_nodes = paths['file_nodes']

    populate_citations_table(file_citations, session)
    populate_deleted_nodes_table(file_delnodes, session)
    populate_divisions_table(file_division, session)
    populate_codons_table(file_gc, session)
    populate_genetic_codes_table(file_gencode, session)
    populate_images_table(file_images, session)
    populate_merged_nodes_table(file_merged, session)
    populate_names_table(file_names, session)
    populate_nodes_table(file_nodes, session)
