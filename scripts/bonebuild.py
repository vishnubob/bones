#!/usr/bin/env python

import bones
import argparse
from bones.packages import __packages__

def get_cli():
    pkglist = list(__packages__) + ["all"]
    parser = argparse.ArgumentParser(description="Image builder for bones")
    parser.add_argument('--mode', '-m', default="shell", choices=["shell", "docker"], help="[shell|docker]")
    parser.add_argument('packages', nargs='*', default="all", choices=pkglist, help="[%s]" % pkglist)
    args = parser.parse_args()
    return args

def build(args):
    if args.mode == "shell":
        installer = bones.package.ShellScriptInstaller
    elif args.mode == "docker":
        installer = bones.package.DockerScriptInstaller
    else:
        msg = "unsupported mode '%s'" % args.mode
        raise ValueError(msg)
    if "all" in args.packages:
        packages = __packages__.values()
    else:
        packages = [__packages__[name] for name in args.packages]
    installer = installer(packages)
    script = installer.build()
    print script

if __name__ == "__main__":
    args = get_cli()
    build(args)
