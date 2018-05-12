import itertools

def runIter(run, iterable, padding=None):
    it = iter(iterable)
    while True:
        currentRun = list(itertools.islice(it, run))
        lcr = len(currentRun)
        if lcr == 0:
            break
        yield currentRun + [padding] * (run - lcr)

