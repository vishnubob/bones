from .. package import Package

class PackagesPySAM(Package):
    PackageName = "pysam"
    Depends = {
        "dpkg": ["git", "build-essential", "python-dev", "python-pip", "python-setuptools", "libcurl4-openssl-dev"],
    }
    Version = "v0.9.1"

    def script(self):
        script = [
            "pip install cython",
            "git clone -b ${PKG_VERSION} https://github.com/pysam-developers/pysam.git ${PKG_SRCDIR}/pysam",
            "cd ${PKG_SRCDIR}/pysam",
            "python setup.py install",
        ]
        return script
