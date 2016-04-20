#!/usr/bin/env python

from setuptools import setup

sctk = {
    "name": "bones",
    "description": "A python toolkit for biology",
    "author":"Giles Hall",
    "author_email": "giles@polymerase.org",
    "keywords": ["biology", "bioinformatics", "genomics", "sequencing"],
    "packages": ["bones"],
    "version": "0.1",
    "install_requires": [
        "pysam",
        "requests",
        "ssw"
    ],
    "dependency_links": [
        "git+git://github.com/vishnubob/ssw.git#egg=ssw-0.3.1",
    ]
}

if __name__ == "__main__":
    setup(**sctk)
