from sqlalchemy import insert, update
from sqlalchemy.orm import Session

from .model_sql import (Citation, Codon, DeletedNode, Division, GeneticCode,
                        Image, MergedNode, Name, Node,
                        assoc_table_nodes_citations, assoc_table_nodes_images)
from .ncbi import codons_from_gc_prt_file, rows_from_dmp_file


def populate_nodes_table(dmp_file_path, session: Session):
    rows = rows_from_dmp_file(dmp_file_path)
    table_rows = list()
    for r in rows:
        embl_code = None
        if r[3] != '':
            embl_code = r[3]
        mitochondrial_genetic_code_id = None
        if r[8] != '0':
            mitochondrial_genetic_code_id = int(r[8])
        comments = None
        if r[12] != '':
            comments = r[12]

        nd = {
            'tax_id': int(r[0]),
            # 'parent_tax_id': int(r[1]),
            'parent_tax_id': 1,
            'rank': r[2],
            'embl_code': embl_code,
            'division_id': int(r[4]),
            # 'inherited_div_flag':bool(int(r[5])),
            'genetic_code_id': int(r[6]),
            # 'inherited_GC_flag':bool(int(r[7])),
            'mitochondrial_genetic_code_id': mitochondrial_genetic_code_id,
            # 'inherited_MGC_flag':bool(int(r[9])),
            'genbank_hidden_flag': bool(int(r[10])),
            # 'hidden_subtree_root_flag':bool(int(r[11])),
            'comments': comments}

        table_rows.append(nd)

    session.execute(
        insert(Node),
        table_rows
    )

    session.commit()

    rows = rows_from_dmp_file(dmp_file_path)
    table_rows = list()
    for r in rows:
        nd = {
            'tax_id': int(r[0]),
            'parent_tax_id': int(r[1])}

        table_rows.append(nd)

    session.execute(
        update(Node),
        table_rows
    )

    session.commit()


def populate_names_table(dmp_file_path, session: Session):
    rows = rows_from_dmp_file(dmp_file_path)
    table_rows = list()
    for r in rows:
        unique_name = None
        if r[2] != '':
            unique_name = r[2]

        nm = {'tax_id': r[0],
              'name': r[1],
              'unique_name': unique_name,
              'name_class': r[3]}

        table_rows.append(nm)

    session.execute(
        insert(Name),
        table_rows
    )

    session.commit()


def populate_divisions_table(dmp_file_path, session: Session):
    rows = rows_from_dmp_file(dmp_file_path)
    table_rows = list()
    for r in rows:
        comments = None
        if r[3] != '':
            comments = r[3]

        dv = {'id': r[0],
              'code': r[1],
              'name': r[2],
              'comments': comments}

        table_rows.append(dv)

    session.execute(
        insert(Division),
        table_rows
    )

    session.commit()


def populate_genetic_codes_table(dmp_file_path, session: Session):
    rows = rows_from_dmp_file(dmp_file_path)
    table_rows = list()
    for r in rows:
        # abbreviation = None
        # if r[1] != '':
        #     abbreviation = r[1]

        gc = {
            'id': r[0],
            # 'abbreviation':abbreviation,
            'name': r[2],
            'translation_table': r[3],
            'start_stop': r[4]}

        table_rows.append(gc)

    session.execute(
        insert(GeneticCode),
        table_rows
    )

    session.commit()


def populate_deleted_nodes_table(dmp_file_path, session: Session):
    rows = rows_from_dmp_file(dmp_file_path)
    table_rows = list()
    for r in rows:
        table_rows.append({'tax_id': r[0]})

    session.execute(
        insert(DeletedNode),
        table_rows
    )

    session.commit()


def populate_merged_nodes_table(dmp_file_path, session: Session):
    rows = rows_from_dmp_file(dmp_file_path)
    table_rows = list()
    for r in rows:

        mn = {'old_tax_id': r[0],
              'new_tax_id': r[1]}

        table_rows.append(mn)

    session.execute(
        insert(MergedNode),
        table_rows
    )

    session.commit()


def populate_codons_table(prt_file_path, session: Session):
    codons = codons_from_gc_prt_file(prt_file_path)
    table_rows = list()
    for c in codons:
        table_rows.append({'codon': c})

    session.execute(
        insert(Codon),
        table_rows
    )

    session.commit()


def populate_citations_table(dmp_file_path, session: Session):
    rows = rows_from_dmp_file(dmp_file_path)
    table_rows = list()
    for r in rows:
        id = int(r[0])
        key = r[1]
        # pubmed_id = r[2]
        medline_id = r[3]
        url = r[4].strip('/').strip('|')
        text = r[5].replace('\\n', ' ').replace('\\t', ' ').replace(
            '\\"', '"').replace('\\\\\\', '\\').replace('\\\\', '\\').replace('  ', ' ')
        if key == '':
            key = None
        # if pubmed_id == '0':
        #     pubmed_id = None
        if medline_id == '0':
            medline_id = None
        if url == '':
            url = None
        if text == '':
            text = None

        # tax_ids = list(map(lambda x: int(x), filter(
        #     lambda x: x != '', r[6].split(' '))))
        # for txid in tax_ids:
        #     session.execute(
        #         assoc_table_nodes_citations.insert().values(tax_id=txid, citation_id=id))

        ct = {
            'id': id,
            'citation_key': key,
            # 'pubmed_id':pubmed_id,
            'medline_id': medline_id,
            'url': url,
            'text': text}

        table_rows.append(ct)

    session.execute(
        insert(Citation),
        table_rows
    )

    session.commit()

    rows = rows_from_dmp_file(dmp_file_path)
    for r in rows:
        id = int(r[0])

        tax_ids = list(map(lambda x: int(x), filter(
            lambda x: x != '', r[6].split(' '))))

        for txid in tax_ids:
            session.execute(
                assoc_table_nodes_citations.insert().values(tax_id=txid, citation_id=id))

    session.commit()


def populate_images_table(dmp_file_path, session: Session):
    rows = rows_from_dmp_file(dmp_file_path)
    table_rows = list()
    for r in rows:
        id = int(r[0])
        key = r[1].replace('image:', '')
        url = r[2].strip('/').strip('|')
        license = r[3]
        attribution = r[4].replace('\\n', ' ').replace('\\t', ' ').replace(
            '\\"', '"').replace('\\\\\\', '\\').replace('\\\\', '\\').replace('  ', ' ')
        source = r[5].replace('\\n', ' ').replace('\\t', ' ').replace(
            '\\"', '"').replace('\\\\\\', '\\').replace('\\\\', '\\').replace('  ', ' ')
        # properties = r[6]
        if attribution == '':
            attribution = None
        # if properties == '':
        #     properties = None

        # tax_ids = list(map(lambda x: int(x), filter(
        #     lambda x: x != '', r[7].split(' '))))
        # for txid in tax_ids:
        #     session.execute(
        #         assoc_table_nodes_images.insert().values(tax_id=txid, img_id=id))

        im = {
            'id': id,
            'image_key': key,
            'url': url,
            'license': license,
            'attribution': attribution,
            'source': source,
            # 'properties':properties,
        }

        table_rows.append(im)

    session.execute(
        insert(Image),
        table_rows
    )

    session.commit()

    rows = rows_from_dmp_file(dmp_file_path)
    for r in rows:
        id = int(r[0])
        tax_ids = list(map(lambda x: int(x), filter(
            lambda x: x != '', r[7].split(' '))))
        for txid in tax_ids:
            session.execute(
                assoc_table_nodes_images.insert().values(tax_id=txid, img_id=id))

    session.commit()
