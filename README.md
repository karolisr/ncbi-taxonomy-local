# ncbi-taxonomy-local [![Build Status](https://travis-ci.com/karolisr/ncbi-taxonomy-local.svg?branch=master)](https://travis-ci.com/karolisr/ncbi-taxonomy-local)
Locally-cached NCBI Taxonomy Database for Python

Initialization:

```python
from ncbi_taxonomy_local import taxonomy
T = taxonomy('~/NCBI_TAXONOMY_DB')
```

Usage Examples:

```python
T.taxids_for_name('Solanum')
T.taxids_for_name('Solanum chilense')
T.names_for_taxid(3701)
T.names_for_taxid(3702)
T.lineage_for_taxid(3701)
```
