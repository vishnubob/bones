#!/usr/bin/env python

import unittest
import os
import tempfile
import shutil

from bones import *
from bones.sequence import random_sequence
from bones.utils import temp_filename
from bones.fast import FastA

class TestConsensus(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.fafn = os.path.join(self.tempdir, "references.fafn")
        self.r1fn = os.path.join(self.tempdir, "reads_1.fq")
        self.r2fn = os.path.join(self.tempdir, "reads_2.fq")
        self.samfile = os.path.join(self.tempdir, "alignment.sam")
        self.fake_reference("fakeref", [1000, 5000, 10000])
        self.fake_reads()
        self.align_reads()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def align_reads(self):
        index = bwa.Index(reference=self.fafn)
        index().wait()
        fh = open(self.samfile, 'w')
        align = bwa.Align(prefix=self.fafn, reads=self.r1fn, mates=self.r2fn)
        align(stdout=fh).wait()

    def fake_reference(self, name, length_list):
        self.references = {}
        for (idx, length) in enumerate(length_list):
            _name = "%s_%d" % (name, idx + 1)
            self.references[_name] = random_sequence(length, name=_name)
        fa = FastA(self.references.values())
        fa.save(self.fafn)

    def fake_reads(self):
        cmd = "wgsim -N 100000 -h %s %s %s" % (self.fafn, self.r1fn, self.r2fn)
        ret = os.system(cmd)

    def test_consensus(self):
        con = consensus.Consensus()
        samf = samfile.Samfile(self.samfile)
        for seq in con.call_samfile(samf.samf):
            self.assertTrue(self.references[seq.name], seq)

if __name__ == '__main__':
    unittest.main()
