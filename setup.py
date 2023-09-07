import setuptools

from ncbi_taxonomy_local import __author__
from ncbi_taxonomy_local import __author_email__
from ncbi_taxonomy_local import __description__
from ncbi_taxonomy_local import __url__
from ncbi_taxonomy_local import __version__

with open('README.md', 'r') as f:
    long_description = f.read()

setuptools.setup(
    name='ncbi-taxonomy-local',
    version=__version__,
    author=__author__,
    author_email=__author_email__,
    description=__description__,
    long_description=long_description,
    long_description_content_type='text/markdown',
    url=__url__,
    packages=setuptools.find_packages(),
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Scientific/Engineering :: Bio-Informatics'
    ],
)
