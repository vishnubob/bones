import pysam
import sys
import collections
import operator
import sequence
from . samfile import Samfile

class Consensus(object):
    def __init__(self, read_coverage_threshold=10):
        self.read_coverage_threshold = read_coverage_threshold

    def process_pileup_column(self, pileup_column):
        base_count = collections.defaultdict(int)
        for pileup_read in pileup_column.pileups:
            if self.filter_pileup_read(pileup_read):
                continue
            alignment = pileup_read.alignment
            if pileup_read.is_del or pileup_read.is_refskip:
                base = ''
                base_quality = -1
            else:
                base_quality = alignment.query_qualities[pileup_read.query_position]
                start_pos = pileup_read.query_position
                end_pos = pileup_read.query_position + max(0, pileup_read.indel) + 1
                base = alignment.query_sequence[start_pos:end_pos]
            base_count[base] += 1
        return dict(base_count)

    def filter_pileup_read(self, pileup_read):
        if pileup_read.alignment.mapq < 20:
            return True
        if pileup_read.alignment.is_qcfail:
            return True

    def process_pileup(self, pileup):
        for pileup_column in pileup:
            base_count = self.process_pileup_column(pileup_column)
            position = pileup_column.pos
            coverage = pileup_column.n
            if self.coverage["max_coverage"] == None:
                self.coverage["max_coverage"] = self.coverage["min_coverage"] = coverage
            self.coverage["max_coverage"] = max(self.coverage["max_coverage"], coverage)
            self.coverage["min_coverage"] = min(self.coverage["min_coverage"], coverage)
            self.coverage["avg_coverage"] += coverage
            self.coverage["column_count"] += 1
            yield (position, coverage, base_count)

    def call_pileup_column(self, position, coverage, base_count):
        # XXX: this is currently as dumn as a box of rocks
        #unique = sum(base_count.values()) / float(cov) * 100
        #info = str.join(', ', map(str, ["%.06f%%" % unique, pos, cov, base_count, call_base(base_count)])) + '\n'
        #sys.stderr.write(info)
        hist = base_count.items()
        if len(hist) == 0:
            # XXX: is this right?
            return ('', "NC")
        if coverage < self.read_coverage_threshold:
            return ('', "LC")
        hist.sort(key=operator.itemgetter(1))
        winner = hist[-1][0]
        if winner == "del":
            return ('', "DL")
        if winner == "refskip":
            return ('', "RS")
        return (winner, "CL")

    def call_pileup(self, pileup):
        seq = ''
        for pileup_column in self.process_pileup(pileup):
            (pileup_column_call, call_type) = self.call_pileup_column(*pileup_column)
            self.call_type_hist[call_type] += 1
            seq += pileup_column_call
        return seq

    def call_samfile(self, samf):
        if type(samf) in (str, unicode):
            samf = Samfile(samf)
        for reference in samf.references:
            # stats
            self.coverage = {"max_coverage": None, "min_coverage": None, "avg_coverage": 0, "column_count": 0}
            self.call_type_hist = collections.defaultdict(int)
            #
            pileup = samf.pileup(reference=reference)
            seq = self.call_pileup(pileup)
            name = "%s_consensus" % reference
            if self.coverage["column_count"]:
                self.coverage["avg_coverage"] = self.coverage["avg_coverage"] / float(self.coverage["column_count"])
            yield sequence.Sequence(seq, name=name)
