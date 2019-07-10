import logging
import os.path
from collections import Counter
import math

import settings
import common as CM
logger = CM.getLogger(__name__, settings.loggingLevel)

def analyze(covSrc, goodInps, badInps, alg, tmpdir):
    assert os.path.isfile(covSrc), src
    assert goodInps, goodInps
    assert badInps, badInps
    assert isinstance(alg, int), alg
    assert os.path.isdir(tmpdir), tmpdir

    #compile
    covExe = "{}.exe".format(covSrc)
    cmd = "clang {} -o {}".format(covSrc, covExe)
    logger.debug(cmd)
    _, errMsg = CM.vcmd(cmd)
    assert "error" not in errMsg, errMsg
    assert os.path.isfile(covExe)
    
    pathFile = "{}.path".format(covSrc)
    goodSids, badSids = collectCov(covExe, pathFile, goodInps, badInps)

    goodNRuns, goodFreqs = analyzeCovs(goodSids)
    badNRuns, badFreqs = analyzeCovs(badSids)
    assert badNRuns == len(badInps)
    sscores = getSuspScores(goodNRuns, goodFreqs, badNRuns, badFreqs, alg)
    return sscores
    
def collectCov(covExe, pathFile, goodInps, badInps):
    assert os.path.isfile(covExe), covExe
    assert isinstance(goodInps, set) and goodInps, goodInps
    assert isinstance(badInps, set) and badInps, badInps

    def run(inps):
        if os.path.isfile(pathFile):
            os.remove(pathFile)
            
        inpStrs = [" ".join(map(str, inp)) for inp in inps]
        cmds = ["{} {}".format(covExe, inpStr) for inpStr in inpStrs]
        for cmd in cmds:
            outMsg, errMsg = CM.vcmd(cmd)
            assert not errMsg

        assert os.path.isfile(pathFile)
        sids = [int(sid) for sid in CM.iread(pathFile) if sid]
        return sids

    goodSids = run(goodInps)
    badSids = run(badInps)
    
    return goodSids, badSids

def analyzeCovs(sids):
    assert all(isinstance(sid, int) for sid in sids) and sids, sids
    freqs = Counter()
    nruns = 0
    
    import itertools
    for k, g in itertools.groupby(sids, key=lambda x: x != 0):
        if not k: continue
        nruns += 1
        for sid in g:
            freqs[sid] += 1   

    return nruns, freqs
    
def getSuspScores(goodNRuns, goodFreqs, badNRuns, badFreqs, alg):
    assert goodNRuns >= 1, goodNRuns
    assert isinstance(goodFreqs, Counter), goodFreqs
    
    assert badNRuns >= 1, badNRuns
    assert isinstance(badFreqs, Counter), badFreqs

    sids = set(list(goodFreqs) + list(badFreqs))

    if alg == 0:
        logger.debug("fault localize using Ochiai")
        falg = algOchiai
    else:
        logger.debug("fault localize using Tarantula")        
        falg = algTarantula
    f = lambda sid: falg(goodNRuns, goodFreqs[sid], badNRuns, badFreqs[sid])
    scores = Counter({sid: f(sid) for sid in sids})
    #print scores.most_common(10)
    
    return scores
    
def algTarantula(goodNRuns, goodOccurs, badNRuns, badOccurs):
    a = float(badOccurs) / badNRuns
    b = float(goodOccurs) / goodNRuns
    c = a + b
    return a / c if c else 0.0

def algOchiai(goodNruns, goodOccurs, badNRuns, badOccurs):
    c = math.sqrt(badOccurs * goodOccurs)
    return badNRuns / c if c else 0.0
    