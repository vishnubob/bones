import os
import sys
import inspect

"""
    apt-get update 
    apt-get install -y \
        build-essential \
        git \
        default-jre-headless \
        zlib1g-dev \
        unzip \
        wget \
        python-dev \
        python-pip \
        samtools \
        libcurl4-openssl-dev
    mkdir $SOURCE_DIR
"""

class PackageInstaller(object):
    def __init__(self, packages, **args):
        self.packages = packages
        self.args = args

    def build(self, pkgcls):
        pkg = pkgcls(**self.args)
        script = pkg.script

    def depends(self, key):
        deps = set()
        for pkg in self.packages:
            for cls in ((pkg, ) + pkg.__mro__):
                depends = cls.__dict__.get("Depends")
                if depends == None:
                    continue
                deps.update(depends.get(key, []))
        return list(deps)

    def dpkg_depends(self):
        dpkg_list = self.depends("dpkg")
        cmd = None
        if dpkg_list:
            cmd = "apt-get update && apt-get -y install %s" % str.join(' ', dpkg_list)
        return cmd

class ShellScriptInstaller(PackageInstaller):
    def build(self):
        script = ''
        for pkgcls in self.packages:
            pkg = pkgcls(**self.args)
            cmds = pkg.script()
            env = pkg.environment()
            env = ["%s=%s" % kv for kv in env.items()]
            env = str.join('\n', env) + '\n'
            script += env
            script += str.join('\n', cmds)
        return script

class DockerScriptInstaller(PackageInstaller):
    DockerTemplate = [
        "FROM ubuntu:14.04",
        "%s",
    ]

    def build(self):
        script = ''
        dpkg_cmd = self.dpkg_depends()
        if dpkg_cmd:
            script += "RUN " + dpkg_cmd + '\n'
        for pkgcls in self.packages:
            pkg = pkgcls(**self.args)
            script += "# %s\n" % pkg.PackageName
            env = pkg.environment()
            cmds = ["%s=%s" % kv for kv in env.items()] + pkg.preinstall_hook() + pkg.script() + pkg.postinstall_hook()
            cmds = "RUN " + str.join(" && \\\n    ", cmds) + '\n'
            script += cmds
        script = str.join('\n', self.DockerTemplate) % script
        return script

class Package(object):
    Name = "__package__"
    Depends = {
        "dpkg": [],
        "pip": []
    }
    Version = ""

    def __init__(self, prefix="/usr/local", srcdir="/tmp/src"):
        self.prefix = prefix
        self.bindir = os.path.join(self.prefix, "bin")
        self.libdir = os.path.join(self.prefix, "lib")
        self.sharedir = os.path.join(self.prefix, "share")
        self.srcdir = srcdir

    def preinstall_hook(self):
        return ["mkdir ${PKG_SRCDIR}"]

    def postinstall_hook(self):
        return []

    def environment(self):
        env = {
            "PKG_SRCDIR": self.srcdir,
            "PKG_BINDIR": self.bindir,
            "PKG_LIBDIR": self.libdir,
            "PKG_SHAREDIR": self.sharedir,
            "PKG_PREFIX": self.prefix,
            "PKG_VERSION": self.Version,
        }
        return env

    def script(self):
        pass

class BonesPackage(Package):
    PackageName = "bones"
    Depends = {
        "dpkg": ["git", "build-essential"],
        "pip": ["pysam", "celery", "requests"]
    }
    Version = "master"

    def script(self):
        script = [
            "pip install https://github.com/vishnubob/ssw/archive/master.zip",
        ]
        return script

def collect_packages():
    thismodule = sys.modules[__name__]
    ns = thismodule.__dict__
    _all = ns.get("__all__", list())
    for key in ns.keys():
        cls = ns[key]
        if inspect.isclass(cls) and issubclass(cls, Package) and (cls.__name__ != "Package"):
            ns[cls.Name] = cls()
            _all.append(cls.TaskName)
    ns["__all__"] = _all

#collect_packages()
