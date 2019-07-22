import setuptools  # noqa

with open('README.md', 'r') as f:
    long_description = f.read()

description = 'Locally-cached NCBI Taxonomy Database for Python'

setuptools.setup(
    name='ncbi-taxonomy-local',
    version='0.0.1',
    author='Karolis Ramanauskas',
    author_email='kraman2@uic.edu',
    description=description,
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/karolisr/ncbi-taxonomy-local',
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: cc-by-sa-4.0',
        'Operating System :: OS Independent',
    ],
)
