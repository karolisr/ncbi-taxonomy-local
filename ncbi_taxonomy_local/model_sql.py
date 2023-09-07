from __future__ import annotations
from typing import List, Optional
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Column, ForeignKey, String, Table


class BaseSQLModel(DeclarativeBase):
    pass


assoc_table_nodes_citations = Table(
    'assoc_nodes_citations', BaseSQLModel.metadata,
    Column('tax_id', ForeignKey('nodes.tax_id'), primary_key=True),
    Column('citation_id', ForeignKey('citations.id'), primary_key=True))

assoc_table_nodes_images = Table(
    'assoc_nodes_images', BaseSQLModel.metadata,
    Column('tax_id', ForeignKey('nodes.tax_id'), primary_key=True),
    Column('img_id', ForeignKey('images.id'), primary_key=True))


class Node(BaseSQLModel):
    __tablename__ = 'nodes'

    tax_id: Mapped[int] = mapped_column(primary_key=True)
    parent_tax_id: Mapped[int] = mapped_column(ForeignKey('nodes.tax_id'))
    rank: Mapped[str]
    embl_code: Mapped[Optional[str]]
    division_id: Mapped[int] = mapped_column(ForeignKey('divisions.id'))
    # inherited_div_flag: Mapped[bool]

    genetic_code_id: Mapped[int] = mapped_column(
        ForeignKey('genetic_codes.id'))

    # inherited_GC_flag: Mapped[bool]

    mitochondrial_genetic_code_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('genetic_codes.id'))

    # inherited_MGC_flag: Mapped[bool]
    genbank_hidden_flag: Mapped[bool]
    # hidden_subtree_root_flag: Mapped[bool]
    comments: Mapped[Optional[str]]

    children = relationship(
        'Node', back_populates='parent')

    parent = relationship(
        'Node', back_populates='children', remote_side=[tax_id])

    names = relationship('Name')

    division = relationship('Division', back_populates='nodes')

    citations: Mapped[List[Citation]] = relationship(
        secondary=assoc_table_nodes_citations,
        back_populates='nodes')

    images: Mapped[List[Image]] = relationship(
        secondary=assoc_table_nodes_images,
        back_populates='nodes')

    def __repr__(self) -> str:
        return f'Node(tax_id={self.tax_id!r}, ' \
            + f'parent_tax_id={self.parent_tax_id!r}, rank={self.rank!r}, ' \
            + f'genetic_code_id={self.genetic_code_id!r})'


class Name(BaseSQLModel):
    __tablename__ = 'names'

    id: Mapped[int] = mapped_column(primary_key=True)

    tax_id: Mapped[int] = mapped_column(ForeignKey('nodes.tax_id'))
    name: Mapped[str]
    unique_name: Mapped[Optional[str]]
    name_class: Mapped[str]

    def __repr__(self) -> str:
        return f'Name(tax_id={self.tax_id!r}, name={self.name!r}, ' \
            + f'unique_name={self.unique_name!r}, ' \
            + f'name_class={self.name_class!r})'


class Division(BaseSQLModel):
    __tablename__ = 'divisions'

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(3))
    name: Mapped[str]
    comments: Mapped[Optional[str]]

    nodes = relationship('Node')

    def __repr__(self) -> str:
        return f'Division(id={self.id!r}, code={self.code!r}, ' \
            + f'name={self.name!r})'


class GeneticCode(BaseSQLModel):
    __tablename__ = 'genetic_codes'

    id: Mapped[int] = mapped_column(primary_key=True)
    # abbreviation: Mapped[Optional[str]]
    name: Mapped[str]
    translation_table: Mapped[str] = mapped_column(String(64))
    start_stop: Mapped[str] = mapped_column(String(64))

    def __repr__(self) -> str:
        return f'GeneticCode(id={self.id!r}, name={self.name!r})'


class DeletedNode(BaseSQLModel):
    __tablename__ = 'deleted_nodes'

    tax_id: Mapped[int] = mapped_column(primary_key=True)

    def __repr__(self) -> str:
        return f'DeletedNode(tax_id={self.tax_id!r})'


class MergedNode(BaseSQLModel):
    __tablename__ = 'merged_nodes'

    old_tax_id: Mapped[int] = mapped_column(primary_key=True)
    new_tax_id: Mapped[int] = mapped_column(ForeignKey('nodes.tax_id'))

    def __repr__(self) -> str:
        return f'MergedNode(old_tax_id={self.old_tax_id!r}, ' \
            + f'new_tax_id={self.new_tax_id!r})'


class Citation(BaseSQLModel):
    __tablename__ = 'citations'

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[Optional[str]]
    # pubmed_id: Mapped[Optional[str]]
    medline_id: Mapped[Optional[str]]
    url: Mapped[Optional[str]]
    text: Mapped[Optional[str]]

    nodes: Mapped[List[Node]] = relationship(
        secondary=assoc_table_nodes_citations,
        back_populates='citations')

    def __repr__(self) -> str:
        return f'Citation(id={self.id!r}, key={self.key!r})'


class Image(BaseSQLModel):
    __tablename__ = 'images'

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str]
    url: Mapped[str]
    license: Mapped[str]
    attribution: Mapped[Optional[str]]
    source: Mapped[str]
    # properties: Mapped[Optional[str]]

    nodes: Mapped[List[Node]] = relationship(
        secondary=assoc_table_nodes_images,
        back_populates='images')

    def __repr__(self) -> str:
        return f'Image(id={self.id!r}, key={self.key!r})'


class Codon(BaseSQLModel):
    __tablename__ = 'codons'

    id: Mapped[int] = mapped_column(primary_key=True)
    codon: Mapped[str] = mapped_column(String(3))

    def __repr__(self) -> str:
        return f'Codon(id={self.id!r}, codon={self.codon!r})'
