from datetime import datetime
import xml.etree.ElementTree as ET
import os
import re
import glob

__all__ = ["SampleSheet", "Sample", "DataDirectory", "RunInfo"]

class DataDirectory(object):
    def __init__(self, root):
        self.root = root
        self.sample_sheet = SampleSheet(self.sample_sheet_path)
        self.samples = [Sample(self, data) for data in self.sample_sheet.data]
        self.runinfo = RunInfo(self.runinfo_path)
        # undetermined reads
        stub = self.sample_sheet.sample_stub
        stub["Sample_ID"] = "Undetermined"
        self.undetermined = Sample(self, stub)

    @property
    def runinfo_path(self):
        return os.path.join(self.root, "RunInfo.xml")

    @property
    def sample_sheet_path(self):
        return os.path.join(self.root, "SampleSheet.csv")

    @property
    def basecalls_path(self):
        return os.path.join(self.root, "Data/Intensities/BaseCalls")

class RunInfo(dict):
    def __init__(self, filepath):
        self.doc = ET.parse(filepath)
        self.parse()

    def parse(self):
        root = self.doc.getroot()
        run = root.find("Run")
        self["Run"] = {"Id": run.attrib["Id"], "Number": int(run.attrib["Number"])}
        self["Flowcell"] = run.find("Flowcell").text
        self["Instrument"] = run.find("Instrument").text
        self["Date"] = datetime.strptime(run.find("Date").text, "%y%m%d")
        self["Reads"] = []
        for read in run.find("Reads").iter("Read"):
            read = {
                "NumCycles": int(read.attrib["NumCycles"]),
                "Number": int(read.attrib["Number"]),
                "IsIndexedRead": (read.attrib["IsIndexedRead"].upper() == 'Y'),
            }
            self["Reads"].append(read)
        self["FlowcellLayout"] = {key: int(val) for (key, val) in run.find("FlowcellLayout").attrib.items()}

    @property
    def read_structure(self):
        chapter = lambda read: "%s%s" % (read["NumCycles"], 'B' if read["IsIndexedRead"] else 'T')
        return str.join('', [chapter(read) for read in self["Reads"]])

class SampleSheet(object):
    re_header = re.compile("^\[(\w+)\].*")

    def __init__(self, filename):
        self.filename = filename
        self.initialize()
        self.parse()

    def initialize(self):
        self.header = {}
        self.reads = ()
        self.settings = {}
        self.data = []
        self.data_header = []

    def parse(self):
        with open(self.filename) as ss:
            current_header = None
            for line in ss:
                line = line.strip()
                if not line:
                    continue
                m = self.re_header.match(line)
                if m:
                    current_header = m.group(1)
                    continue
                assert current_header != None, "Expected header before content (%s)" % line 
                fname = "parse_%s" % current_header.lower()
                func = getattr(self, fname, None)
                assert func != None, "Unexpected header '%s'" % current_header
                func(line)

    def _parse_keyval(self, line):
        keyval = line.split(',')[:2]
        assert len(keyval) in (1, 2), "Expected one or two values, got %d (%s)" % (len(keyval), line)
        if len(keyval) == 1:
            keyval.append(None)
        return keyval

    def parse_header(self, line):
        (key, val) = self._parse_keyval(line)
        assert key not in self.header, "Found duplicate key '%s' in header" % key
        self.header[key] = val

    def parse_reads(self, line):
        value = line.split(',')[0]
        read_length = int(value)
        self.reads = self.reads + (read_length, )

    def parse_settings(self, line):
        (key, val) = self._parse_keyval(line)
        assert key not in self.settings, "Found duplicate key '%s' in header" % key
        self.settings[key] = val

    def parse_data(self, line):
        row = line.split(',')
        if not self.data_header:
            self.data_header = row
        else:
            row = [val if val else None for val in row]
            pad = len(self.data_header) - len(row)
            assert pad >= 0, "There are more columns in data line than the header"
            row += [None] * pad
            row = dict(zip(self.data_header, row))
            self.data.append(row)

    @property
    def sample_stub(self):
        return dict([(key, None) for key in self.data_header])

class Sample(object):
    def __init__(self, datadir, data):
        self.datadir = datadir
        self.data = data
        self.id = self.data["Sample_ID"]
        self.name = self.data["Sample_Name"]
        self.glob_pattern = os.path.join(self.datadir.basecalls_path, "*%s*.fastq*" % self.id)
        self.files = glob.glob(self.glob_pattern)
        self.files.sort()

    @property
    def reads(self):
        return tuple(self.files)
