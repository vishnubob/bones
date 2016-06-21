import os
import uuid
from celery import Celery, Task

__all__ = ["app", "Context", "BoneTask"]

default_celery_broker = "amqp://guest@broker"
amqp_url = os.getenv("CELERY_BROKER", default_celery_broker)
bones_output_dir = os.getenv("BONES_OUTPUT_DIR", "/tmp")

app = Celery(
    __name__,
    broker=amqp_url,
    backend=amqp_url,
    include=["bones", "bones.tasks"]
)

@app.task
def plumrun(cmd, **kw):
    print("plumrun cmd: %s" % repr(cmd))
    print("plumrun kw: %s" % repr(kw))
    cmd()

# Optional configuration, see the application user guide.
#app.conf.update(
    #CELERY_TASK_RESULT_EXPIRES=3600,
#)

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

