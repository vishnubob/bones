import errno
import glob
import sys
import os

import pysam

from . utils import *

__all__ = ["Samfile"]

class Samfile(object):
    def __init__(self, basename, reffn=None):
        self._cache = {}
        basename_parts = basename.split('.')
        if basename_parts[-1].lower() in ("sam", "bam"):
            basename = str.join('.', basename_parts[:-1])
        self.basename = basename
        self.basedir = os.path.split(self.basename)[0]
        if not (os.path.exists(self.samfn) or os.path.exists(self.bamfn)):
            msg = "No such file: '%s' or '%s'" % (self.samfn, self.bamfn)
            raise IOError(errno.ENOENT, msg)
        self.reffn = reffn
        self.prepare()

    @property
    def samfn(self):
        return self.basename + ".sam"

    @property
    def bamfn(self):
        return self.basename + ".bam"

    @property
    def baifn(self):
        return self.bamfn + ".bai"

    def get_samf(self, fn):
        (samf, cache_mtime) = self._cache.get(fn, (None, 0))
        source_mtime = os.path.getmtime(fn)
        if source_mtime != cache_mtime:
            if samf != None:
                samf.close()
            samf = pysam.AlignmentFile(fn, "rb")
            self._cache[fn] = (samf, source_mtime)
        return samf

    @property
    def samf(self):
        if os.path.exists(self.bamfn):
            if not os.path.exists(self.samfn):
                # no SAM file to test against, return the BAM
                return self.get_samf(self.bamfn)
            # since there is a SAM file, test to see if the BAM is stale
            if not is_stale(self.samfn, self.bamfn):
                return self.get_samf(self.bamfn)
        return self.get_samf(self.samfn)

    @property
    def is_sorted(self):
        return self.samf.header.get("HD", {}).get("SO", "") == "coordinate"

    @property
    def is_bam(self):
        # https://github.com/pysam-developers/pysam/issues/186
        return self.samf.filename.lower().endswith(".bam")

    @property
    def is_sam(self):
        # https://github.com/pysam-developers/pysam/issues/186
        return self.samf.filename.lower().endswith(".sam")

    def prepare(self):
        # are we dealing with a bam?
        if self.is_sam:
            self.to_bam()
        # is our bam sorted?
        if not self.is_sorted:
            self.sort()
        # is our index stale?
        if is_stale(self.bamfn, self.baifn):
            self.build_index()
        # clear our cache
        self._cache = {}

    def to_bam(self):
        msg = "Converting %s to BAM %s" % (self.samfn, self.bamfn)
        print(msg)
        # we need to make sure we are basing our conversion on the *SAM* file
        samf = self.get_samf(self.samfn)
        bamf = pysam.AlignmentFile(self.bamfn, "wb", template=self.samf)
        map(bamf.write, samf)
        bamf.close()

    def sort(self):
        msg = "Sorting %s" % self.bamfn
        print(msg)
        tempfn_stem = os.path.join(self.basedir, temp_filename())
        pysam.sort(self.bamfn, tempfn_stem)
        tempfn_glob = glob.glob(tempfn_stem + '*')
        assert len(tempfn_glob) == 1, "Unexpected number of temporary output files: %r" % tempfn_glob
        tempfn = tempfn_glob[0]
        # rename our sorted bamfn 
        os.rename(tempfn, self.bamfn)

    def rmdup(self):
        msg = "Removing duplicates in %s" % self.bamfn
        print(msg)
        tempfn_stem = os.path.join(self.basedir, temp_filename())
        pysam.rmdup("-s", self.bamfn, tempfn_stem)
        tempfn_glob = glob.glob(tempfn_stem + '*')
        assert len(tempfn_glob) == 1, "Unexpected number of temporary output files: %r" % tempfn_glob
        tempfn = tempfn_glob[0]
        # rename our dedupped bamfn 
        os.rename(tempfn, self.bamfn)

    def build_index(self):
        msg = "Building index %s" % self.baifn
        print(msg)
        pysam.index(self.bamfn)
