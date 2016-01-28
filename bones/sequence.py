# XXX: transition to unicode
import random
import math

__all__ = ["Sequence", "ComplimentTable", "random_sequence"]

def build_compliment_table():
    cmap = ((ord('G'), ord('C')), (ord('A'), ord('T')))
    _ctable = [chr(idx) for idx in xrange(0xff + 1)]
    case_delta = ord('a') - ord('A')
    for (base1, base2) in cmap:
        _ctable[base1] = chr(base2)
        _ctable[base2] = chr(base1)
        _ctable[base1 + case_delta] = chr(base2 + case_delta)
        _ctable[base2 + case_delta] = chr(base1 + case_delta)
    return str.join('', _ctable)
ComplimentTable = build_compliment_table()

class Sequence(str):
    def __new__(cls, sequence, name='', **kw):
        obj = super(Sequence, cls).__new__(cls, sequence)
        obj.name = name
        return obj

    def __getitem__(self, idx):
        subseq = super(Sequence, self).__getitem__(idx)
        return self.copy(subseq)

    def __getslice__(self, *args):
        subseq = super(Sequence, self).__getslice__(*args)
        return self.copy(subseq)

    def window(self, window_size):
        sz = min(len(self), window_size)
        return (self[x:x + sz] for x in xrange(len(self) - sz + 1))

    def copy(self, sequence=None, **kw):
        ns = self.__dict__.copy()
        ns.update(kw)
        sequence = sequence if sequence != None else str(self)
        return self.__class__(sequence, **ns)

    def gc_window(self, window_size=10):
        return (seq.gc_content for seq in self.window(window_size))

    @property
    def reverse(self):
        return self.copy(self[::-1])

    @property
    def compliment(self):
        return self.copy(self.translate(ComplimentTable))

    @property
    def reverse_compliment(self):
        return self.reverse.compliment
    rc = revcomp = reverse_compliment

    @property
    def gc_count(self):
        seq = super(Sequence, self).upper()
        return seq.count('G') + seq.count('C')

    @property
    def at_count(self):
        return len(self) - self.gc_count

    @property
    def gc_content(self):
        return self.gc_count / float(len(self))

    @property
    def at_content(self):
        return self.at_count / float(len(self))

    @property
    def is_palindrome(self):
        if len(self) & 0x1:
            # sequences of odd length can't be palindromes
            return False
        return self == self.rc

def random_sequence(length, name=None, gc_median=0.5, gc_spread=0.1):
    gc_low = int(math.ceil(max(0, gc_median - gc_spread) * length))
    gc_high = int(math.floor(min(1, gc_median + gc_spread) * length))
    gc_count = random.randint(gc_low, gc_high)
    gc_seq = [random.choice("GC") for idx in xrange(gc_count)]
    at_seq = [random.choice("AT") for idx in xrange(length - gc_count)]
    seq = gc_seq + at_seq
    random.shuffle(seq)
    seq = str.join('', seq)
    name = name if name != None else "random_sequence"
    return Sequence(seq, name=name)
