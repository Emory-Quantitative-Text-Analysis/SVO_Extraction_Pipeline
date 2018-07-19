# coding: utf-8

from setuptools import setup, find_packages

with open('README.md')as f:
    readme = f.read()

with open('LICENSE') as f:
    _license = f.read()

setup(
    name='SVO_Automation',
    version='0.0.1',
    description='Python package for SVO automation',
    long_description=readme,
    author='Gabriel Wang',
    author_email='gabrielwry@gmail.com',
    url='',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)