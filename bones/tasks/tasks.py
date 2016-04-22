import os
import sys

import inspect
import uuid
import json
import pprint

from celery import Celery, Task
from bones import *
from bones.utils import *
from bones.fast import FastA
from bones.fastqc import FastQC
from bones.samfile import Samfile
from bones.sickle import Sickle
import ssw

__all__ = ["app", "Context"]

default_celery_broker = "amqp://guest@broker"
amqp_url = os.getenv("CELERY_BROKER", default_celery_broker)
bones_output_dir = os.getenv("BONES_OUTPUT_DIR", "/tmp")

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

def verify_link(source, target):
    try:
        return os.readlink(target) == source
    except OSError:
        pass
    return False

def symlink(source, directory):
    if not source:
        return None
    source = os.path.abspath(source)
    (path, filename) = os.path.split(source)
    target = os.path.join(directory, filename)
    if source == target:
        return target
    if not verify_link(source, target):
        try:
            os.symlink(source, target)
        except Exception, err:
            message = "Failed to symlink source '%s' to target '%s' (%s)" % (source, target, err)
            raise RuntimeError(message)
    return target

class Context(dict):
    def __init__(self, *args, **kw):
        super(Context, self).__init__()
        self.init(*args, **kw)

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

class ContextualizedTask(Task):
    context = None

    def bind_context(self, context):
        self.__dict__["context"] = context

    def unbind_context(self):
        context = self.__dict__["context"]
        self.__dict__["context"] = None
        return context

    def run(self, context=None, **kw):
        self.bind_context(Context(context))
        self.init()
        ret = self._run(**kw)
        context = self.unbind_context()
        ret = ret if ret != None else context
        return ret
    
    def init(self):
        pass
    
    def _run(self, *args, **kw):
        raise RuntimeError("You need to overload this method")

    def __getattr__(self, key):
        context = self.__dict__.get("context", None)
        if context != None and key in context:
            return context[key]
        return getattr(super(ContextualizedTask, self), key)

    def __setattr__(self, key, value):
        context = self.__dict__.get("context", None)
        if context != None:
            context[key] = value
        else:
            super(ContextualizedTask, self).__setattr__(key, value)

class BoneTask(ContextualizedTask):
    TaskName = "BoneTask"
    Directories = []

    def init(self):
        if "runid" not in self.context:
            self.runid = str(uuid.uuid4()).split('-')[0]
        if "dir_output" not in self.context:
            self.dir_output = os.path.join(bones_output_dir, self.runid)
        elif os.path.isabs(self.dir_output):
            self.dir_output = os.path.join(bones_output_dir, self.dir_output)
        if not os.path.isdir(self.dir_output):
            os.makedirs(self.dir_output)
        for dirname in self.Directories:
            dirpath = os.path.join(self.dir_output, dirname)
            if not os.path.isdir(dirpath):
                os.makedirs(dirpath)
            key = "dir_%s" % dirname
            setattr(self, key, dirpath)
        self._init()

    def _init(self):
        pass

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

def bootstrap_tasks():
    thismodule = sys.modules[__name__]
    ns = thismodule.__dict__
    _all = ns.get("__all__", list())
    for key in ns.keys():
        cls = ns[key]
        if inspect.isclass(cls) and issubclass(cls, BoneTask) and (cls.__name__ != "BoneTask"):
            cls.bind(app)
            ns[cls.TaskName] = cls()
            _all.append(cls.TaskName)
    ns["__all__"] = _all

bootstrap_tasks()
