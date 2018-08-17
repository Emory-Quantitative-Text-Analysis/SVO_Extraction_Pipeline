# coding: utf-8

from setuptools import setup, find_packages

with open('README.md')as f:
    readme = f.read()

with open('LICENSE') as f:
    _license = f.read()

setup(
    name='svo_automatin',
    version='0.0.1',
    description='Python package for SVO automation',
    long_description=readme,
    author='Gabriel Wang',
    author_email='gabrielwry@gmail.com',
    url='https://github.com/gabrielwry/SVO_Extraction_Pipeline.git',
    license=license,
    python_requires = '>=3.6.0',
    packages=find_packages(include='logging_config.ini',exclude=('tests', 'docs')),
    install_requires =
    "nltk==3.3 \
    numpy==1.14.5 \
    pandas==0.23.3 \
    spacy==2.0.11 \
    stanfordcorenlp==3.9.1.1"
)