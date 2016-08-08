import os
import boto
import uuid
import time
import math
import sys
from datetime import datetime
import flywheel
import fnmatch
from flywheel import Model, Field
from bones.aws.s3.tar import tar, untar

class Engine(flywheel.Engine):
    def register(self, *models):
        super(Engine, self).register(*models)
        for model in models:
            model.__engine__ = self

class IlluminaSample(Model):
    __metadata__ = {
        "_name": "_illumina_sample",
        "throughput": {
            "read": 10,
            "write": 10,
        }
    }

    id = Field(hash_key=True)
    run_id = Field(range_key=True)
    samples = Field(data_type=list)

    @classmethod
    def from_sample(cls, **kw):
        kw["id"] = kw["Sample_ID"]
        instance = cls(**kw)
        instance.save()
        return instance

class IlluminaRun(Model):
    __metadata__ = {
        "_name": "_illumina_run",
        "throughput": {
            "read": 10,
            "write": 10,
        }
    }

    id = Field(hash_key=True)
    samples = Field(data_type=list)

    @classmethod
    def from_directory(cls, rundir, bucket):
        dd = illumina.DataDirectory(rundir)
        return from_data_directory(dd, bucket)

    @classmethod
    def from_data_directory(cls, dd, bucket, prefix="runs/"):
        fileref = cls.upload_library(dd, bucket, prefix=prefix)
        runinfo = dict(dd.runinfo)
        runinfo["Date"] = str(runinfo["Date"])
        samples = []
        run_id = dd.runinfo["Run"]["Id"]
        for sample in dd.sample_sheet.data:
            sample = IlluminaSample.from_sample(run_id=run_id, **sample)
            samples.append(sample.id)
        kw = {
            "id": run_id,
            "samples": samples
        }
        kw.update(runinfo)
        instance = cls(**kw)
        # file
        fileref["id"] = run_id
        FileReference(**fileref)
        instance.save()
        return instance

    @classmethod
    def upload_library(cls, dd, bucket, prefix=""):
        filter_list = ["*.fastq.*"]
        def filter_callback(filename):
            for pattern in filter_list:
                if fnmatch.fnmatch(filename, pattern):
                    return False
            return True
        runid = dd.runinfo["Run"]["Id"]
        filename = "%s.tar.gz" % runid
        key = os.path.join(prefix, filename)
        obj = bucket.Object(key)
        total_size = tar(obj, dd.root, arcpath=runid + '/', callback=filter_callback)
        return {"key": key, "bucket": bucket.name, "filename": filename, "size": total_size}

    def download_library(self, path): 
        if not os.path.exists(path):
            os.makedirs(path)
        fileobj = self.__engine__.query(FileReference).filter(FileReference.id == self.id).first()
        bucket = boto3.resource("s3").Bucket(fileobj.bucket)
        obj = bucket.Object(fileobj.key)
        total_size = untar(obj, path)
        return total_size

    def populate_library(dd):
        models.IlluminaRun.from_data_directory(dd)

class FileReference(Model):
    __metadata__ = {
        "_name": "_file_reference",
        "throughput": {
            "read": 10,
            "write": 10,
        }
    }

    key = Field(hash_key=True)
    bucket = Field(range_key=True, nullable=False)
    tags = Field(data_type=set)
    size = Field(data_type=int)
    filename = Field()
    digest = Field()
    id = Field()

    @classmethod
    def add_file(cls, **kw):
        instance = cls.__init__(**kw)
        instance.save()
        return instance

engine = Engine()
engine.connect_to_region("us-east-1")
models = [IlluminaRun, IlluminaSample, FileReference]
engine.register(*models)
engine.create_schema()
