# ncbi-taxonomy-local [![Build Status](https://app.travis-ci.com/karolisr/ncbi-taxonomy-local.svg?branch=master)](https://app.travis-ci.com/karolisr/ncbi-taxonomy-local)
Locally-cached NCBI Taxonomy Database for Python 3

Installation:

```bash
pip3 install --upgrade git+https://github.com/karolisr/ncbi-taxonomy-local
```

Initialization:

```python
from ncbi_taxonomy_local import Tax
```

```python
# Use the SQLite backend:
#   - Slightly slower queries
#   - Instant loading time
#   - Lower RAM usage
tax = Tax()
# or
tax = Tax(backend='SQLite')
```

```python
# Load entire database into RAM.
#   - Faster queries
#   - Slower loading time
#   - Higher RAM usage
tax = Tax(backend='RAM')
```

Usage Examples:

```python
tax.taxids_for_name('Solanum')
tax.taxids_for_name('Solanum chilense')
tax.names_for_taxid(3701)
tax.names_for_taxid(3702)
tax.lineage_of_taxids(3701)
tax.common_name_for_taxid(3702)
tax.taxids_for_name('Homo')
tax.taxids_for_name('ape')
tax.scientific_name_for_taxid(9606)
tax.scientific_name_for_taxid(9600)
tax.common_name_for_taxid(9600)
tax.common_name_for_taxid(314295)
```
