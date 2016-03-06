#!/usr/bin/env python

import unittest
import tempfile
import shutil
import os
import json
from bones.sequence import *
from bones.fast import *

FA_TEST = \
""">seq1
AGTC
>seq2 {"name": "seq2", "strand": -1}
AGTCAGTC
"""

class TestFastA(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.fasta_paths = {
            "one": os.path.join(self.tempdir, "one.fa")
        }
        with open(self.fasta_paths["one"], 'w') as fa:
            fa.write(FA_TEST)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_load(self):
        fa = FastA.load(self.fasta_paths["one"])
        self.assertEquals(len(fa), 2)
        self.assertEquals(fa[0], "AGTC")
        self.assertEquals(fa[0].__class__, Sequence)
        self.assertEquals(fa[1], "AGTCAGTC")
        self.assertEquals(fa[1].strand, -1)

    def test_save_strict(self):
        fa = FastA()
        seq = Sequence("AGTC", name="seq1")
        fa.append(seq)
        fafn = os.path.join(self.tempdir, "test.fa")
        fa.save(fafn, strict=True)
        with open(fafn) as fa:
            line = fa.readline().strip()
            self.assertEquals(">seq1", line)
            line = fa.readline().strip()
            self.assertEquals("AGTC", line)

    def test_save(self):
        fa = FastA()
        seq = Sequence("AGTC", name="seq1")
        fa.append(seq)
        fafn = os.path.join(self.tempdir, "test.fa")
        fa.save(fafn)
        with open(fafn) as fa:
            line = fa.readline().strip()
            tokens = line.split(" ")
            self.assertEquals(">seq1", tokens[0])
            info = json.loads(str.join(' ', tokens[1:]))
            self.assertEquals(info, seq.info)
            line = fa.readline().strip()
            self.assertEquals("AGTC", line)

if __name__ == '__main__':
    unittest.main()
