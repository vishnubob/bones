import os
import operator
import subprocess
from . utils import which

__all__ = ["Process", "ProcessArgument"]

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
        self._args = {}
        for (key, val) in args.iteritems():
            setattr(self, key, val)

    def get_argument(self, name):
        if name not in self._argmap:
            raise KeyError, "unknown argument '%s'" % name
        parg = self._argmap[name]
        return self._args.get(name, parg.default)

    def set_argument(self, name, value):
        if name not in self._argmap:
            raise KeyError, "unknown argument '%s'" % name
        parg = self._argmap[name]
        if parg.type != None:
            # XXX: autocast?
            value = parg.type(value)
        self._args[name] = value

    def __getattr__(self, key):
        if key in self._argmap:
            return self.get_argument(key)
        return super(Process, self).__getattr__(key)

    def __setattr__(self, key, val):
        if key in self._argmap:
            return self.set_argument(key, val)
        super(Process, self).__setattr__(key, val)

    def cli_arguments(self, **kw):
        _args = self._args.copy()
        _args.update(kw)
        #
        cli = []
        for parg in self.Arguments:
            if parg.name in _args:
                if parg.argument == None:
                    cli.append("%s" % _args[parg.name])
                elif parg.type == bool and _args[parg.name]:
                    cli.append(parg.argument)
                else:
                    cli.append(parg.argument)
                    cli.append("%s" % _args[parg.name])
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

    @property
    def subprocess_options(self):
        opts = {}
        for (key, val) in self.ProcessOptions.iteritems():
            if type(val) in (str, unicode):
                if val.lower() == "pipe":
                    val = subprocess.PIPE
            opts[key] = val
        return opts

    def execute(self, **kw):
        cli = self.cli(**kw)
        self.proc = subprocess.Popen(cli, **self.subprocess_options)
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
