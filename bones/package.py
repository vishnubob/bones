import os
import sys
import inspect

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
            deps.update(pkg.get_depends(key))
        return list(deps)

    def dpkg_depends(self):
        dpkg_list = self.depends("dpkg")
        cmd = None
        if dpkg_list:
            cmd = "apt-get update && apt-get -y install %s" % str.join(' ', dpkg_list)
        return cmd

    @property
    def build_order(self):
        from bones.packages import __packages__
        deps = [__packages__.get(name) for name in self.depends("packages")]
        packages = list(set(deps + self.packages))
        packages.sort(reverse=True)
        build_order = []
        while packages:
            # XXX: unresolved depends graphs can cause an
            #       infinite loop.
            pkg = packages.pop()
            requires = pkg.get_depends("packages")
            provided = [ppkg.PackageName for ppkg in build_order]
            if requires and (set(requires) - set(provided)):
                # package still has outstanding deps, continue
                packages.insert(0, pkg)
                continue
            build_order.append(pkg)
        return build_order

class ShellScriptInstaller(PackageInstaller):
    def build(self):
        script = ''
        for pkgcls in self.build_order:
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
        for pkgcls in self.build_order:
            entrypoint = getattr(pkgcls, "Entrypoint", None)
            if entrypoint:
                script += "ENTRYPOINT %s\n" % entrypoint
            pkg = pkgcls(**self.args)
            script += "# %s\n" % pkg.PackageName
            env = pkg.environment()
            cmds = ["%s=%s" % kv for kv in env.items()] + pkg.preinstall_hook() + pkg.script() + pkg.postinstall_hook()
            cmds = "RUN " + str.join(" && \\\n    ", cmds) + '\n'
            script += cmds
        script = str.join('\n', self.DockerTemplate) % script
        return script

class Package(object):
    PackageName = "__package__"
    Depends = {
        "dpkg": [],
        "pip": [],
        "packages": [],
    }
    Version = ""

    def __init__(self, prefix="/usr/local", srcdir="/tmp/src"):
        self.prefix = prefix
        self.bindir = os.path.join(self.prefix, "bin")
        self.libdir = os.path.join(self.prefix, "lib")
        self.sharedir = os.path.join(self.prefix, "share")
        self.srcdir = srcdir

    @classmethod
    def get_depends(cls, key):
        deps = set()
        for cls in ((cls, ) + cls.__mro__):
            depends = cls.__dict__.get("Depends", {})
            deps.update(depends.get(key, []))
        return list(deps)

    def preinstall_hook(self):
        return ["if [ ! -d ${PKG_SRCDIR} ]; then mkdir ${PKG_SRCDIR}; fi"]

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
