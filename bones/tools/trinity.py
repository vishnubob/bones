import os
import operator
import subprocess
import multiprocessing

from .. utils import *
from .. process import *
from .. task import *
from .. package import *

__all__ = ["Index", "Align"]

class Trinity(Process):
    pass

class TrinityTask(BoneTask):
    Directories = ["denovo"]
    TaskName = "trinity"

    def _init(self):
        self.reads = [symlink(fn, self.dir_reads) for fn in self.reads]

    def _run(self, *args, **kw):
        cmdkw = {
            "reads": self.reads[0],
        }
        if len(self.reads) > 1:
            cmdkw["mates"] = self.reads[1]
        cmdkw.update(kw)
        align = bwa.Align(**cmdkw)
        with open(self.fn_alignment, 'w') as fh:
            align.run(stdout=fh, wait=True)

class PackageTrinity(Package):
    PackageName = "trinity"
    Depends = {
        "dpkg": ["git", "build-essential", "zlib1g-dev", "libncurses5-dev"],
    }
    Version = "v2.2.0"

    def script(self):
        script = [
            "git clone -b ${PKG_VERSION} https://github.com/trinityrnaseq/trinityrnaseq.git ${PKG_SRCDIR}/trinity",
            "cd ${PKG_SRCDIR}/trinity",
            "make",
        ]
        return script
