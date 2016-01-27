import pysam
import sys
import collections
import operator
import sequence

class Consensus(object):
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
            position = pileup_column.pos
            coverage = pileup_column.n
            base_count = self.process_pileup_column(pileup_column)
            yield (position, coverage, base_count)

    def call_pileup_column(self, position, coverage, base_count):
        # XXX: this is currently as dumn as a box of rocks
        #unique = sum(base_count.values()) / float(cov) * 100
        #info = str.join(', ', map(str, ["%.06f%%" % unique, pos, cov, base_count, call_base(base_count)])) + '\n'
        #sys.stderr.write(info)
        hist = base_count.items()
        hist.sort(key=operator.itemgetter(1))
        winner = hist[-1][0]
        if winner == "del":
            return ''
        if winner == "refskip":
            return ''
        return winner

    def call_pileup(self, pileup):
        seq = ''
        for pileup_column in self.process_pileup(pileup):
            pileup_column_call = self.call_pileup_column(*pileup_column)
            seq += pileup_column_call
        return seq

    def call_samfile(self, samf):
        for reference in samf.references:
            pileup = samf.pileup(reference=reference)
            seq = self.call_pileup(pileup)
            yield sequence.Sequence(seq, name=reference)
