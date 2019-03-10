from __future__ import absolute_import

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='loader',
    author='Mitchell Olsthoorn',
    description='IPv8 dApp loader',
    long_description=long_description,
    long_description_content_type='text/markdown',
    version='0.1.0',
    url='https://github.com/mitchellolsthoorn/ipv8-dapps-loader',
    package_data={'loader': ['*.*']},
    packages=find_packages(),
    install_requires=[
        "pyipv8",
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Twisted",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Distributed Computing",
        "Topic :: System :: Networking"
    ]
)
