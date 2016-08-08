import threading
import multiprocessing
import time
import tarfile
import os
from bones import log

logger = log.get_logger(__name__)

class TarProcessor(object):
    class TarThread(threading.Thread):
        def __init__(self, mode='r', pipes=None, *args, **kw):
            self.pipes = pipes
            self._tarfile = None
            self.mode = mode
            if 'r' in self.mode:
                target = self.extract
            elif 'w' in self.mode:
                target = self.archive
            kw["target"] = target
            super(TarProcessor.TarThread, self).__init__(*args, **kw)
            self.daemon = True

        def f_arcpath(self, root, arcpath, path):
            return os.path.join(arcpath, os.path.relpath(path, root))

        @property
        def tarfile(self):
            if self._tarfile != None:
                return self._tarfile
            if 'r' in self.mode:
                self._tarfile = tarfile.open(mode=self.mode, fileobj=self.pipes[0])
            elif 'w' in self.mode:
                self._tarfile = tarfile.open(mode=self.mode, fileobj=self.pipes[1])
            else:
                raise ValueError("unknown mode `%s`" % self.mode)
            return self._tarfile

        def archive(self, path=".", arcpath=None, callback=None):
            f_callback = callback if callback != None else (lambda fn: True)
            f_arcpath = (lambda _path: self.f_arcpath(path, arcpath, _path)) if arcpath != None else (lambda x: x)
            for (root, dirs, files) in os.walk(path):
                files = [(_path, f_arcpath(_path)) for _path in filter(f_callback, [os.path.join(root, f) for f in files])]
                for (_path, _arcpath) in files:
                    msg = "Archiving `%s` as `%s`" % (_path, _arcpath)
                    logger.debug(msg)
                    self.tarfile.add(_path, arcname=_arcpath)
            self.tarfile.close()
            self.pipes[1].close()

        def extract(self, path="."):
            self.tarfile.extractall(path=path)

    class TransportThread(threading.Thread):
        def __init__(self, mode='r', pipes=None, *args, **kw):
            self.pipes = pipes
            self.mode = mode
            if 'r' in self.mode:
                target = self.download
            elif 'w' in self.mode:
                target = self.upload
            kw["target"] = target
            super(TarProcessor.TransportThread, self).__init__(*args, **kw)
            self.daemon = True
            self.callback_refresh_ts = None
            self.callback_refresh_rate = 30
            self.total_size = 0

        def download(self, object=None):
            # untar
            object.download_fileobj(self.pipes[1], Callback=self.callback)
            self.pipes[1].close()

        def upload(self, object=None):
            # tar
            object.upload_fileobj(self.pipes[0], Callback=self.callback)

        def callback(self, byte_count):
            if self.callback_refresh_ts == None:
                self.callback_byte_count = 0
                self.callback_refresh_ts = time.time() + self.callback_refresh_rate
            self.callback_byte_count += byte_count
            self.total_size += byte_count
            now = time.time()
            if now > self.callback_refresh_ts:
                value = (self.callback_byte_count / 1e6) / self.callback_refresh_rate
                self.callback_byte_count = 0
                self.callback_refresh_ts = now + self.callback_refresh_rate
                prefix = "MB"
                msg = "%.02f%s/s" % (value, prefix)
                logger.info(msg)

    def get_pipe(self):
        (read_pipe, write_pipe) = os.pipe()
        read_pipe = os.fdopen(read_pipe)
        write_pipe = os.fdopen(write_pipe, 'w')
        return (read_pipe, write_pipe)

    def untar(self, s3obj, path, mode="r|gz"):
        if not os.path.exists(path):
            os.makedirs(path)
        pipes = self.get_pipe()
        tar_thread = self.TarThread(mode, pipes=pipes, kwargs={"path": path})
        transpo_thread = self.TransportThread(mode, pipes=pipes, kwargs={"object": s3obj})
        transpo_thread.start()
        tar_thread.start()
        msg = "extracting tar archive `%s` to `%s`" % (s3obj.key, path)
        logger.info(msg)
        while transpo_thread.isAlive():
            time.sleep(1)
        transpo_thread.join()
        tar_thread.join()
        return transpo_thread.total_size

    def tar(self, s3obj, path, arcpath=None, callback=None, mode="w|gz"):
        if path.startswith("/") and arcpath == None:
            arcpath = "/"
        pipes = self.get_pipe()
        tar_thread = self.TarThread(mode, pipes=pipes, kwargs={"path": path, "arcpath": arcpath, "callback": callback})
        transpo_thread = self.TransportThread(mode=mode, pipes=pipes, kwargs={"object": s3obj})
        tar_thread.start()
        transpo_thread.start()
        msg = "creating tar archive `%s` from `%s`" % (s3obj.key, path)
        logger.info(msg)
        while tar_thread.isAlive():
            time.sleep(1)
        tar_thread.join()
        transpo_thread.join()
        return transpo_thread.total_size

def tar(*args, **kw):
    tp = TarProcessor()
    return tp.tar(*args, **kw)

def untar(*args, **kw):
    tp = TarProcessor()
    return tp.untar(*args, **kw)
