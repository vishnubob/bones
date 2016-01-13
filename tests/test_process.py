#!/usr/bin/env python

import os
import unittest
import time
from bones.process import *

class EchoCommand(Process):
    Command = "echo"
    ProcessOptions = {"stdout": "pipe"}
    Arguments = [
        ProcessArgument(name="content", type=str, help="Echo content"),
    ]

class WordCountCommand(Process):
    Command = "wc"
    ProcessOptions = {"stdout": "pipe", "stdin": "pipe"}
    Arguments = [
        ProcessArgument(name="char_count", argument="-c", type=bool, default=False, help="Character count")
    ]

class GenericCommand(Process):
    Command = "echo"
    ProcessOptions = {"stdout": "pipe"}
    Arguments = [
        ProcessArgument(name="arg1", argument="-a", type=int, default=1, required=True, help="Argument 1"),
        ProcessArgument(name="arg2", argument="-x", type=bool, default=False, help="Argument 2"),
        ProcessArgument(name="content", type=str, help="Echo content"),
    ]

class TestProcess(unittest.TestCase):
    def test_flag_args(self):
        cmd = GenericCommand()
        args = cmd.cli()
        self.assertEquals(os.path.split(args[0])[-1], "echo")
        self.assertEquals(args[1:], ["-a", "1"])
        args = cmd.cli(arg2=True)
        self.assertEquals(args[1:], ["-a", "1", "-x"])

    def test_attribute_interface(self):
        cmd = GenericCommand()
        self.assertEquals(cmd.arg1, 1)
        cmd.arg1 = 2
        self.assertEquals(cmd.arg1, 2)
        cmd.arg1 = "3"
        self.assertEquals(cmd.arg1, 3)

    def test_position_args(self):
        cmd = GenericCommand(content="this is a test")
        args = cmd.cli()
        self.assertEquals(args[1:], ["-a", "1", "this is a test"])

    def test_execution(self):
        cmd = EchoCommand(content="this is a test")
        proc = cmd()
        output = proc.stdout.read()
        proc.wait()
        self.assertEquals(output, "this is a test\n")

    def test_pipe(self):
        cmd1 = EchoCommand(content="this is a test")
        cmd2 = WordCountCommand(char_count=True)
        proc1 = cmd1()
        proc2 = cmd2()
        proc2.stdin.write(proc1.stdout.read())
        proc2.stdin.close()
        output = proc2.stdout.read()
        proc1.wait()
        proc2.wait()
        self.assertEquals(output, "15\n")

if __name__ == '__main__':
    unittest.main()
