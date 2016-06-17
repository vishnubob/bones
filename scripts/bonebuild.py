#!/usr/bin/env python

import bones
import sys
import os
import argparse
import json
from bones.packages import __packages__

def get_cli():
    pkglist = list(__packages__) + ["all"]
    parser = argparse.ArgumentParser(description="Image builder for bones")
    parser.add_argument('--mode', '-m', default="shell", choices=["shell", "docker", "build"], help="[shell|docker]")
    parser.add_argument('packages', nargs='*', default="all", choices=pkglist, help="[%s]" % pkglist)
    args = parser.parse_args()
    return args

class DockerBuild(bones.package.DockerScriptInstaller):
    def build(self):
        from docker import Client
        from io import BytesIO
        dockerhost = os.environ.get("DOCKER_HOST", "tcp://127.0.0.1:2375")
        dockerfile = super(DockerBuild, self).build()
        dockerfile = BytesIO(dockerfile.encode('utf-8'))
        cli = Client(dockerhost)
        builder = cli.build(fileobj=dockerfile, rm=True, tag="bones")
        for line in builder:
            line = json.loads(line)
            if len(line.keys()) == 1 and "stream" in line:
                sys.stdout.write(line["stream"])
                sys.stdout.flush()
            else:
                print(line)

def build(args):
    if args.mode == "shell":
        installer = bones.package.ShellScriptInstaller
    elif args.mode == "docker":
        installer = bones.package.DockerScriptInstaller
    elif args.mode == "build":
        installer = DockerBuild
    else:
        msg = "unsupported mode '%s'" % args.mode
        raise ValueError(msg)
    if "all" in args.packages:
        packages = __packages__.values()
    else:
        packages = [__packages__[name] for name in args.packages]
    installer = installer(packages)
    script = installer.build()

if __name__ == "__main__":
    args = get_cli()
    build(args)
