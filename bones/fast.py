# XXX: move to io module
import re
import json
from . sequence import Sequence
from cStringIO import StringIO

__all__ = ["FastSequenceList", "FastA"]

class ParseError(Exception):
    pass

class FastSequenceList(list):
    pass

class FastA(FastSequenceList):
    re_infoname = re.compile("^>\s*(?P<name>[^{]*?)\s*(?P<info>{.+})\s*$")

    def _iter_load(self, iterable):
        seq = ''
        kw = None
        for line in iterable:
            if line[0] == '>':
                if seq != '':
                    _seq = Sequence(seq, **kw)
                    self.append(_seq)
                    seq = ''
                    kw = None
                m = self.re_infoname.match(line)
                if m:
                    infoname = m.groupdict()
                    kw = json.loads(infoname["info"])
                    if "name" not in kw:
                        kw["name"] = infoname.get("name", "").strip()
                else:
                    kw = {"name": line[1:].strip()}
            else:
                if kw == None:
                    raise ParseError("Sequence specified without name")
                seq += line.strip()
        # check for left over sequence
        if seq != '':
            _seq = Sequence(seq, **kw)
            self.append(_seq)

    def to_string(self, strict=False):
        for seq in self:
            name = getattr(seq, "name", "")
            info = getattr(seq, "info", None)
            if info != None and not strict:
                yield ">%s %s\n" % (name, json.dumps(info))
            else:
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

    def save(self, fafn, strict=False):
        with open(fafn, 'w') as fa:
            for line in self.to_string(strict=strict):
                fa.write(line)
