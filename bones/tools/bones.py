from .. package import Package

class PackagesBones(Package):
    PackageName = "bones"
    Depends = {
        "dpkg": ["git", "build-essential", "python-dev", "python-pip", "python-setuptools"],
        "packages": ["pysam"],
    }
    Version = "v0.0.1"
    Entrypoint = "/bones/entrypoint.sh"

    def script(self):
        script = [
            "git clone https://github.com/vishnubob/bones.git /bones",
            "cd ${PKG_SRCDIR}/bones",
            "python setup.py install",
            "chmod 755 /ebones/ntrypoint.sh"
        ]
        return script
