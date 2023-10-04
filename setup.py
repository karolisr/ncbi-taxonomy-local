from setuptools import setup
from setuptools import find_packages

from datetime import datetime

date_time = datetime.now()
y = str(date_time.year)

__version__ = '1.0.0'
__author__ = 'Karolis Ramanauskas'
__author_email__ = 'kraman2@uic.edu'
__description__ = 'Locally-cached NCBI Taxonomy Database for Python 3.'
__copyright__ = 'Copyright \u00A9 ' + __author__ + ', ' + y
__license__ = 'Creative Commons Attribution-ShareAlike 4.0 International ' \
              'License: cc-by-sa-4.0'
__url__ = 'https://github.com/karolisr/ncbi-taxonomy-local'

with open('README.md', 'r') as f:
    long_description = f.read()

with open('requirements.txt', 'r') as f:
    reqs = f.read()

reqs = reqs.splitlines()

setup(
    name='ncbi-taxonomy-local',
    version=__version__,
    author=__author__,
    author_email=__author_email__,
    description=__description__,
    long_description=long_description,
    long_description_content_type='text/markdown',
    url=__url__,
    install_requires=reqs,
    packages=find_packages(),
    python_requires='>=3.9',
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
