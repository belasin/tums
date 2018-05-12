#!/usr/bin/python
"""Processes a list of wav files and merges them to make a single mp3 file using sox"""
#-m -v 1 $LEFT-tmp.wav -v 1 $RIGHT-tmp.wav $OUT.mp3 
import os, traceback
import sys

soxcmd = """/usr/bin/sox -m -v 1 %(path)stmp_%(sub)s/%(left)s.wav -v 1 %(path)stmp_%(sub)s/%(right)s.wav %(path)s%(sub)s/%(out)s.wav"""
infileT = """%(path)stmp_%(sub)s/%(left)s.wav"""
oufileT = """%(path)stmp_%(sub)s/%(right)s.wav"""
mxfileT = """%(path)s%(sub)s/%(out)s.wav"""

recpath = "/var/lib/samba/data/vRecordings/"
subDirList = ["inbound","outbound"]
tmpPref = "tmp_"

def remixFile(infile, outfile, mixfile, sub):
    data = {
        "path": recpath,
        "sub": sub,
        "left": infile,
        "right": outfile,
        "out": mixfile
    }

    c = soxcmd % data
    if not os.path.exists(mxfileT % data):
        os.system(c)
    if os.path.exists(mxfileT % data):
        os.system("rm "+infileT % data)
        os.system("rm "+oufileT % data)

def procDir(directory, sub):
    dirList = os.listdir(directory)
    fileList = []
    for i in dirList:
        if "-in.wav" == i[-7:]:
            file = i[:-7]
        else:
            file = i[:-8]
        if len(sys.argv) > 1:
            if sys.argv[1] in sub+"/"+file and file not in fileList:
                fileList.append(file)
        elif file not in fileList:
            fileList.append(file)
    for i in fileList:
        if ".wav" == i[-4:]:
            newfilename = i[:-4]
        else:
            newfilename = i
        remixFile(i+"-in", i+"-out", newfilename, sub)

def scanDirs():
    for sub in subDirList:
        try:
            procDir(recpath+tmpPref+sub,sub)
        except:
            print "Error: %s" % traceback.format_exc()

scanDirs()
