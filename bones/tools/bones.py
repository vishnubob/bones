from .. package import Package

class PackagesBones(Package):
    PackageName = "bones"
    Depends = {
        "dpkg": ["git", "build-essential", "python-dev", "python-pip", "python-setuptools"]
    }
    Version = "v0.0.1"

    def script(self):
        script = [
            "git clone https://github.com/vishnubob/bones.git ${PKG_SRCDIR}/bones",
            "cd ${PKG_SRCDIR}/bones",
            "python setup.py install",
        ]
        return script

