import os
import operator
import subprocess
import multiprocessing

from . utils import *
from . process import Process

__all__ = ["Index", "Align"]

class Index(object):
    IndexExtensionList = ["amb", "ann", "bwt", "pac", "sa"]

    def __init__(self, reference=None, prefix=None):
        if (reference == None and prefix == None):
            raise ValueError, "You must provide a path to reference file or a BWA index prefix" 
        self.reference = reference
        if prefix == None:
            (basedir, reffn) = os.path.split(os.path.abspath(self.reference))
            (refstem, refext) = os.path.splitext(reffn)
            prefix = os.path.join(basedir, refstem + "_bwa_index", refstem)
        self.prefix = prefix
        if not self.is_valid:
            self.build_index()

    @property
    def is_valid(self):
        for ext in self.IndexExtensionList:
            fn = "%s.%s" % (self.prefix, ext)
            if not os.path.exists(fn):
                return False
            if self.reference and is_stale(self.reference, fn):
                return False
        return True

    def build_index(self):
        # make sure the base directory for the prefix exists
        basedir = os.path.split(self.prefix)[0]
        if not os.path.isdir(basedir):
            os.mkdir(basedir)
        cmd = ["bwa", "index", "-p", self.prefix, self.reference]
        proc = subprocess.Popen(cmd)
        proc.wait()
        if proc.returncode != 0:
            msg = "The command '%s' did not exit cleanly (return code = %d)" % (str.join(' ', cmd), proc.returncode)
            raise RuntimeError, msg

class Align(Process):
    Command = "bwa"
    Arguments = [
        ProcessArgument(name="threads", argument="-t", type=int, default=1, help="Number of threads"),
        ProcessArgument(name="min_seed_len", argument="-k", type=int, default=19, help="Minimum seed length")
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
    ]

    def __init__(self, index, threads=-1):
        self.index = index
        self.threads = threads if threads >= 0 else multiprocessing.cpu_count()

    def align(self, reads1, reads2=None, output=None, args=None):
        args = args if args != None else dict()
        if self.threads and "-t" not in args:
            args["-t"] = self.threads
        args = list(map(str, reduce(operator.add, args.items(), tuple())))
        reads = [reads1] if reads2 == None else [reads1, reads2]
        cmd = ["bwa", "mem"] + args + [self.index.prefix] + reads
        if output == None:
            output = common_filename(*reads)
            if output == '':
                output = "alignment.sam"
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        with open(output, 'wb') as fout:
            fout.write(proc.stdout.read())
        proc.wait()
        if proc.returncode != 0:
            msg = "The command '%s' did not exit cleanly (return code = %d)" % (str.join(' ', cmd), proc.returncode)
            raise RuntimeError, msg
        return output
