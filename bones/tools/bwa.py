import os
import operator
import subprocess
import multiprocessing

from .. utils import *
from .. process import *
from .. task import *
from .. package import *

__all__ = ["Index", "Align"]

class Index(Process):
    Command = "bwa"
    Arguments = [
        ProcessArgument(name="bwa_module", type=str, default="index", required=True, help="BWA module name"),
        ProcessArgument(name="prefix", argument="-p", type=str, help="Prefix of database"),
        ProcessArgument(name="algorithm", argument="-a", type=str, help="Algorithm for index construction"),
        ProcessArgument(name="reference", required=True, type=str, help="Path to reference"),
    ]
    IndexExtensionList = ["amb", "ann", "bwt", "pac", "sa"]

    def get_index_dir(self):
        return getattr(self, "_index_dir", None)
    def set_index_dir(self, path):
        self._index_dir = path
    index_dir = property(get_index_dir, set_index_dir)

    def get_prefix(self):
        if hasattr(self, "_prefix"):
            return self._prefix
        if hasattr(self, "_prefix_dir") and hasattr(self, "_reference"):
            ref_fn = os.path.split(self._reference)[-1]
            return os.path.join(self._prefix_dir, ref_fn)
        if hasattr(self, "_reference"):
            return self._reference
        return None
    def set_prefix(self, prefix):
        self._prefix = prefix
    prefix = property(get_prefix, set_prefix)

    def get_reference(self):
        if hasattr(self, "_reference"):
            return self._reference
        if hasattr(self, "_prefix"):
            return self._prefix
        return None
    def set_reference(self, reference):
        self._reference = reference
    prefix = property(get_prefix, set_prefix)

    @property
    def is_valid(self):
        for ext in self.IndexExtensionList:
            fn = "%s.%s" % (self.prefix, ext)
            if not os.path.exists(fn):
                return False
            if self.reference and is_stale(self.reference, fn):
                return False
        return True

class Align(Process):
    Command = "bwa"
    ProcessOptions = {
        "stdout": "pipe"
    }
    Arguments = [
        ProcessArgument(name="bwa_module", type=str, default="mem", required=True, help="BWA module name"),
        ProcessArgument(name="threads", argument="-t", type=int, default=1, help="Number of threads"),
        ProcessArgument(name="min_seed_len", argument="-k", type=int, default=19, help="Minimum seed length"),
        ProcessArgument(name="bandwidth", argument="-w", type=int, default=100, help="Gaps longer than bandwidth will not be found"),
        ProcessArgument(name="zdropoff", argument="-d", type=int, default=100, help="Off-diagonal X-dropoff"),
        ProcessArgument(name="seed_split_ratio", argument="-r", type=float, default=1.5, help="Re-seeding trigger ratio"),
        ProcessArgument(name="max_occurrence", argument="-c", type=int, default=10000, help="Threshold for MEM occurence before discarding"),
        ProcessArgument(name="lazy_rescue", argument="-P", type=bool, default=False, help="Ignore pairing information for rescued hits"),
        ProcessArgument(name="matching_score", argument="-A", type=int, default=1, help="Matching score"),
        ProcessArgument(name="mismatch_penalty", argument="-B", type=int, default=4, help="Mismatch penalty"),
        ProcessArgument(name="gap_open_penalty", argument="-O", type=int, default=6, help="Gap open penalty"),
        ProcessArgument(name="gap_extension_penalty", argument="-E", type=int, default=1, help="Gap extentsion penalty"),
        ProcessArgument(name="clipping_penalty", argument="-L", type=int, default=5, help="Clipping penalty"),
        ProcessArgument(name="unpaired_read_penalty", argument="-U", type=int, default=9, help="Unpaired read penalty"),
        ProcessArgument(name="interleaved_pairs", argument="-p", type=bool, default=False, help="Pairs are interleaved"),
        ProcessArgument(name="read_group", argument="-R", type=str, help="Complete read group header line"),
        ProcessArgument(name="score_cutoff", argument="-T", type=int, default=30, help="Don't output reads with score less than cutoff"),
        ProcessArgument(name="all_alignments", argument="-a", type=bool, default=False, help="Output all alignments including secondary alignments"),
        ProcessArgument(name="comment", argument="-C", type=str, help="Append comment to the SAM file"),
        ProcessArgument(name="hard_clipping", argument="-H", type=bool, default=False, help="Use hard clipping in SAM file"),
        ProcessArgument(name="mark_short_splits", argument="-M", type=bool, default=False, help="Mark shorter split hits as secondary"),
        ProcessArgument(name="verbose", argument="-v", type=int, default=3, help="Control the verbose level of the output."),
        ProcessArgument(name="prefix", type=str, required=True, help="Base index of reference"),
        ProcessArgument(name="reads", type=str, required=True, help="Path to reads file"),
        ProcessArgument(name="mates", type=str, help="Path to mate reads file"),
    ]

    def get_prefix(self):
        thing = getattr(self, "_prefix", None)
        if type(thing) in (str, unicode):
            return thing
        if isinstance(thing, Index):
            return thing.prefix
        return None

    def set_prefix(self, prefix):
        self._prefix = prefix
    prefix = property(get_prefix, set_prefix)

class BWA_IndexTask(BoneTask):
    TaskName = "bwa_index"
    Directories = ["reads", "reference"]

    def _init(self):
        self.reference = symlink(self.reference, self.dir_reference)

    def _run(self, *args, **kw):
        cmdkw = {"reference": self.reference}
        cmdkw.update(kw)
        index = bwa.Index(**cmdkw)
        index.run(wait=True)
        self.index_prefix = index.prefix

class BWA_AlignmentTask(BoneTask):
    Directories = ["alignment"]
    TaskName = "bwa_align"

    def _init(self):
        self.reads = [symlink(fn, self.dir_reads) for fn in self.reads]
        self.fn_alignment = os.path.join(self.dir_alignment, "alignment.sam")

    def _run(self, *args, **kw):
        #if not is_stale(self.reference, self.fn_alignment):
        #   return
        cmdkw = {
            "prefix": self.reference,
            "reads": self.reads[0],
        }
        if len(self.reads) > 1:
            cmdkw["mates"] = self.reads[1]
        cmdkw.update(kw)
        align = bwa.Align(**cmdkw)
        with open(self.fn_alignment, 'w') as fh:
            align.run(stdout=fh, wait=True)

class PackageBWA(Package):
    PackageName = "bwa"
    Depends = {
        "dpkg": ["git", "build-essential", "zlib1g-dev"],
        "pip": []
    }
    Version = "v0.7.13"

    def script(self):
        script = [
            "git clone -b ${PKG_VERSION} https://github.com/lh3/bwa.git ${PKG_SRCDIR}/bwa",
            "cd ${PKG_SRCDIR}/bwa",
            "make",
            "cp bwa ${PKG_BINDIR}",
        ]
        return script
