from sqlalchemy.orm import Session
from sqlalchemy import Null
from .ncbi import codons_from_gc_prt_file, rows_from_dmp_file
from .model_sql import (
    Node, Name, Division, GeneticCode, DeletedNode, MergedNode, Codon,
    Citation, Image, assoc_table_nodes_citations, assoc_table_nodes_images)


def populate_nodes_table(dmp_file_path, session: Session):
    rows = rows_from_dmp_file(dmp_file_path)
    for r in rows:
        embl_code = Null()
        if r[3] != '':
            embl_code = r[3]
        mitochondrial_genetic_code_id = Null()
        if r[8] != '0':
            mitochondrial_genetic_code_id = int(r[8])
        comments = Null()
        if r[12] != '':
            comments = r[12]
        node = Node(
            tax_id=int(r[0]),
            parent_tax_id=int(r[1]),
            rank=r[2],
            embl_code=embl_code,
            division_id=int(r[4]),
            # inherited_div_flag=bool(int(r[5])),
            genetic_code_id=int(r[6]),
            # inherited_GC_flag=bool(int(r[7])),
            mitochondrial_genetic_code_id=mitochondrial_genetic_code_id,
            # inherited_MGC_flag=bool(int(r[9])),
            genbank_hidden_flag=bool(int(r[10])),
            # hidden_subtree_root_flag=bool(int(r[11])),
            comments=comments)
        session.add(node)
    session.commit()


def populate_names_table(dmp_file_path, session: Session):
    rows = rows_from_dmp_file(dmp_file_path)
    for r in rows:
        unique_name = Null()
        if r[2] != '':
            unique_name = r[2]
        nm = Name(tax_id=r[0],
                  name=r[1],
                  unique_name=unique_name,
                  name_class=r[3])
        session.add(nm)
    session.commit()


def populate_divisions_table(dmp_file_path, session: Session):
    rows = rows_from_dmp_file(dmp_file_path)
    for r in rows:
        comments = Null()
        if r[3] != '':
            comments = r[3]
        dv = Division(id=r[0],
                      code=r[1],
                      name=r[2],
                      comments=comments)
        session.add(dv)
    session.commit()


def populate_genetic_codes_table(dmp_file_path, session: Session):
    rows = rows_from_dmp_file(dmp_file_path)
    for r in rows:
        # abbreviation = Null()
        # if r[1] != '':
        #     abbreviation = r[1]
        gc = GeneticCode(
            id=r[0],
            # abbreviation=abbreviation,
            name=r[2],
            translation_table=r[3],
            start_stop=r[4])
        session.add(gc)
    session.commit()


def populate_deleted_nodes_table(dmp_file_path, session: Session):
    rows = rows_from_dmp_file(dmp_file_path)
    for r in rows:
        session.add(DeletedNode(tax_id=r[0]))


def populate_merged_nodes_table(dmp_file_path, session: Session):
    rows = rows_from_dmp_file(dmp_file_path)
    for r in rows:
        mn = MergedNode(old_tax_id=r[0],
                        new_tax_id=r[1])
        session.add(mn)
    session.commit()


def populate_codons_table(prt_file_path, session: Session):
    codons = codons_from_gc_prt_file(prt_file_path)
    for c in codons:
        session.add(Codon(codon=c))
    session.commit()


def populate_citations_table(dmp_file_path, session: Session):
    rows = rows_from_dmp_file(dmp_file_path)
    for r in rows:
        id = int(r[0])
        key = r[1]
        # pubmed_id = r[2]
        medline_id = r[3]
        url = r[4].strip('/').strip('|')
        text = r[5].replace('\\n', ' ').replace('\\t', ' ').replace(
            '\\"', '"').replace('\\\\\\', '\\').replace('\\\\', '\\').replace('  ', ' ')
        tax_ids = list(map(lambda x: int(x), filter(
            lambda x: x != '', r[6].split(' '))))
        if key == '':
            key = Null()
        # if pubmed_id == '0':
        #     pubmed_id = Null()
        if medline_id == '0':
            medline_id = Null()
        if url == '':
            url = Null()
        if text == '':
            text = Null()
        for txid in tax_ids:
            session.execute(
                assoc_table_nodes_citations.insert().values(tax_id=txid, citation_id=id))
        ct = Citation(
            id=id,
            key=key,
            # pubmed_id=pubmed_id,
            medline_id=medline_id,
            url=url,
            text=text)
        session.add(ct)
    session.commit()


def populate_images_table(dmp_file_path, session: Session):
    rows = rows_from_dmp_file(dmp_file_path)
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
            attribution = Null()
        # if properties == '':
        #     properties = Null()
        tax_ids = list(map(lambda x: int(x), filter(
            lambda x: x != '', r[7].split(' '))))
        for txid in tax_ids:
            session.execute(
                assoc_table_nodes_images.insert().values(tax_id=txid, img_id=id))
        im = Image(
            id=id,
            key=key,
            url=url,
            license=license,
            attribution=attribution,
            source=source,
            # properties=properties,
        )
        session.add(im)
    session.commit()
