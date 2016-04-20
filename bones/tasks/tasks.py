import os
from celery import Celery

import uuid
import json

from bones import *
from bones.utils import *
from bones.fast import FastA
from bones.fastqc import FastQC
from bones.samfile import Samfile
import ssw

default_celery_broker = "amqp://guest@bones-rabbitmq:10101"
amqp_url = os.getenv("CELERY_BROKER", default_celery_broker)

app = Celery(
    __name__,
    broker=amqp_url,
    backend=amqp_url,
    include=["bones", "bones.tasks"]
)

# Optional configuration, see the application user guide.
#app.conf.update(
    #CELERY_TASK_RESULT_EXPIRES=3600,
#)


class Context(dict):
    Directories = ["reference", "qc", "alignment", "consensus", "reads", "logs"]
    # reference=None, reads=None, mates=None, dir_output=None

    def __init__(self, context=None, **kw):
        context = context if context != None else {}
        super(Context, self).__init__()
        self.update(context)
        self.update(kw)

    def update(self, ns):
        for key in ns:
            self.__setattr__(key, ns[key])

    def __getattr__(self, key):
        nkey = ('_' + key) if key[0] != '_' else key
        print("__getattr__(" + nkey + ")")
        if nkey in self:
            return self[nkey]
        raise AttributeError(key)

    def __setattr__(self, key, value):
        nkey = ('_' + key) if key[0] != '_' else key
        print("__setattr__(" + nkey + ")")
        self[nkey] = value

    def init_directories(self):
        for dirname in self.Directories:
            dirpath = os.path.join(self.dir_output, dirname)
            if not os.path.isdir(dirpath):
                os.makedirs(dirpath)
            key = "_dir_%s" % dirname
            self[key] = dirpath

    def verify_link(self, source, target):
        try:
            return os.readlink(target) == source
        except OSError:
            pass
        return False

    def symlink(self, source, directory):
        if not source:
            return None
        source = os.path.abspath(source)
        (path, filename) = os.path.split(source)
        target = os.path.join(directory, filename)
        if not self.verify_link(source, target):
            os.symlink(source, target)
        return target

    def init(self):
        if "_runid" not in self:
            self["_runid"] = str(uuid.uuid4()).split('-')[0]
        if "_dir_output" not in self:
            self["_dir_output"] = self.runid
        #
        if not os.path.isdir(self.dir_output):
            os.makedirs(self.dir_output)
        self.init_directories()
        # files
        self.reads = [self.symlink(fn, self.dir_reads) for fn in self.reads]
        self.reference = self.symlink(self.reference, self.dir_reference)
        # filenames
        self.fn_alignment = os.path.join(self.dir_alignment, "alignment.sam")
        self.fn_consensus = os.path.join(self.dir_consensus, "consensus.sam")
        self.fn_results_json = os.path.join(self.dir_output, "results.json")
        self.fn_results_txt = os.path.join(self.dir_output, "results.txt")

    def build_index(self):
        index = bwa.Index(reference=self.reference)
        index.run(wait=True)
        self.index_prefix = index.prefix

    def align(self):
        if not is_stale(self.reference, self.fn_alignment):
            return
        kw = {
            "prefix": self.reference,
            "reads": self.reads[0],
        }
        if len(self.reads) > 1:
            kw["mates"] = self.reads[1]
        align = bwa.Align(**kw)
        with open(self.fn_alignment, 'w') as fh:
            align.run(stdout=fh, wait=True)

    def generate_qc(self):
        qc_glob = os.path.join(self.dir_qc, "*")
        stale_flag = is_stale(self.reads, qc_glob)
        if self.mates:
            stale_flag |= is_stale(self.mates, qc_glob)
        if not stale_flag:
            return
        reads = [self.reads]
        if self.mates:
            reads.append(self.mates)
        qc = FastQC(outdir=self.dir_qc, seqfiles=reads)
        qc.run(wait=True)

    def build_consensus(self):
        if not is_stale(self.fn_alignment, self.fn_consensus):
            return
        self.align_reads()
        samf = samfile.Samfile(self.fn_alignment)
        cc = consensus.Consensus()
        sequences = cc.call_samfile(samf.samf)
        fa = FastA(sequences)
        fa.save(self.fn_consensus)

    def compare_consensus(self):
        refseqs = FastA.load(self.reference)
        conseqs = FastA.load(self.fn_consensus)
        aligner = ssw.Aligner()
        for reference in refseqs:
            row = []
            for query in conseqs:
                alignment = aligner.align(query, reference)
                row.append(alignment)
            row.sort(cmp=lambda x, y: cmp(x.score, y.score), reverse=True)
            winner = row[0]
            yield (reference, winner)

    def build_report(self):
        refs = FastA.load(self.reference)
        report = {
            "reference_count": len(refs),
            "references": [],
        }

        global_verified_flag = True
        for (reference, alignment) in self.compare_consensus():
            verified_flag = alignment.match_count == len(reference)
            global_verified_flag &= verified_flag
            alstat = {
                "name": reference.name,
                "verified": str(verified_flag),
                "cigar": alignment.cigar,
                "alignment": alignment.alignment_report,
            }
            report["references"].append(alstat)
        report["verified"] = str(global_verified_flag)
        return report
    
    def build_report_txt(self, report):
        rpt = ''
        for ref_report in report["references"]:
            rpt += "Reference: %(name)s\nVerified: %(verified)s\nCIGAR: %(cigar)s\n%(alignment)s\n" % ref_report
        return rpt

    def run(self):
        self.init_filesystem()
        self.generate_qc()
        self.build_consensus()
        report = self.build_report()
        json_report = json.dumps(report)
        txt_report = self.build_report_txt(report)
        with open(self.fn_results_json, 'w') as fh:
            fh.write(json_report)
        with open(self.fn_results_txt, 'w') as fh:
            fh.write(txt_report)

@app.task
def ngs_workflow(cfg):
    ctxt = Context(cfg)
    ctxt.init()
    return dict(ctxt)

@app.task
def align(cfg):
    ctxt = Context(cfg)
    ctxt.align()
    return dict(ctxt)

@app.task
def samtools(*args, **kw):
    print("samtools", args, kw)

@app.task
def build_index(cfg):
    ctxt = Context(cfg)
    ctxt.build_index()
    return dict(ctxt)

@app.task
def run_fastq(*args, **kw):
    print("run_fastqc", args, kw)

@app.task
def trim_reads(*args, **kw):
    print("trim_reads", args, kw)
