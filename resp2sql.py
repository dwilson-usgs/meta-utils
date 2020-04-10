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

parser = argparse.ArgumentParser(description='reads in RESP, recalculates a0, and dump poles and zeros to sql')

parser.add_argument("-f", action="store", dest="RespFile",
                    required=True, help="Resp file")
parser.add_argument("-key", action="store", dest="Key",
                    default='ZP_STSX',   required=True, help="Key for PZ representation (default is ZP_STSX)")
parser.add_argument("-title", action="store", dest="Title",
                    default='STSX',  required=True, help="Title of PZ representation (default is STSX)")
parser.add_argument("-t", action="store", dest="RespTime",
                    default='2099-12-31',  help="Time in case there are multiple epochs (default is latest epoch)")
parser.add_argument("-freq", action="store", dest="NormFreq",
                    default=999,  help="Normalization Frequency in Hz, default is the currently stated frequency")


args = parser.parse_args()
fil = args.RespFile
tt = args.RespTime
freq= np.float(args.NormFreq)
titl = args.Title
key = args.Key

try:
    xmlf = read_inventory(fil)
except:
    sys.exit("Couldn't read in file.")

def calc_a0(resp,f):
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
    pz=resp.get_paz()
    resp.response_stages[0].stage_gain=1
    
    a1=np.abs(resp.get_evalresp_response_for_frequencies([f],output=unit,start_stage=1, end_stage=1)) / pz.normalization_factor;
    a0 = 1/a1
    return a0

myresp = xmlf.select(time=UTCDateTime(tt))

#mps_df = pd.DataFrame(columns=['Station', 'Sensor', 'Location', 'Channel', 'Mass'])
#mps_dict = collections.defaultdict(dict)
resp1=myresp[0][0][0].response
pz=resp1.get_paz()
if freq>998:
    freq=pz.normalization_frequency
a0=calc_a0(resp1,freq)
print("INSERT INTO seed_pz (key, title, type, in_unit, out_unit, pcterr, A0, AF, desctype, description) VALUES (\'%s\', \'%s\', \'A\', \'M/S\', \'V\', 0, %8.7e, %4.3f, \'TEXT\', NULL) ; " % (key, titl,a0,freq))
zn=-1
for z in pz.zeros:
    zn=zn+1
    #print("%13.6E %13.6E"%(np.real(z),np.imag(z)))
    print("INSERT INTO seed_pz_data (key, rowkey, r_value, r_error, i_value, i_error) VALUES (\'%s\', \'Z%03d\', %8.7e, %8.7e, %8.7e, %8.7e ) ; " % (key, zn, np.real(z), 0, np.imag(z),0))
zn=-1
for z in pz.poles:
    zn=zn+1
    #print("%13.6E %13.6E"%(np.real(z),np.imag(z)))
    print("INSERT INTO seed_pz_data (key, rowkey, r_value, r_error, i_value, i_error) VALUES (\'%s\', \'P%03d\', %8.7e, %8.7e, %8.7e, %8.7e ) ; " % (key, zn, np.real(z), 0, np.imag(z),0))
            

#INSERT INTO seed_pz (key, title, type, in_unit, out_unit, pcterr, A0, AF, desctype, description) VALUES ('ZP_STS-6A2', 'STS-6A', 'A', 'M/S', 'V', 0, 9.772601e+12, .02, 'TEXT', NULL) ;
#INSERT INTO seed_pz_data (key, rowkey, r_value, r_error, i_value, i_error) VALUES ('ZP_STS-6A2', 'Z000', 0.000000E+00, 0.000000E+00, 0.000000E+00, 0.000000E+00) ;
