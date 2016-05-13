import os
import operator
import subprocess
import multiprocessing

from .. utils import *
from .. process import *
from .. task import *
from .. package import *

__all__ = ["BCL2FastQ"]

class BCL2FastQ(Process):
    Command = "bcl2fastq"
    Arguments = [
        ProcessArgument(name="min_log_level", argument="-l", type=str, default="info", help="minimum log level"),
        ProcessArgument(name="input_dir", argument="-i", type=str, help="pah to input directory"),
        ProcessArgument(name="runfolder_dir", argument="-R", type=str, help="path to runfolder directory"),
        ProcessArgument(name="intensities_dir", argument="--intensities-dir", type=str, help="path to intensities directory"),
        ProcessArgument(name="output_dir", argument="-o", type=str, help="path to output directory"),
        ProcessArgument(name="interop_dir", argument="interop-dir", type=str, help="path to demultiplexing statistics directory"),
        ProcessArgument(name="stats_dir", argument="--stats-dir", type=str, help="path to human-readable demultiplexing statistics directory"),
        ProcessArgument(name="reports_dir", argument="--reports-dir", type=str, help="path to reporting directory"),
        ProcessArgument(name="sample_sheet", argument="--sample-sheet", type=str, help="path to sample sheet"),
        ProcessArgument(name="aggregated_tiles", argument="--aggregated-tiles", type=str, default="auto", help="tiles aggregation structure of input files"),
        ProcessArgument(name="loading_threads", argument="--loading-threads", type=int, default=4, help="number of threads used for loading BCL data"),
        ProcessArgument(name="demultiplexing_threads", argument="--demultiplexing-threads", type=int, help="number of threads used for demultiplexing"),
        ProcessArgument(name="processing_threads", argument="--processing-threads", type=int, help="number of threads used for processing demultiplexed data"),
        ProcessArgument(name="writing_threads", argument="--writing-threads", type=int, help="number of threads used for processing demultiplexed data"),
        ProcessArgument(name="tiles", argument="--tiles", type=str, help="Comma-separated list of regular expressions to select only a subset of the tiles available in the flow-cell"),
        ProcessArgument(name="read_group", argument="-R", type=str, help="Complete read group header line"),
        ProcessArgument(name="minimum_trimmed_read_length", argument="--minimum-trimmed-read-length", type=int, default=35, help="minimum read length after adapter trimming"),
        ProcessArgument(name="use_bases_mask", argument="--use-bases-mask", type=str, help="specifies how to use each cycle"),
        ProcessArgument(name="mask_short_adapter_reads", argument="--mask-short-adapter-reads", type=int, default=22, help="smallest number of remaining bases below which whole read is masked"),
        ProcessArgument(name="adapter_stringency", argument="--adapter-stringency", type=float, default=0.9, help="adapter stringency"),
        ProcessArgument(name="ignore_missing_bcls", argument="--ignore-missing-bcls", type=bool, default=False, help="assume 'N'/'#' for missing calls"),
        ProcessArgument(name="ignore_missing_filter", argument="--ignore-missing-filter", type=bool, default=False, help="assume 'true' for missing filters"),
        ProcessArgument(name="ignore_missing_positions", argument="--ignore-missing-positions", type=bool, default=False, help="assume [0,i] for missing positions, where i is incremented starting from 0"),
        ProcessArgument(name="ignore_missing_controls", argument="--ignore-missing-control", type=bool, default=False, help="assume 0 for missing controls"),
        ProcessArgument(name="write_fastq_reverse_complement", argument="--write-fastq-reverse-complement", type=bool, default=False, help="Generate FASTQs containing reverse complements of actual data"),
        ProcessArgument(name="with_failed_reads", argument="--with-failed-reads", type=bool, default=False, help="include non-PF clusters"),
        ProcessArgument(name="create_fastq_for_index_reads", argument="--create-fastq-for-index-reads", type=bool, default=False, help="create FASTQ files also for index reads"),
        ProcessArgument(name="find_adapters_with_sliding_window", argument="--find-adapters-with-sliding-window", type=bool, default=False, help="find adapters with simple sliding window algorithm"),
        ProcessArgument(name="no_bgzf_compression", argument="--no-bgzf-compression", type=bool, default=False, help="Turn off BGZF compression for FASTQ files"),
        ProcessArgument(name="fastq_compression_level", argument="--fastq-compression-level", type=int, default=4, help="Zlib compression level (1-9) used for FASTQ files"),
        ProcessArgument(name="barcode_mismatches", argument="--barcode-mismatches", type=int, default=1, help="number of allowed mismatches per index"),
        ProcessArgument(name="no_lane_splitting", argument="--no-lane-splitting", type=bool, help="Do not split fastq files by lane."),
    ]

class BCL2FastQ_Tasl(BoneTask):
    Directories = ["alignment"]
    TaskName = "bcl2fastq"

    def _init(self):
        #self.reads = [symlink(fn, self.dir_reads) for fn in self.reads]
        #self.fn_alignment = os.path.join(self.dir_alignment, "alignment.sam")
        pass

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

class PackageBCL2FastQ(Package):
    PackageName = "bcl2fastq"
    Depends = {
        "dpkg": ["build-essential", "libboost1.54-all-dev", "cmake", "zlibc", "unzip", "wget"],
        "pip": []
    }
    Version = "v2.17.1.14"
    Filename = "bcl2fastq2-%s" % Version
    ZIP_Filename = Filename + ".tar.zip"
    GZ_Filename = Filename + ".tar.gz"
    URL = "ftp://webdata2:webdata2@ussd-ftp.illumina.com/downloads/software/bcl2fastq/%s" % ZIP_Filename

    def script(self):
        script = [
            "cd ${PKG_SRCDIR}",
            "wget %s" % self.URL,
            "unzip %s" % self.ZIP_Filename,
            "tar xzf %s" % self.GZ_Filename,
            "mkdir bcl2fastq/build",
            "cd bcl2fastq/build",
            "../src/configure --prefix=/usr/local",
            "make install",
        ]
        return script
