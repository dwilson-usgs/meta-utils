#!/usr/bin/env python
import sys
import warnings
from obspy import read, UTCDateTime, read_inventory
from obspy.clients.fdsn.header import FDSNNoDataException
from numpy import median
import collections
from obspy.clients.fdsn import Client
client = Client("IRIS")
warnings.filterwarnings('ignore')

import argparse

parser = argparse.ArgumentParser(description='read in  station xml or dataless and list contents')

parser.add_argument("-f", action="store", dest="xfil",
                    default='nofile', help="Station XML or dataless file")
parser.add_argument("-n", action="store", dest="Network",
                    default='nonet', help="Network Code. Only used if no file is given")
parser.add_argument("-s", action="store", dest="Station",
                    default='nosta', help="Station Code. Only used if no file is given")

args = parser.parse_args()
fil = args.xfil
net1= args.Network
sta1=args.Station

if fil != "nofile":
    try:
        xmlf = read_inventory(fil)
    except:
        sys.exit("Couldn't read in file.")
elif net1 != "nonet" and sta1 != "nosta":
    xmlf = client.get_stations(network=net1,station=sta1, level='response')
else:
    sys.exit("Must provide either a file or network and station on input.")
    
#mps_df = pd.DataFrame(columns=['Station', 'Sensor', 'Location', 'Channel', 'Mass'])
mps_dict = collections.defaultdict(dict)
for net in xmlf:
    for sta in net:
        for chan in sta:
            sncl = '{}.{}.{}.{}'.format(net.code, sta.code, chan.location_code, chan.code)
            sensor = chan.sensor.description
            if chan.sensor.model is not None:
                sensor+=" "+chan.sensor.model
            if chan.sensor.serial_number is not None:
                sensor+=" "+chan.sensor.serial_number
            #print(chan.types)
            if 'TRIGGERED' in chan.types:
                flag='T'
            elif 'CONTINUOUS' in chan.types:
                flag='C'
            else:
                flag=' '
            epoch="%s-%s"%(str(chan.start_date),str(chan.end_date))
            mystr="%s (%5.1f sps)%s, dep:%4.1f, az:%4.1f, dip:%3.1f"%(sncl,chan.sample_rate,flag,chan.depth,chan.azimuth,chan.dip)
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
            if not mps_dict[sta.code][epoch][chan.location_code][sensor]:
                mps_dict[sta.code][epoch][chan.location_code][sensor] = collections.defaultdict(dict)
                #mps_dict[sta.code][epoch][chan.location_code]['sensor']=sensor
            if not mps_dict[sta.code][epoch][chan.location_code][sensor]['chans']:
                mps_dict[sta.code][epoch][chan.location_code][sensor]['chans']=[mystr]
            else:
                mps_dict[sta.code][epoch][chan.location_code][sensor]['chans'].append(mystr)


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
            for sensor in mps_dict[sta][epoch][loc]:
                #print("Location %s, sensor=%s"%(loc,mps_dict[sta][epoch][loc]['sensor']))
                print("Location %s, sensor=%s"%(loc,sensor))
                for chan in sorted(mps_dict[sta][epoch][loc][sensor]['chans']):
                    print("\t %s "%(chan))                           

    


