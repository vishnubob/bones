import os
import operator
import subprocess

__all__ = ["Process"]

class ProcessArgument(object):
    def __init__(self, name=None, argument=None, type=None, default=None, required=False, help=None):
        self.name = name
        self.argument = argument
        self.type = type
        self.default = default
        self.required = required
        self.help = help

class ProcessMetaclass(type):
    def __new__(cls, name, parents, dct):
        argmap = dct.get("_argmap", {})
        for parg in dct["Arguments"]:
            argmap[parg.name] = parg
        dct["_argmap"] = argmap
        return super(InterfaceMeta, cls).__new__(cls, name, parents, dct)

class Process(object):
    Command = "__command__"
    ProcessOptions = {}
    Arguments = []
    ReturnCode = 0
    __metaclass__ = ProcessMetaclass

    def __init__(self, command_path=None, **args):
        command_path = command_path if command_path != None else self.Command
        command_path = which(command_path)
        self.command_path = command_path
        # make local copies
        self._args = {}
        for (key, val) in args:
            self.set_argument(key, val)

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

    def build_command_line(self, **kw):
        _args = self._args.copy()
        _args.update(kw)
        #
        cli = [self.command_path]
        for (name, parg) in self._argmap.items():
            if name in _args:
                if parg.type == "bool" and _args[name]:
                    cli.append(parg.argument)
                else:
                    cli.append(parg.argument)
                    cli.append("%r" % _args[name])
            elif parg.required:
                if parg.type == "bool" and parg.default:
                    cli.append(parg.argument)
                else:
                    cli.append(parg.argument)
                    cli.append("%r" % parg.default)
        return cli

    def execute(self, **kw):
        cmd = self.command(**kw)
        self.proc = subprocess.Popen(cmd, **self.ProcessOptions)
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
