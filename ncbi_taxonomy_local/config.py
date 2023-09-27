import contextlib
from os.path import join as opj

import sqlalchemy.exc
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from .model_sql import BaseSQLModel
from .ncbi import TAXDMP_FILES, update_ncbi_taxonomy_data
from .populate_sql import (populate_citations_table, populate_codons_table,
                           populate_deleted_nodes_table,
                           populate_divisions_table,
                           populate_genetic_codes_table, populate_images_table,
                           populate_merged_nodes_table, populate_names_table,
                           populate_nodes_table)

from .utils import Log, make_dirs

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


# PG_TERMINATE_CONNS = """
# -- Terminate any existing connections to this database
# SELECT
#     pg_terminate_backend(pg_stat_activity.pid)
# FROM
#     pg_stat_activity
# WHERE
#     pg_stat_activity.datname = 'taxonomy'
#     AND pid <> pg_backend_pid();
# """

# ------------------------------------------------------------------------
# engine = create_engine('postgresql+psycopg2://localhost/postgres', echo=echo)
# with contextlib.suppress(sqlalchemy.exc.ProgrammingError):
#     with engine.connect() as conn:
#         conn.execute(text('commit'))
#         conn.execute(text(PG_TERMINATE_CONNS))
#         conn.execute(text('commit'))
#         conn.execute(text('DROP DATABASE taxonomy'))
#         conn.execute(text('commit'))
#         conn.execute(text('CREATE DATABASE taxonomy'))
# ------------------------------------------------------------------------
# with contextlib.suppress(sqlalchemy.exc.ProgrammingError):
#     with engine.connect() as conn:
#         conn.execute(text('commit'))
#         conn.execute(text('CREATE DATABASE taxonomy'))
# ------------------------------------------------------------------------


def init_db(url: str, echo: bool = False):
    engine = create_engine(url, echo=echo)
    BaseSQLModel.metadata.create_all(bind=engine, checkfirst=True)
    Session = sessionmaker(engine)
    return Session


def populate_db(paths: dict[str, str], session: Session, logger=Log):

    file_division = paths['file_division']
    file_gc = paths['file_gc']
    file_gencode = paths['file_gencode']
    file_delnodes = paths['file_delnodes']
    file_nodes = paths['file_nodes']
    file_merged = paths['file_merged']
    file_names = paths['file_names']
    file_citations = paths['file_citations']
    file_images = paths['file_images']

    msg = 'Populating table:'

    Log.wrn(msg, 'divisions')
    # 1
    populate_divisions_table(file_division, session)

    Log.wrn(msg, 'codons')
    # 2
    populate_codons_table(file_gc, session)

    Log.wrn(msg, 'genetic_codes')
    # 3
    populate_genetic_codes_table(file_gencode, session)

    Log.wrn(msg, 'deleted_nodes')
    # 4
    populate_deleted_nodes_table(file_delnodes, session)

    Log.wrn(msg, 'nodes')
    # 5
    populate_nodes_table(file_nodes, session)

    Log.wrn(msg, 'merged_nodes')
    # 6
    populate_merged_nodes_table(file_merged, session)

    Log.wrn(msg, 'names')
    # 7
    populate_names_table(file_names, session)

    Log.wrn(msg, 'citations')
    # 8
    populate_citations_table(file_citations, session)

    Log.wrn(msg, 'images')
    # 9
    populate_images_table(file_images, session)
