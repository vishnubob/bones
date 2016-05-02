import os
from .. process import *
from .. task import *
from .. package import *

__all__ = ["Sickle"]

class Sickle(Process):
    Command = "sickle"
    Arguments = [
        ProcessArgument(name="mode", type=str, required=True, default="pe", help="Type of reads [pe | se]"),
        ProcessArgument(name="pe-file1", argument="-f", type=str, help="Input paired-end forward fastq file"),
        ProcessArgument(name="pe-file2", argument="-r", type=str, help="Input paired-end reverse fastq file"),
        ProcessArgument(name="output-pe1", argument="-o", type=str, help="Output trimmed forward fastq file"),
        ProcessArgument(name="output-pe2", argument="-p", type=str, help="Output trimmed reverse fastq file"),
        ProcessArgument(name="pe-combo", argument="-c", type=bool, help="Interleaved input paired-end fastq"),
        ProcessArgument(name="output-combo", argument="-m", type=bool, help="Output interleaved paired-end fastq file"),
        ProcessArgument(name="output-combo-all", argument="-M", type=bool, help="Output interleaved paired-end fastq file including discarded reads"),
        ProcessArgument(name="qual-type", argument="-t", type=str, default="sanger", required=True, help="Quality score type [solexa | illumina | sanger]"),
        ProcessArgument(name="output-single", argument="-s", type=str, help="Output trimmed singles fastq file"),
        ProcessArgument(name="qual-threshold", argument="-q", type=int, default=20, help="Threshold for trimming based on average quality in a window"),
        ProcessArgument(name="length-threshold", argument="-l", type=int, default=20, help="Threshold to keep a read based on length after trimming"),
        ProcessArgument(name="no-fiveprime", argument="-x", type=bool, help="Don't trim from 5'"),
        ProcessArgument(name="gzip-output", argument="-g", type=bool, help="Output gzipped files"),
        ProcessArgument(name="truncate-n", argument="-n", type=int, help="Truncate the first N bases of every read"),
    ]

class PackageSickle(Package):
    PackageName = "sickle"
    Depends = {
        "dpkg": ["git", "build-essential"],
        "pip": []
    }
    Version ="v1.33"

    def script(self):
        script = [
            "git clone -b ${PKG_VERSION} https://github.com/najoshi/sickle.git ${SRCDIR}/sickle"
            "cd ${PKG_SRCDIR}/sickle",
            "make",
            "cp sickle ${PKG_BINDIR}"
        ]
        return script

class SickleTask(BoneTask):
    TaskName = "sickle"
    Directories = ["reads"]

    def _run(self, *args, **kw):
        # XXX: gz?
        outputs = []
        for read_path in self.reads:
            read_fn = os.path.split(read_path)[-1]
            parts = read_fn.split('.')
            read_fn = parts[0]
            extlist = parts[1:]
            out_fn = "%s_trimmed.%s" % (read_fn, str.join('.', extlist))
            out_path = os.path.join(self.dir_reads, out_fn)
            outputs.append(out_path)
        stem = common_filename(*self.reads)
        stem_fn = os.path.split(stem)[-1]
        parts = read_fn.split('.')
        stem_fn = parts[0]
        out_fn = "%s_singles_trimmed.%s" % (stem_fn, str.join('.', extlist))
        singles_fn = os.path.join(self.dir_reads, out_fn)

        # XXX: test if SE or PE mode
        cmdkw = {
            "mode": "pe",
            "pe-file1": self.reads[0],
            "pe-file2": self.reads[1],
            "output-pe1": outputs[0],
            "output-pe2": outputs[1],
            "output-single": singles_fn,
        }
        cmdkw.update(kw)
        sickle = Sickle(**cmdkw)
        sickle.run(wait=True)
        self.reads = outputs

