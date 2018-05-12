import os, sys, time

def exTest(testname):
    os.system('C:\\Python26\\python.exe C:\\tests\\test_%s.py' % testname)


# Update svn
os.system('svn up C:\\tests\\')

exTest(sys.argv[1])
