#!/usr/bin/env python
import sys
import warnings

#from obspy.clients.fdsn.header import FDSNNoDataException
#from numpy import median
#import collections
import numpy as np
import collections

import argparse

parser = argparse.ArgumentParser(description='read in RESP and recalculate a0 and overall sensitivity at given frequency ')

parser.add_argument("-lf", action="store", dest="LowFreqRespFile",
                    required=True, help="Low Frequency Resp file")
parser.add_argument("-hf", action="store", dest="HighFreqRespFile",
                    required=True, help="High Frequency Resp file")
parser.add_argument("-of", action="store", dest="OutputRespFile",
                    default="RESP.out", help="Output Resp file (default is RESP.out)")
parser.add_argument("-freq", action="store", dest="StitchFreq",
                    default=1,  help="Frequency to stitch low and high together around (default is 1Hz)")

args = parser.parse_args()
lfil = args.LowFreqRespFile
hfil = args.HighFreqRespFile
ofil = args.OutputRespFile
freq= np.float(args.StitchFreq)

zdict = collections.defaultdict(dict)
pdict = collections.defaultdict(dict)

fl=open(lfil,mode='r')

zn=-1
pn=-1
for line in fl:
    blks = line.split()
    if  ("B053F10" in blks[0]) or ("B053F15" in blks[0]):
        zf = np.sqrt(np.float(blks[2])**2+np.float(blks[3])**2)/(2*np.pi)
        if ("B053F10-13" in blks[0]) and (zf < freq):
            zn=zn+1
            zdict[zn]=blks[2:]
        elif "B053F15-18" in blks[0] and (zf < freq):
            pn=pn+1
            pdict[pn]=blks[2:]
fl.close()

fl=open(hfil,mode='r')

for line in fl:
    blks = line.split()
    if  ("B053F10" in blks[0]) or ("B053F15" in blks[0]):
        zf = np.sqrt(np.float(blks[2])**2+np.float(blks[3])**2)/(2*np.pi)
        if ("B053F10-13" in blks[0]) and (zf > freq):
            zn=zn+1
            zdict[zn]=blks[2:]
        elif "B053F15-18" in blks[0] and (zf > freq):
            pn=pn+1
            pdict[pn]=blks[2:]
fl.close()
    
zout=0
pout=0

fl=open(lfil,mode='r')
fo=open(ofil,mode='w')
for line in fl:
    blks = line.split()
    if ("B053F10-13" in blks[0]) and (zout==0):
        zout=1
        for zn in zdict:
            #print(zdict[zn])
            zz=np.asarray(zdict[zn],dtype=np.float64)
            fo.write("B053F10-13    %i  %6.5E   %6.5E  %6.5E  %6.5E\n"%(np.int(zn),zz[0],zz[1],zz[2],zz[3]))
        
    elif "B053F15-18" in blks[0] and (pout==0):
        pout=1
        for zn in pdict:
            zz=np.asarray(pdict[zn],dtype=np.float64)
            fo.write("B053F15-18    %i  %6.5E   %6.5E  %6.5E  %6.5E\n"%(np.int(zn),zz[0],zz[1],zz[2],zz[3]))
    elif ("B053F15-18" not in blks[0]) and ("B053F10-13" not in blks[0]):
        fo.write(line)
        
fl.close()
fo.close()

