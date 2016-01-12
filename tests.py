#!/usr/bin/env python

import os
import unittest
import time
from worf.utils import *
from worf.sequence import Sequence

class TestSequence(unittest.TestCase):
    def test_revcomp(self):
        testseq = "aGTGCGATGTGCGATGAGATCg"
        answer = "cGATCTCATCGCACATCGCACt"
        seq = Sequence(testseq)
        revcomp_seq = seq.revcomp()
        self.assertEquals(answer, revcomp_seq)
        self.assertEquals(seq.name, revcomp_seq.name)

    def test_kmer(self):
        testseq = "AGTGCGATGT"
        answer = ["AGTG", "GTGC", "TGCG", "GCGA", "CGAT", "GATG", "ATGT"]
        seq = Sequence(testseq)
        kmers = list(seq.kmerize(4))
        self.assertEquals(len(answer), len(kmers))
        for (test_kmer, ans_kmer) in zip(kmers, answer):
            self.assertEquals(test_kmer, ans_kmer)

class TestUtils(unittest.TestCase):
    def test_temp_filename_collision(self):
        fn1 = temp_filename()
        fn2 = temp_filename()
        self.assertNotEqual(fn1, fn2)

    def test_temp_filename_kwargs(self):
        fn = temp_filename(prefix="temp_")
        self.assertTrue(fn.startswith("temp_"))
        fn = temp_filename(postfix="_temp")
        self.assertTrue(fn.endswith("_temp"))
        fn = temp_filename(ext="dat")
        self.assertTrue(fn.endswith(".dat"))
        fn = temp_filename(prefix="/usr/local/", postfix="_temp", ext="dat")
        self.assertTrue(fn.startswith("/usr/local/"))
        self.assertTrue(fn.endswith("_temp.dat"))

    def test_is_stale(self):
        younger_fn = temp_filename(prefix="/tmp/")
        older_fn = temp_filename(prefix="/tmp/")
        ts = time.time()
        touch(older_fn, mtime=ts)
        touch(younger_fn, mtime=ts - 100)
        try:
            self.assertFalse(is_stale(younger_fn, older_fn))
            self.assertTrue(is_stale(older_fn, younger_fn))
        finally:
            os.unlink(younger_fn)
            os.unlink(older_fn)
    
    def test_common_filename(self):
        fn1 = "/this/is/common/filename_elephant"
        fn2 = "/this/is/common/filename_rhino"
        fn3 = "/this/is/common/filename_cat"
        cfn = common_filename(fn1, fn2, fn3)
        self.assertEquals(cfn, "/this/is/common/filename_")
        # nothing similar
        fn4 = "not like the others"
        cfn = common_filename(fn1, fn2, fn3, fn4)
        self.assertEquals(cfn, "")
        # short match
        fn5 = "/this/is/common/filename_"
        cfn = common_filename(fn1, fn2, fn3, fn5)
        self.assertEquals(cfn, "/this/is/common/filename_")

if __name__ == '__main__':
    unittest.main()


