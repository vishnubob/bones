from .. package import Package

class PackagesBones(Package):
    PackageName = "bones"
    Depends = {
        "dpkg": ["git", "build-essential", "python-dev", "python-pip", "python-setuptools", "samtools"],
        "packages": ["pysam"],
    }
    Version = "v0.0.1"
    Entrypoint = "/bones/entrypoint.sh"

    def script(self):
        script = [
            "git clone https://github.com/vishnubob/bones.git /bones",
            "cd /bones",
            "python setup.py install",
            "chmod 755 /bones/entrypoint.sh"
        ]
        return script
