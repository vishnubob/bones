#!/usr/bin/env python

import unittest
from bones.sequence import *

class TestSequence(unittest.TestCase):
    def test_revcomp(self):
        testseq = "aGTGCGATGTGCGATGAGATCg"
        answer = "cGATCTCATCGCACATCGCACt"
        seq = Sequence(testseq)
        revcomp_seq = seq.rc
        self.assertEquals(answer, revcomp_seq)
        self.assertEquals(seq.name, revcomp_seq.name)
        self.assertEquals(seq.strand, 1)
        self.assertEquals(revcomp_seq.strand, -1)

    def test_window(self):
        testseq = "AGTGCGATGT"
        answer = ["AGTG", "GTGC", "TGCG", "GCGA", "CGAT", "GATG", "ATGT"]
        seq = Sequence(testseq)
        kmers = list(seq.window(4))
        self.assertEquals(len(answer), len(kmers))
        for (test_kmer, ans_kmer) in zip(kmers, answer):
            self.assertEquals(test_kmer, ans_kmer)
        kmers = list(seq.window(len(seq) + 1))
        self.assertEquals(1, len(kmers))
        kmers = list(seq.window(len(seq)))
        self.assertEquals(1, len(kmers))
        kmers = list(seq.window(len(seq) - 1))
        self.assertEquals(2, len(kmers))

    def test_random_sequence(self):
        seq = random_sequence(50, gc_median=0.5, gc_spread=0, name="split")
        self.assertEquals(seq.name, "split")
        self.assertEquals(seq.gc_count, 25)
        self.assertEquals(seq.at_count, 25)

    def test_counts(self):
        testseq = "GcgCAtAt"
        seq = Sequence(testseq)
        self.assertEquals(seq.gc_count, 4)
        self.assertEquals(seq.at_count, 4)
        self.assertEquals(seq.gc_content, 0.5)

    def test_slice(self):
        testseq = "GCAT"
        seq = Sequence(testseq)
        subseq = seq[:2]
        self.assertTrue(isinstance(seq, Sequence))

    def test_gc_window(self):
        testseq = "GGGGAGAGTTTT"
        answer = [1, .75, .75, .5, .5, .5, .25, .25, 0]
        seq = Sequence(testseq)
        gc_content = seq.gc_window(4)
        self.assertEquals(list(gc_content), answer)

if __name__ == '__main__':
    unittest.main()
