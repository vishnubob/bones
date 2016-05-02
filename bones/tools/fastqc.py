import os
from .. process import *
from .. task import *
from .. package import *

__all__ = ["FastQC"]

class FastQC(Process):
    Command = "fastqc"
    Arguments = [
        ProcessArgument(name="outdir", argument="-o", type=str, required=True, help="Output directory"),
        ProcessArgument(name="seqfiles", required=True, type=list, help="One or more sequence files to process"),
    ]

class FastQCTask(BoneTask):
    TaskName = "fastqc"
    Directories = ["QC"]

    def _run(self, *args, **kw):
        """
        qc_glob = os.path.join(self.dir_qc, "*")
        stale_flag = is_stale(self.reads, qc_glob)
        if self.mates:
            stale_flag |= is_stale(self.mates, qc_glob)
        if not stale_flag:
            return
        """
        reads = [self.reads]
        if self.mates:
            reads.append(self.mates)
        cmdkw = {
            "outdir": self.dir_qc,
            "seqfiles": reads,
        }
        cmdkw.update(kw)
        qc = FastQC(**cmdkw)
        qc.run(wait=True)


class PackageFastQC(Package):
    PackageName = "fastqc"
    Depends = {
        "dpkg": ["git", "build-essential", "wget", "unzip"],
        "pip": []
    }
    Version = "v0.11.5"

    def script(self):
        script = [
            "cd ${PKG_SRCDIR}",
            "wget http://www.bioinformatics.babraham.ac.uk/projects/fastqc/fastqc_${PKG_VERSION}.zip",
            "unzip fastqc_${PKG_VERSION}.zip",
            "chmod 755 FastQC/fastqc",
            "mv FastQC ${PKG_SHAREDIR}",
            "ln -s ${PKG_SHAREDIR}/FastQC/fastqc ${PKG_BINDIR}/fastqc",
        ]
        return script

