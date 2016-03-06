# XXX: transition to unicode
import random
import math
import copy

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

class SequenceInfo(dict):
    Defaults = {
        "name": "",
        "strand": 1,
    }

    def __init__(self, info=None, **kw):
        if info == None:
            info = {}
        if not isinstance(info, dict):
            raise TypeError("info must be a dictionary, not %s" % type(info))
        super(SequenceInfo, self).__init__(self.Defaults)
        self.update(info)
        self.update(kw)

    def copy(self):
        return self.__class__(self)

    def update(self, info):
        for (key, val) in info.items():
            self[key] = val

    def __getitem__(self, key):
        if key == "features":
            return self.features
        return super(SequenceInfo, self).__getitem__(key)

    def __setitem__(self, key, val):
        if key == "features":
            self.features = val
            return
        super(SequenceInfo, self).__setitem__(key, val)

    def get_features(self):
        return self.get("features", {})

    def set_features(self, features):
        if type(features) != dict:
            raise TypeError("features must be a dictionary, not %s" % type(features))
        self["features"] = {key: SequenceFeature(val) for (key, val) in features.items()}

class SequenceFeature(dict):
    Defaults = {
        "name": "",
        "strand": 1,
        "region": (0, 0),
    }

    def __init__(self, feature, **kw):
        if not isinstance(feature, dict):
            raise TypeError("feature must be a dictionary")
        super(SequenceFeature, self).__init__(self.Defaults)
        self.update(feature)
        self.update(kw)

    def copy(self):
        return self.__class__(self)

class Sequence(str):
    def __new__(cls, sequence, **kw):
        obj = super(Sequence, cls).__new__(cls, sequence)
        return obj
    
    def __init__(self, *args, **kw):
        self.info = kw

    def get_info(self):
        return self._info
    
    def set_info(self, info):
        if info == None:
            info = {}
        if not isinstance(info, SequenceInfo):
            info = SequenceInfo(info)
        self._info = info
    info = property(get_info, set_info)

    def get_features(self):
        return self.info.features

    def set_features(self, features):
        self.info.features = features
    features = property(get_features, set_features)

    def get_name(self):
        return self.info.get("name", "")

    def set_name(self, name):
        self.info["name"] = name
    name = property(get_name, set_name)

    def get_strand(self):
        return self.info.get("strand", 1)

    def set_strand(self, strand):
        self.info["strand"] = strand
    strand = property(get_strand, set_strand)

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
        sequence = sequence if sequence != None else str(self)
        info = self.info.copy()
        info.update(kw)
        return self.__class__(sequence, **info)

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
        seq = str(self)[::-1].translate(ComplimentTable)
        return self.copy(seq, strand=-(self.strand))
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
