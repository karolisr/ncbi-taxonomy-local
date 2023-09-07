#!/usr/bin/env python3

"""Rudimentary Testing"""

from pprint import pprint

from ncbi_taxonomy_local import TaxonomyRAM
tax = TaxonomyRAM()
tax.init(data_dir='NCBI_TAXONOMY')

pprint(tax.taxids_for_name('Solanum'))
pprint(tax.taxids_for_name('Solanum chilense'))
pprint(tax.names_for_taxid(3701))
pprint(tax.names_for_taxid(3702))
pprint(tax.lineage_for_taxid(3701))
pprint(tax.common_name_for_taxid(3702))
pprint(tax.taxids_for_name('Homo'))
pprint(tax.taxids_for_name('ape'))
pprint(tax.scientific_name_for_taxid(9606))
pprint(tax.scientific_name_for_taxid(9600))
pprint(tax.common_name_for_taxid(9600))
pprint(tax.common_name_for_taxid(314295))
