# XXX: transition to unicode

__all__ = ["Sequence", "ComplimentTable"]

def build_compliment_table():
    cmap = (('g', 'c'), ('a', 't'))
    _ctable = [chr(idx) for idx in xrange(0xff + 1)]
    for (base1, base2) in cmap:
        for casef in (str.lower, str.upper):
            base1 = casef(base1)
            base2 = casef(base2)
            base1_val = ord(base1)
            base2_val = ord(base2)
            _ctable[base1_val] = base2
            _ctable[base2_val] = base1
    return str.join('', _ctable)

ComplimentTable = build_compliment_table()

class Sequence(str):
    def __new__(cls, sequence, name='', **kw):
        obj = super(Sequence, cls).__new__(cls, sequence)
        obj.name = name
        return obj

    def kmerize(self, klen):
        kmer_count = len(self) - klen + 1
        for offset in xrange(kmer_count):
            kmer = self[offset:offset+klen]
            _name = self.name + " K%d.%d" % (klen, offset)
            yield self.__class__(kmer, name=_name)

    def reverse(self):
        return self.__class__(self[::-1], name=self.name)

    def compliment(self):
        return self.__class__(self.translate(ComplimentTable), name=self.name)

    def reverse_compliment(self):
        return self.reverse().compliment()
    revcomp = reverse_compliment
