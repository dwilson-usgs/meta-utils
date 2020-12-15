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

parser = argparse.ArgumentParser(description='reads in RESP, and dump a FIR cascade to a extended station xml ready for upload to SIS. retains error values.')

parser.add_argument("-f", action="store", dest="RespFile",
                    required=True, help="Resp file")
parser.add_argument("-key", action="store", dest="Key",
                    default='FIR_out', help="Key for FIR representation (default is FIR_out)")
parser.add_argument("-desc", action="store", dest="Title",
                    default='ASL calibration', help="FIR description (default is ASL calibration)")
parser.add_argument("-ss", action="store", dest="sStage",
                    default='4', help="number of the stage to start the filter cascade (default is 4)")
parser.add_argument("-es", action="store", dest="eStage",
                    default='999', help="number of the stage to end the filter cascade (default is same as ss)")

freq=999

args = parser.parse_args()
fil = args.RespFile
desc = args.Title
key = args.Key
stagen=int(args.sStage)
if args.eStage == '999':
    stagex=stagen
else:
    stagex=int(args.eStage)

def check_sym(st):
    nn=len(st.numerator)
    n2=int(np.floor(nn/2))
    tf=False
    nstop=nn
    if n2*2 == nn:
        nsum=0
        for nc in range(n2):
            nsum=nsum+st.numerator[nc]-st.numerator[-(nc+1)]
        if nsum ==0:
            tf=True
            nstop=n2
    return tf, nstop
    
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

mychan=xmlf[0][0][0]

#print('<fsx:FDSNStationXML xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:fsx=\"http://www.fdsn.org/xml/station/1\" xmlns:sis=\"http://anss-sis.scsn.org/xml/ext-stationxml/2.2\" xsi:type=\"sis:RootType\" schemaVersion=\"2.2\" sis:schemaLocation=\"http://anss-sis.scsn.org/xml/ext-stationxml/2.2 https://anss-sis.scsn.org/xml/ext-stationxml/2.2/sis_extension.xsd\">')
print('<fsx:FDSNStationXML xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:fsx=\"http://www.fdsn.org/xml/station/1\" xmlns:sis=\"http://anss-sis.sc'+
        'sn.org/xml/ext-stationxml/3.0\" xsi:type=\"sis:RootType\" schemaVersion=\"3.0\" sis:schemaLocation=\"http://anss-sis.scsn.org/xml/ext-stationxml/3.0 https://anss-sis.sc'+
        'sn.org/xml/ext-stationxml/3.0/sis_extension.xsd\">\n')
print('   <fsx:Source>ASL</fsx:Source>')
print('    <fsx:Sender>ASL</fsx:Sender>')
print('    <fsx:Created>%s</fsx:Created>'%(str(UTCDateTime())))
print('    <fsx:Network code=\"N4\">')
print('    </fsx:Network>')
print('    <sis:HardwareResponse>')
print('    <sis:ResponseDictGroup>')
ns=stagen-1
for stage in mychan.response.response_stages[stagen-1:stagex]:
    ns=ns+1
    IU=stage.input_units
    
    OU=stage.output_units
    if IU=='COUNTS':
        IU='counts'
    if OU=='COUNTS':
        OU='counts'
    IUdesc=stage.input_units_description
    OUdesc=stage.output_units_description
    tf, nstop = check_sym(stage)
    sym='NONE'
    if tf==True:
        sym='EVEN'
    print('       <sis:ResponseDict>     ')

    print('         <sis:FIR name=\"%s_%i\" SISNamespace=\"ASL\">'%(key,ns))
    print('         <fsx:Description>%s</fsx:Description>'%(desc))
    print('         <fsx:InputUnits>')
    print('         <fsx:Name>%s</fsx:Name>'%(IU))
    print('         <fsx:Description>%s</fsx:Description>'%(IUdesc))
    print('         </fsx:InputUnits>')
    print('         <fsx:OutputUnits>')
    print('         <fsx:Name>%s</fsx:Name>'%(OU))
    print('         <fsx:Description>%s</fsx:Description>'%(OUdesc))
    print('         </fsx:OutputUnits>')
    print('         <fsx:Symmetry>%s</fsx:Symmetry>'%(sym))
    nn=0
    for cc in stage.numerator:
        nn=nn+1
        if nn <= nstop:
            print('         <fsx:NumeratorCoefficient i="%i">%9.8e</fsx:NumeratorCoefficient>'%(nn,cc))
        else:
            break

    print('         </sis:FIR>')
    print('       </sis:ResponseDict>     ')

print('       <sis:ResponseDict>     ')
print('         <sis:FilterSequence name=\"%s\" SISNamespace=\"ASL\">'%(key))
ns=stagen-1
sqn=0
for stage in mychan.response.response_stages[stagen-1:stagex]:
    ns=ns+1
    sqn=sqn+1
    IU=stage.input_units
    OU=stage.output_units
    if IU=='COUNTS':
        IU='counts'
    if OU=='COUNTS':
        OU='counts'
    IUdesc=stage.input_units_description
    OUdesc=stage.output_units_description

    print('         <sis:FilterStage>')
    print('         <sis:SequenceNumber>%i</sis:SequenceNumber>'%(sqn))
    print('         <sis:Filter>')
    print('         <sis:Name>%s_%i</sis:Name>'%(key,ns))
    print('         <sis:SISNamespace>ASL</sis:SISNamespace>')
    print('         <sis:Type>FIR</sis:Type>')
    print('         </sis:Filter>')
    print('         <sis:Decimation>')
    print('         <fsx:InputSampleRate>%9.8e</fsx:InputSampleRate>'%stage.decimation_input_sample_rate)
    print('         <fsx:Factor>%i</fsx:Factor>'%stage.decimation_factor)
    print('         <fsx:Offset>%i</fsx:Offset>'%stage.decimation_offset)
    print('         <fsx:Delay>%9.8e</fsx:Delay>'%stage.decimation_delay)
    print('         <fsx:Correction>%9.8e</fsx:Correction>'%stage.decimation_correction)
    print('         </sis:Decimation>')
    print('         <sis:Gain>')
    print('         <fsx:Value>%9.8e</fsx:Value>'%stage.stage_gain)
    print('         <fsx:Frequency>%9.8e</fsx:Frequency>'%stage.stage_gain_frequency)
    print('         <sis:InputUnits>')
    print('         <fsx:Name>%s</fsx:Name>'%(IU))
    print('         <fsx:Description>%s</fsx:Description>'%(IUdesc))
    print('         </sis:InputUnits>')
    print('         <sis:OutputUnits>')
    print('         <fsx:Name>%s</fsx:Name>'%(OU))
    print('         <fsx:Description>%s</fsx:Description>'%(OUdesc))
    print('         </sis:OutputUnits>')
    print('         </sis:Gain>')
    print('         </sis:FilterStage>')

print('         </sis:FilterSequence>')
print('       </sis:ResponseDict>     ')
print('    </sis:ResponseDictGroup>')
print('</sis:HardwareResponse>')
print('</fsx:FDSNStationXML>')

