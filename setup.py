from __future__ import absolute_import

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='module_loader',
    author='Mitchell Olsthoorn',
    description='IPv8 module loader',
    long_description=long_description,
    long_description_content_type='text/markdown',
    version='0.1.0',
    url='https://github.com/mitchellolsthoorn/ipv8-module-loader',
    package_data={'module_loader': ['*.*']},
    packages=find_packages(),
    install_requires=[
        "pyipv8",
        "service_identity",
        "yappi",
        "six"
    ]
)
