# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='publishtimer',
    version='1.0',
    description='Service for computing publish-time-recommendations',
    long_description=readme,
    author='Parag Guruji',
    author_email='paragguruji@gmail.com',
    url='https://github.com/Codigami/publishtimer',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)
