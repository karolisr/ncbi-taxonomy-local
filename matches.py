#!/usr/bin/env python3
from ncbi_taxonomy_local import Tax
tax = Tax(backend="SQLite", check_for_updates=False)
taxids = tax.taxids_for_name('Tomato')
print(taxids)
