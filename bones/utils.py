import os
import sys
import uuid
import time
import glob

__all__ = ["is_stale", "common_filename", "touch", "temp_filename", "assert_status_code", "which", "verify_link", "symlink"]

def verify_link(source, target):
    try:
        return os.readlink(target) == source
    except OSError:
        pass
    return False

def symlink(source, directory):
    if not source:
        return None
    source = os.path.abspath(source)
    (path, filename) = os.path.split(source)
    target = os.path.join(directory, filename)
    if source == target:
        return target
    if not verify_link(source, target):
        try:
            os.symlink(source, target)
        except Exception as err:
            message = "Failed to symlink source '%s' to target '%s' (%s)" % (source, target, err)
            raise RuntimeError(message)
    return target

def is_stale(source_glob, target_glob):
    no_content = True
    for target_fn in glob.glob(target_glob):
        for source_fn in glob.glob(source_glob):
            no_content = False
            if not os.path.exists(target_fn):
                return True
            source_mtime = os.path.getmtime(source_fn)
            target_mtime = os.path.getmtime(target_fn)
            if source_mtime > target_mtime:
                return True
    return no_content

def common_filename(*filenames):
    idx = 0
    while True:
        try:
            chars = set([fn[idx] for fn in filenames])
        except IndexError:
            break
        if len(chars) != 1:
            break
        idx += 1
    return filenames[0][:idx]

def touch(fn, mtime=None, atime=None):
    if mtime or atime:
        mtime = mtime if mtime != None else time.time()
        atime = atime if atime != None else time.time()
        times = (atime, mtime)
    else:
        times = None
    with open(fn, 'a'):
        os.utime(fn, times)

def temp_filename(prefix='', postfix='', ext=''):
    tmpfn = str(uuid.uuid4())
    if ext and ext[0] != '.':
        ext = '.' + ext
    tmpfn = prefix + tmpfn + postfix + ext
    return tmpfn

def assert_status_code(resp, expected_status_code=200, msg=''):
    if resp.status_code == expected_status_code:
        return
    if msg == None:
        msg = "%s request to '%s' did not return the expected status code (%d instead of %d)" % (resp.request.method, resp.request.url, resp.status_code, expected_status_code)
    raise RuntimeError(msg)

def which(program):
    if not program:
        raise ValueError("program cannot be a null string")
    def is_qualified_exe(fpath):
        return len(os.path.split(fpath)[0]) and os.path.isfile(fpath) and os.access(fpath, os.X_OK)
    if is_qualified_exe(program):
        return program
    program = os.path.split(program)[-1]
    if sys.platform == "darwin":
        bg1 = "/Applications/%s/%s.app/Contents/MacOS/%s" % (program, program, program)
        bg2 = "/Applications/%s.app/Contents/MacOS/%s" % (program, program)
        for best_guess in (bg1, bg2):
            if is_qualified_exe(best_guess):
                return best_guess
    for path in os.environ["PATH"].split(os.pathsep):
        path = path.strip('"')
        best_guess = os.path.join(path, program)
        if is_qualified_exe(best_guess):
            return best_guess
