#!/usr/bin/env python

import unittest
from bones.sequence import Sequence

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

if __name__ == '__main__':
    unittest.main()
