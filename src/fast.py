# XXX: move to io module
from . sequence import Sequence
from cStringIO import StringIO

__all__ = ["FastSequenceList", "FastA"]

class FastSequenceList(list):
    pass

class FastA(FastSequenceList):
    def _iter_load(self, iterable):
        seq = name = ''
        for line in iterable:
            if line[0] == '>':
                if seq != '' and name != '':
                    _seq = Sequence(seq, name=name)
                    self.append(_seq)
                    seq = ''
                name = line[1:].strip()
            else:
                seq += line.strip()
        # check for left over sequence
        if seq != '' and name != '':
            _seq = Sequence(seq, name=name)
            self.append(_seq)

    def to_string(self):
        for seq in self:
            name = getattr(seq, "name", "")
            yield ">%s\n" % name
            yield "%s\n" % seq

    def from_string(self, fastr):
        buf = cStringIO(fastr)
        self._iter_load(buf)

    @classmethod
    def load(cls, fafn):
        fa = FastA()
        with open(fafn) as fafh:
            fa._iter_load(fafh)
        return fa

    def save(self, fafn):
        with open(fafn, 'w') as fa:
            for line in self.to_string():
                fa.write(line)
