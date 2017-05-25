import logging

# common #
import subprocess as sp
def vcmd(cmd, inp=None, shell=True):
    proc = sp.Popen(cmd,shell=shell,stdin=sp.PIPE,
                    stdout=sp.PIPE,stderr=sp.PIPE)
    return proc.communicate(input=inp)

def isCompile(src):
    cmd = "gcc {} -o {}.exe".format(src, src)
    logging.debug(cmd)
    outMsg, errMsg = vcmd(cmd)
    return not errMsg

def iread(filename):
    with open(filename, 'r') as fh:
        for line in fh:
            yield line