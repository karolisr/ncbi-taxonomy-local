# ncbi-taxonomy-local [![Build Status](https://app.travis-ci.com/karolisr/ncbi-taxonomy-local.svg?branch=master)](https://app.travis-ci.com/karolisr/ncbi-taxonomy-local)
Locally-cached NCBI Taxonomy Database for Python 3

Installation:

```bash
pip3 install --user --upgrade git+https://github.com/karolisr/ncbi-taxonomy-local
```

or:

```bash
pip3 install --upgrade git+https://github.com/karolisr/ncbi-taxonomy-local
```

Initialization:

```python
from ncbi_taxonomy_local import Taxonomy
```

```python
# Use the SQLite backend:
#   - Slightly slower queries
#   - Instant loading time
#   - Lower RAM usage
tax = Taxonomy()
# or
tax = Taxonomy(backend='SQL')
```

```python
# Load entire database into RAM.
#   - Faster queries
#   - Slower loading time
#   - Higher RAM usage
tax = Taxonomy(backend='RAM')
```

Usage Examples:

```python
tax.taxids_for_name('Solanum')
tax.taxids_for_name('Solanum chilense')
tax.names_for_taxid(3701)
tax.names_for_taxid(3702)
tax.lineage_for_taxid(3701)
tax.common_name_for_taxid(3702)
tax.taxids_for_name('Homo')
tax.taxids_for_name('ape')
tax.scientific_name_for_taxid(9606)
tax.scientific_name_for_taxid(9600)
tax.common_name_for_taxid(9600)
tax.common_name_for_taxid(314295)
```
