import os
from . process import Process

__all__ = ["FastQC"]

class FastQC(Process):
    Command = "fastqc"
    Arguments = {
        "input": None,
        "outdir": "-o"
    }

    def __call__(self, **kw):
        _kw = self.arguments(**kw)
        outdir = _kw["-o"]
        if not os.path.isdir(outdir):
            os.makedirs(outdir)
        return super(FastQC, self).__call__(**kw)
