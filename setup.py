#!/usr/bin/env python

from setuptools import setup

sctk = {
    "name": "bones",
    "description": "A python toolkit for biology",
    "author":"Giles Hall",
    "author_email": "giles@polymerase.org",
    "keywords": ["biology", "bioinformatics", "genomics", "sequencing"],
    "packages": ["bones"],
    "package_dir": {"bones": "src"},
    "install_requires": [
        "pysam", 
        "requests", 
    ],
    "version": "0.1",
}

if __name__ == "__main__":
    setup(**sctk)
