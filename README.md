# ncbi-taxonomy-local [![Build Status](https://app.travis-ci.com/karolisr/ncbi-taxonomy-local.svg?branch=master)](https://app.travis-ci.com/karolisr/ncbi-taxonomy-local)
Locally-cached NCBI Taxonomy Database for Python 3

Installation:

```bash
pip3 install --upgrade git+https://github.com/karolisr/ncbi-taxonomy-local
```

In case this fails you may try:

```bash
sudo -H pip3 install --upgrade git+https://github.com/karolisr/ncbi-taxonomy-local
```

or:

```bash
pip3 install --user --upgrade git+https://github.com/karolisr/ncbi-taxonomy-local
```

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
