#!/usr/bin/env python
import sys
import warnings
from obspy import read, UTCDateTime, read_inventory
#from obspy.clients.fdsn.header import FDSNNoDataException
#from numpy import median
#import collections
import numpy as np
warnings.filterwarnings('ignore')

import argparse

parser = argparse.ArgumentParser(description='reads in RESP, and dump poles and zeros to a extended station xml ready for upload to SIS. retains error values.')

parser.add_argument("-f", action="store", dest="RespFile",
                    required=True, help="Resp file")
parser.add_argument("-key", action="store", dest="Key",
                    default='ZP_STSX', help="Key for PZ representation (default is ZP_STSX)")
parser.add_argument("-desc", action="store", dest="Title",
                    default='ASL calibration', help="PZ description (default is ASL calibration)")
parser.add_argument("-a", action="store", dest="Calca0",
                    default=True, help="recalculate a0? (default is True)")
#parser.add_argument("-t", action="store", dest="RespTime",
#                    default='2099-12-31',  help="Time in case there are multiple epochs (default is latest epoch)")
#parser.add_argument("-freq", action="store", dest="NormFreq",
 #                   default=999,  help="Normalization Frequency in Hz, default is the currently stated frequency")
freq=999

args = parser.parse_args()
fil = args.RespFile
#tt = args.RespTime
#freq= np.float(args.NormFreq)
desc = args.Title
key = args.Key
calcA=args.Calca0

def calc_a0(resp,f):
    pz=resp.get_paz()
    omega=2*np.pi*f
    a1=1
    for n in range(len(pz.zeros)):
        a1=a1*(1j*omega - pz.zeros[n])
    for n in range(len(pz.poles)):
        a1=a1/(1j*omega - pz.poles[n])
    a0= 1/np.abs(a1)
    return a0

try:
    xmlf = read_inventory(fil)
except:
    sys.exit("Couldn't read in file.")

# Check to see if there is more than one epoch
if len(xmlf[:][:][0]) >1:
    print('It looks like you have more than one channel on input. This could go horribly wrong.')
    sys.exit()

zdict=[]
pdict=[]

fl=open(fil,mode='r')

for line in fl:
    blks = line.split()
    if len(blks):
        if ("B053F07" in blks[0]):
            A0=blks[4]
        elif ("B053F10-13" in blks[0]):
            zdict.append(blks[1:])
        elif "B053F15-18" in blks[0]:
            pdict.append(blks[1:])
        elif "B053F08" in blks[0] and freq > 998:
            freq=blks[3]
        elif "B053F05" in blks[0]:
            IU=blks[5]
            IUdesc=" ".join((blks[7:]))
        elif "B053F06" in blks[0]:
            OU=blks[5]
            OUdesc=" ".join((blks[7:]))
        
fl.close()

if calcA:
    mychan=xmlf[0][0][0]
    print(mychan)
    A0=calc_a0(mychan.response,float(freq))
    
print('<fsx:FDSNStationXML xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:fsx=\"http://www.fdsn.org/xml/station/1\" xmlns:sis=\"http://anss-sis.scsn.org/xml/ext-stationxml/2.2\" xsi:type=\"sis:RootType\" schemaVersion=\"2.2\" sis:schemaLocation=\"http://anss-sis.scsn.org/xml/ext-stationxml/2.2 https://anss-sis.scsn.org/xml/ext-stationxml/2.2/sis_extension.xsd\">')
print('   <fsx:Source>ASL</fsx:Source>')
print('    <fsx:Sender>ASL</fsx:Sender>')
print('    <fsx:Created>%s</fsx:Created>'%(str(UTCDateTime())))
print('    <fsx:Network code=\"N4\">')
print('    </fsx:Network>')
print('    <sis:HardwareResponse>')
print('    <sis:ResponseDictGroup>')
print('       <sis:ResponseDict>     ')

print('         <sis:PolesZeros name=\"%s\" SISNamespace=\"ASL\">'%(key))
print('         <fsx:Description>%s</fsx:Description>'%(desc))
print('         <fsx:InputUnits>')
print('         <fsx:Name>%s</fsx:Name>'%(IU))
print('         <fsx:Description>%s</fsx:Description>'%(IUdesc))
print('         </fsx:InputUnits>')
print('         <fsx:OutputUnits>')
print('         <fsx:Name>%s</fsx:Name>'%(OU))
print('         <fsx:Description>%s</fsx:Description>'%(OUdesc))
print('         </fsx:OutputUnits>')
print('         <fsx:PzTransferFunctionType>LAPLACE (RADIANS/SECOND)</fsx:PzTransferFunctionType>')
print('         <fsx:NormalizationFactor>%s</fsx:NormalizationFactor>'%(A0))
print('         <fsx:NormalizationFrequency>%s</fsx:NormalizationFrequency>'%(freq))
for zz in zdict:
    print('         <fsx:Zero number="%s">'%(zz[0]))
    print('            <fsx:Real plusError="%s" minusError="%s">%s</fsx:Real>'%(zz[3],zz[3],zz[1]))
    print('            <fsx:Imaginary plusError="%s" minusError="%s">%s</fsx:Imaginary>'%(zz[4],zz[4],zz[2]))
    print('         </fsx:Zero>')

for zz in pdict:    
    print('         <fsx:Pole number="%s">'%(zz[0]))
    print('            <fsx:Real plusError="%s" minusError="%s">%s</fsx:Real>'%(zz[3],zz[3],zz[1]))
    print('            <fsx:Imaginary plusError="%s" minusError="%s">%s</fsx:Imaginary>'%(zz[4],zz[4],zz[2]))
    print('         </fsx:Pole>')

print('         </sis:PolesZeros>')
print('       </sis:ResponseDict>     ')
print('    </sis:ResponseDictGroup>')
print('</sis:HardwareResponse>')
print('</fsx:FDSNStationXML>')

 
