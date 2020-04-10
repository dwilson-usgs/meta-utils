#!/usr/bin/env python
import sys
import warnings
from obspy import read, UTCDateTime, read_inventory
from obspy.clients.fdsn.header import FDSNNoDataException
from numpy import median
import collections
warnings.filterwarnings('ignore')

import argparse

parser = argparse.ArgumentParser(description='read in  station xml or dataless and list contents')

parser.add_argument("-f", action="store", dest="xfil",
                    required=True, help="Station XML or dataless file")


args = parser.parse_args()
fil = args.xfil


try:
    xmlf = read_inventory(fil)
except:
    sys.exit("Couldn't read in file.")

#mps_df = pd.DataFrame(columns=['Station', 'Sensor', 'Location', 'Channel', 'Mass'])
mps_dict = collections.defaultdict(dict)
for net in xmlf:
    for sta in net:
        for chan in sta:
            sncl = '{}.{}.{}.{}'.format(net.code, sta.code, chan.location_code, chan.code)
            sensor = chan.sensor.description
            epoch="%s-%s"%(str(chan.start_date),str(chan.end_date))
            mystr="%s (%5.1f sps), dep:%4.1f, az:%4.1f, dip:%3.1f"%(sncl,chan.sample_rate,chan.depth,chan.azimuth,chan.dip)
            #print(mystr)
            #print(chan.response)
            if chan.response is not None:
                for resp in chan.response.response_stages:
                    if resp.stage_gain is not None:
                        if abs(float(resp.stage_gain)-1.) > .01:
                            if resp.stage_gain > 20000:
                                mystr=mystr+", s%ig:%6e @ %3.2f Hz"%(resp.stage_sequence_number, resp.stage_gain, resp.stage_gain_frequency)
                            else:
                                mystr=mystr+", s%ig:%5.2f @ %3.2f Hz"%(resp.stage_sequence_number, resp.stage_gain, resp.stage_gain_frequency)
            #else:
                #mystr=mystr+", no response"
            if not mps_dict[sta.code]:
                mps_dict[sta.code] = collections.defaultdict(dict)
            if not mps_dict[sta.code][epoch]:
                mps_dict[sta.code][epoch] = collections.defaultdict(dict)
            if not mps_dict[sta.code][epoch][chan.location_code]:
                mps_dict[sta.code][epoch][chan.location_code] = collections.defaultdict(dict)
            if not mps_dict[sta.code][epoch][chan.location_code]['sensor']:
                mps_dict[sta.code][epoch][chan.location_code]['sensor']=sensor
            if not mps_dict[sta.code][epoch][chan.location_code]['chans']:
                mps_dict[sta.code][epoch][chan.location_code]['chans']=[mystr]
            else:
                mps_dict[sta.code][epoch][chan.location_code]['chans'].append(mystr)


# print if out of tolerance
for sta in mps_dict:
    print("Station: %s"%(sta))
    #epochs=sorted(mps_dict[sta].values())
    #mps_dict[sta]=sorted(mps_dict[sta])
    #for epoch in mps_dict[sta]:
    for epoch in sorted(mps_dict[sta].keys()):
        print("\n ------------------------")
        print(epoch)
        for loc in mps_dict[sta][epoch]:
            print("Location %s, sensor=%s"%(loc,mps_dict[sta][epoch][loc]['sensor']))
            for chan in sorted(mps_dict[sta][epoch][loc]['chans']):
                print("\t %s "%(chan))                           



