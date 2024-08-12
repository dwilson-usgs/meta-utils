#!/usr/bin/env python
import sys
import warnings

#from obspy.clients.fdsn.header import FDSNNoDataException
#from numpy import median
#import collections
import numpy as np
from copy import deepcopy as dcopy

with warnings.catch_warnings():
    warnings.filterwarnings(action='ignore')
    from obspy import read, UTCDateTime, read_inventory


import argparse

parser = argparse.ArgumentParser(description='read in RESP and recalculate a0 and overall sensitivity at given frequency ')

parser.add_argument("-f", action="store", dest="RespFile",
                    required=True, help="Resp file")
parser.add_argument("-t", action="store", dest="RespTime",
                    default='2099-12-31',  help="Time in case there are multiple epochs (default is latest)")
parser.add_argument("-freq", action="store", dest="NormFreq",
                    default=999,  help="Normalization Frequency in Hz, default is the currently stated frequency")

args = parser.parse_args()
fil = args.RespFile
tt = args.RespTime
freq= float(args.NormFreq)

if 1:
    xmlf = read_inventory(fil)
else:
    sys.exit("Couldn't read in file.")

myresp = xmlf.select(time=UTCDateTime(tt))

def get_unit(resp):
    unit_map = {
            "DISP": ["M"],
            "VEL": ["M/S", "M/SEC"],
            "ACC": ["M/S**2", "M/(S**2)", "M/SEC**2", "M/(SEC**2)",
                    "M/S/S"]}
    i_u = resp.instrument_sensitivity.input_units
    unit = "VEL"
    for key, value in unit_map.items():
        if i_u and i_u.upper() in value:
            unit = key
    return unit

def old_calc_a0(resp,f):  # This one fails if gain and normalization frequencies are not the same
    unit=get_unit(resp)
    pz=resp.get_paz()
    #resp.response_stages[0].stage_gain=1
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        a1=np.abs(resp.get_evalresp_response_for_frequencies([f],output=unit,start_stage=1, end_stage=1)) / (pz.normalization_factor*resp.response_stages[0].stage_gain);
    a0 = 1/a1
    return a0

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

###############
with warnings.catch_warnings():
    warnings.filterwarnings(action='ignore')
    resp1=myresp[0][0][0].response
    pz=resp1.get_paz()
    a1=resp1.instrument_sensitivity.value
    a1f=resp1.instrument_sensitivity.frequency
    if freq>998:
        freq=pz.normalization_frequency
        f2=a1f
    else:
        f2=freq
        
    a2=np.abs(resp1.get_evalresp_response_for_frequencies([f2],output=get_unit(resp1)))
    a0=calc_a0(dcopy(resp1),freq)
    
    

    print("\n a0 Stated: %13.6E at %3.2f Hz, Computed: %13.6E at %3.2f Hz \n"%(pz.normalization_factor,pz.normalization_frequency,a0,freq))
    print("Overall Sensitivity Stated: %13.6E at %3.2f Hz, Computed: %13.6E at %3.2f Hz"%(a1,a1f,a2,f2))
         
            
