import os
import operator
import subprocess
from . utils import which

__all__ = ["Process", "ProcessArgument", "Pipe"]

class ProcessArgument(object):
    def __init__(self, name=None, argument=None, type=None, default=None, required=False, position=None, help=None):
        self.name = name
        self.argument = argument
        self.type = type
        self.default = default
        self.required = required
        self.help = help

class ProcessMeta(type):
    def __new__(cls, name, parents, dct):
        argmap = dct.get("_argmap", {})
        for parg in dct["Arguments"]:
            argmap[parg.name] = parg
        dct["_argmap"] = argmap
        return super(ProcessMeta, cls).__new__(cls, name, parents, dct)

class Process(object):
    Command = "__command__"
    ProcessOptions = {}
    Arguments = []
    ReturnCode = 0
    __metaclass__ = ProcessMeta

    def __init__(self, command_path=None, **args):
        command_path = command_path if command_path != None else self.Command
        command_path = which(command_path)
        self.command_path = command_path
        # make local copies
        for (key, val) in args.iteritems():
            setattr(self, key, val)

    def set_argument(self, name, value):
        if name not in self._argmap:
            raise KeyError, "unknown argument '%s'" % name
        parg = self._argmap[name]
        if parg.type != None:
            # XXX: autocast?
            value = parg.type(value)
        super(Process, self).__setattr__(name, value)

    def __getattr__(self, key):
        if key in self._argmap:
            return None
        return super(Process, self).__getattr__(key)

    def __setattr__(self, key, val):
        if key in self._argmap:
            return self.set_argument(key, val)
        super(Process, self).__setattr__(key, val)

    def cli_arguments(self, **kw):
        cli = []
        for parg in self.Arguments:
            value = kw.get(parg.name, getattr(self, parg.name, None))
            if value != None:
                if parg.argument == None:
                    cli.append("%s" % value)
                elif parg.type == bool and value:
                    cli.append(parg.argument)
                else:
                    cli.append(parg.argument)
                    cli.append("%s" % value)
            elif parg.required:
                if parg.type == bool and parg.default:
                    cli.append(parg.argument)
                elif parg.argument == None:
                    cli.append("%s" % parg.default)
                else:
                    cli.append(parg.argument)
                    cli.append("%s" % parg.default)
        return cli

    def cli_command(self, **kw):
        return [self.command_path]

    def cli(self, **kw):
        return self.cli_command(**kw) + self.cli_arguments(**kw)

    def subprocess_arguments(self, **kw):
        config = self.ProcessOptions.copy()
        config.update(kw)
        opts = {}
        for (key, val) in config.iteritems():
            if type(val) in (str, unicode):
                if val.lower() == "pipe":
                    val = subprocess.PIPE
            opts[key] = val
        return opts

    def execute(self, args=None, **kw):
        args = args if args else {}
        cli = self.cli(**args)
        subprocess_args = self.subprocess_arguments(**kw)
        print cli
        self.proc = subprocess.Popen(cli, **subprocess_args)
        return self.proc
    __call__ = execute

    def assert_return_code(self):
        if self.ReturnCode == None:
            return
        if self.proc.returncode == None:
            return
        if self.proc.returncode != self.ReturnCode:
            raise RuntimeError, "The command '%s' did not return the expected return code (%s instead of %s)" % (self.command_path, self.proc.returncode, self.ReturnCode)

    def wait(self):
        self.proc.wait()
        self.assert_return_code()
        return self.proc.returncode

    def poll(self):
        if self.proc.poll() == None:
            return
        self.assert_return_code()
        return self.proc.returncode

class Pipe(object):
    def __init__(self, stdout=None, stdin=None):
        self.stdout = stdout
        self.stdin = stdin

    def execute(self, stdin_args=None, stdout_args=None):
        self.stdout_proc = self.stdout.execute(args=stdout_args, stdout=subprocess.PIPE)
        self.stdin_proc = self.stdin.execute(args=stdin_args, stdin=self.stdout_proc.stdout)
        return (self.stdout_proc, self.stdin_proc)
    __call__ = execute

    def wait(self):
        self.stdout.wait()
        self.stdin.wait()
        return self.stdin_proc.returncode

    def poll(self):
        if self.stdin.poll() == None:
            return
        if self.stdout.poll() == None:
            return
        return self.stdin_proc.returncode
