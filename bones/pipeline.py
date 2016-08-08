import plumbum
import shutil
from . import utils
from . import consensus
import os
import uuid
from celery import Celery, Task
from . fast import FastA
import inspect
import pysam
import ssw
import json

default_output_dir = os.getenv("BONES_OUTPUT_DIR", "/tmp")

def plumcmd(cmd):
    cmd = plumbum.path.LocalPath(cmd)
    return plumbum.cmd.__getattr__(cmd)

class Context(dict):
    def __init__(self, *args, **kw):
        super(Context, self).__init__()
        self.init(*args, **kw)

    def __getitem__(self, key):
        # XXX: is this too goofy?
        val = super(Context, self).__getitem__(key)
        try:
            val = val % self
        except:
            pass
        return val

    def init(self, context=None, **kw):
        context = context if context != None else {}
        self.update(context)
        self.update(kw)
        if "_history_stack" not in self:
            self._history_stack = []

    def push(self):
        ctxt = self.copy()
        del ctxt["_history_stack"]
        self["_history_stack"].append(ctxt)

    def pop(self):
        assert len(self._history_stack), "pop requested on empty history stack"
        ctxt = self._history_stack.pop()
        ctxt["_history_stack"] = self._history_stack
        self.clear()
        self.init(ctxt)

class Bindable(object):
    def bind_context(self, context):
        self.__dict__["context"] = context

    def unbind_context(self):
        context = self.__dict__["context"]
        self.__dict__["context"] = None
        return context

    def __getattr__(self, key):
        context = self.__dict__.get("context", None)
        if context != None and key in context:
            return context[key]
        return getattr(super(Bindable, self), key)

    def __setattr__(self, key, value):
        context = self.__dict__.get("context", None)
        if context != None:
            context[key] = value
        else:
            super(Bindable, self).__setattr__(key, value)

class Pipeline(list, Bindable):
    Directories = []
    DefaultContext = {}

    def __init__(self, **context):
        self.context = Context(self.DefaultContext)
        self.context.update(context)

    def init(self):
        pass

    def run(self):
        self.bind_context(self.context)
        self.init()
        for stage in self:
            if inspect.isclass(stage):
                stage = stage()
            stage.bind_context(self.context)
            stage.run()
            stage.unbind_context()
        self.unbind_context()

class SequencingPipeline(Pipeline):
    # XXX: r1/r2 for pooled runs

    DefaultContext = {
        "runid": None,
        "reference": None,
        "reads": None,
        # directories
        "dir_output": None,
        "dir_reference": "%(dir_output)s/reference",
        "dir_qc": "%(dir_output)s/qc",
        "dir_alignment": "%(dir_output)s/alignment",
        "dir_consensus": "%(dir_output)s/consensus",
        "dir_reads": "%(dir_output)s/reads",
        "dir_logs": "%(dir_output)s/logs",
        "dir_reports": "%(dir_output)s/reports",
        "dir_assembly": "%(dir_output)s/assembly",
        # files
        "fn_reference": "%(dir_reference)s/reference.fa",
        "fn_alignment": "%(dir_alignment)s/alignment.bam",
        "fn_reads": None,
    }

    def init(self):
        if self.context.get("runid", None) == None:
            self.context["runid"] = str(uuid.uuid4()).split('-')[0]
        if self.context.get("dir_output", None) == None:
            self.context["dir_output"] = os.path.join(default_output_dir, self.runid)
        self.init_directories()
        self.init_filesystem()

    def init_directories(self):
        if not os.path.isdir(self.dir_output):
            os.makedirs(self.dir_output)
        for key in self.context.keys():
            if not key.startswith("dir_"):
                continue
            dirpath = self.context[key]
            if not os.path.isdir(dirpath):
                os.makedirs(dirpath)

    def init_filesystem(self):
        # files
        # XXX: abstract input files
        if self.fn_reads == None:
            self.fn_reads = []
        for read in self.reads:
            if not read.startswith(self.dir_reads):
                target = os.path.join(self.dir_reads, os.path.split(read)[-1])
                if os.path.exists(target):
                    os.unlink(target)
                os.symlink(read, target)
                self.fn_reads.append(target)
            else:
                self.fn_reads.append(read)
        if self.reference and not self.reference.startswith(self.dir_reference):
            if os.path.exists(self.fn_reference):
                os.unlink(self.fn_reference)
            os.symlink(self.reference, self.fn_reference)
        # filenames
        self.fn_alignment = os.path.join(self.dir_alignment, "alignment.bam")

class PipelineStage(Bindable):
    Name = None
    context = None

    def version(self):
        return "unknown"
    
    def execute(self):
        pass

    def run(self, context=None, **kw):
        self.init()
        ret = self._run(**kw)
        ret = ret if ret != None else context
        return ret
    
    def init(self):
        pass
    
    def _run(self, *args, **kw):
        raise RuntimeError("You need to overload this method")

class PipelineCommand(PipelineStage):
    Command = "false"

    def args(self):
        return []

    def command(self):
        cmd = plumcmd(self.Command)
        cmd = cmd[self.args()]
        return cmd
        
    def _run(self):
        # XXX: extra
        self.extra = []
        cmd = self.command()
        print "executing: '%s'" % cmd
        cmd()

class SamtoolsBAM(PipelineCommand):
    Name = "samtools_bam"
    Command = "samtools"

    def args(self):
        return ["view"] + self.extra + ["-bS", "-"]

class SamtoolsSort(PipelineCommand):
    Name = "samtools_sort"
    Command = "samtools"

    def args(self):
        prefix = os.path.splitext(self.fn_alignment)[0]
        return ["sort"] + self.extra + [self.fn_alignment, prefix]

class SamtoolsIndex(PipelineCommand):
    Name = "samtools_index"
    Command = "samtools"

    def args(self):
        return ["index"] + self.extra + [self.fn_alignment]

class BWA_Index(PipelineCommand):
    Name = "bwa_index"
    Command = "bwa"

    def args(self):
        return ["index"] + self.extra + [self.fn_reference]

class Megahit(PipelineCommand):
    Name = "megahit"
    Command = "megahit"

    def init(self):
        # XXX: i'm just making this up right now
        self.preset = self.context.get("megahit_preset", "single-cell")

    def args(self):
        if len(self.fn_reads) == 2:
            (read_1, read_2) = self.fn_reads
        else:
            msg = "Megahit pipeline command only supports a single pair of paired-end reads currently"
            raise RuntimeError(msg)
        outdir = os.path.join(self.dir_assembly, "megahit")
        if os.path.exists(outdir):
            shutil.rmtree(outdir)
        return ["--presets", self.preset, "-1", read_1, "-2", read_2, "-o", outdir]

class BWA_Align(PipelineCommand):
    Name = "bwa_align"
    Command = "bwa"

    def args(self):
        return ["mem"] + self.extra + [self.fn_reference] + self.fn_reads 

    def samtools_tobam(self):
        return plumcmd("samtools")["view", "-bS", "-"]

    def command(self):
        if not self.fn_alignment:
            self.fn_alignment = os.path.join(self.dir_alignment, "alignment.bam")
        if os.path.splitext(self.fn_alignment)[-1].lower() == "sam":
            cmd = (plumcmd(self.Command)[self.args()] > self.fn_alignment)
        else:
            cmd = (plumcmd(self.Command)[self.args()] | self.samtools_tobam() > self.fn_alignment)
        return cmd

class FastQC(PipelineCommand):
    Name = "fastqc"
    Command = "FastQC"

    def run(self):
        pass

class Consensus(PipelineStage):
    Name = "consensus_analysis"

    def _run(self):
        self.fn_results_json = os.path.join(self.dir_reports, "consensus_results.json")
        self.fn_results_txt = os.path.join(self.dir_reports, "consensus_results.txt")
        self.fn_consensus = os.path.join(self.dir_consensus, "consensus.fa")
        self.references = FastA.load(self.fn_reference)
        self.write_report()

    def call_consensus(self):
        self.cc = consensus.Consensus()
        samf = pysam.AlignmentFile(self.fn_alignment, "rb")
        seqs = []
        for sequence in self.cc.call_samfile(samf):
            yield (sequence, self.cc)
            seqs.append(sequence)
        fa = FastA(seqs)
        fa.save(self.fn_consensus)

    def execute_alignment(self, query):
        row = []
        self.dna_alphabet = "AGTCNRYSWKMBDHV"
        matrix = ssw.DNA_ScoreMatrix(alphabet=self.dna_alphabet)
        aligner = ssw.Aligner(matrix=matrix)
        for reference in self.references:
            alignment = aligner.align(query, reference)
            row.append(alignment)
        row.sort(cmp=lambda x, y: cmp(x.score, y.score), reverse=True)
        winner = row[0]
        return (winner.reference, winner)

    def compare_consensus(self):
        for (consensus_sequence, consensus_caller) in self.call_consensus():
            (reference, alignment) = self.execute_alignment(consensus_sequence)
            yield (reference, alignment, consensus_caller)

    def build_report(self):
        refs = FastA.load(self.fn_reference)
        report = {
            "reference_count": len(refs),
            "references": [],
        }

        global_verified_flag = True
        for (reference, alignment, consensus_caller) in self.compare_consensus():
            verified_flag = alignment.match_count == len(reference)
            global_verified_flag &= verified_flag
            alstat = {
                "name": reference.name,
                "verified": verified_flag,
                "cigar": alignment.cigar,
                "alignment": alignment.alignment_report(),
            }
            alstat.update(consensus_caller.coverage)
            report["references"].append(alstat)
        report["verified"] = global_verified_flag
        return report
    
    def build_report_txt(self, report):
        rpt = ''
        for ref_report in report["references"]:
            rpt += "Reference: %(name)s\nVerified: %(verified)s\nCIGAR: %(cigar)s\n%(alignment)s\n" % ref_report
        return rpt

    def write_report(self):
        report = self.build_report()
        json_report = json.dumps(report)
        txt_report = self.build_report_txt(report)
        with open(self.fn_results_json, 'w') as fh:
            fh.write(json_report)
        with open(self.fn_results_txt, 'w') as fh:
            fh.write(txt_report)

def bootstrap():
    import sys
    import inspect
    thismodule = sys.modules[__name__]
    ns = thismodule.__dict__
    tasks = {}
    for (name, cls) in ns.items():
        if inspect.isclass(cls) and issubclass(cls, PipelineStage) and (cls.Name != None):
            ns[cls.Name] = cls
    del ns["bootstrap"]
bootstrap()
