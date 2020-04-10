#!/usr/bin/env python
import sys
import warnings
from obspy import read, UTCDateTime, read_inventory
from obspy.clients.fdsn.client import Client
from obspy.clients.fdsn.header import FDSNNoDataException
from numpy import median
import numpy as np
import collections
import datetime

warnings.filterwarnings('ignore')
import matplotlib.pyplot as plt
import argparse
import datetime
import time
import matplotlib.dates as mdates
import ssl
myssl = ssl.create_default_context();
myssl.check_hostname=False
myssl.verify_mode=ssl.CERT_NONE

# Keep Python2 and Python3 compatibility
try:
    import urllib.parse as urlparse
    import urllib.request as urlrequest
except ImportError:
    import urllib as urlparse
    import urllib as urlrequest

parser = argparse.ArgumentParser(description='read in  station xml or dataless and list contents')

#parser.add_argument("-f", action="store", dest="xfil",
#                    required=True, help="Station XML or dataless file")


def date_type(date):
    try:
        return datetime.datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        try:
            return datetime.datetime.strptime(date, "%Y-%j")
        except ValueError:
            raise argparse.ArgumentTypeError("Invalid date: \"" + date + "\"")


formats = ["Human", "CSV"]

aliases = {"prod": "https://igskgacgvmweb01.cr.usgs.gov/dqa",
           "test": "https://igskgacgvmwebx1.cr.usgs.gov/dqa/test",
           "local": "http://localhost/dqa"
           }

parser.add_argument("-C", "--command", help="command for type of data retrieval, EG: -C data, hash, or md5, default is \"data\"", default="data")

parser.add_argument("-w", "--website", help="use website alias or full url. Aliases: prod, dev, and dqags", default="prod")
parser.add_argument("-n", "--network", help="network identifier, EG: -n IU", default="%")
parser.add_argument("-s", "--station", help="station identifier, EG: -s ANMO", default="%")
parser.add_argument("-l", "--location", help="location identifier, EG: -l 00", default="00-10")
parser.add_argument("-c", "--channel", help="channel identifier, EG: -c BH%%", default="%")
parser.add_argument("-m", "--metric", help="metric name, EG: -m AvailabilityMetric", default="DifferencePBM:4-8")
parser.add_argument("-b", "--begin", help="start date EG: 2014-02-15 Default: Current date", type=date_type, default=time.strftime("%Y-%m-%d"))
parser.add_argument("-e", "--end", help="end date EG: 2014-02-15 Default: Current date", type=date_type, default=time.strftime("%Y-%m-%d"))
parser.add_argument("-f", "--format", choices=formats, help="format of output ", default="CSV")
parser.add_argument("-j", "--julian", help="show day of year ", action='store_true')
parser.add_argument("-a", "--average", help="display average of values ", action='store_true')

#parser.add_argument("-g", "--getmetrics", help="get list of metrics stored in database", action="store_true")
#parser.add_argument("-N", "--getnetworks", help="get list of networks stored in database", action="store_true")
#parser.add_argument("-S", "--getstations", help="get list of stations stored in database", action="store_true")

args = parser.parse_args()


if args.website in aliases:
    site = aliases[args.website]
else:
    site = args.website


#mps_df = pd.DataFrame(columns=['Station', 'Sensor', 'Location', 'Channel', 'Mass'])
def make_dict(xmlf):
    mps_dict = collections.defaultdict(dict)
    for net in xmlf:
        for sta in net:
            for chan in sta:
                sncl = '{}.{}.{}.{}'.format(net.code, sta.code, chan.location_code, chan.code)
                sensor = chan.sensor.description
                epoch="%s-%s"%(str(chan.start_date),str(chan.end_date))
                mystr="%s (%5.1f sps), dep:%4.1f, az:%4.1f, dip:%3.1f"%(sncl,chan.sample_rate,chan.depth,chan.azimuth,chan.dip)
                chstr=""
                #print(mystr)
                #print(chan.response)
                if chan.response is not None:
                    #for resp in chan.response.response_stages:
                    resp = chan.response.response_stages[0]
                    if resp.stage_gain is not None:
                        if abs(float(resp.stage_gain)-1.) > .01:
                            if resp.stage_gain > 20000:
                                mystr=mystr+", %6e @ %3.2f Hz"%(resp.stage_gain, resp.stage_gain_frequency)
                                chstr=chstr+", %6e @ %3.2f Hz"%( resp.stage_gain, resp.stage_gain_frequency)
                            else:
                                mystr=mystr+", %5.2f @ %3.2f Hz"%( resp.stage_gain, resp.stage_gain_frequency)
                                chstr=chstr+", %5.2f @ %3.2f Hz"%( resp.stage_gain, resp.stage_gain_frequency)
                #else:
                    #mystr=mystr+", no response"
                if not mps_dict[sta.code]:
                    mps_dict[sta.code] = collections.defaultdict(dict)
                if not mps_dict[sta.code][epoch]:
                    mps_dict[sta.code][epoch] = collections.defaultdict(dict)
                if not mps_dict[sta.code][epoch][chan.location_code]:
                    mps_dict[sta.code][epoch][chan.location_code] = collections.defaultdict(dict)
                if not mps_dict[sta.code][epoch]['start']:
                    mps_dict[sta.code][epoch]['start'] = datetime.datetime.strptime(chan.start_date.strftime('%Y-%m-%d %H:%M:%S'), "%Y-%m-%d %H:%M:%S")
                if not mps_dict[sta.code][epoch]['end']:
                    #print(chan.end_date)
                    if chan.end_date is None:
                        mps_dict[sta.code][epoch]['end'] = datetime.datetime.strptime("2599-01-01", "%Y-%m-%d")
                    else:
                        mps_dict[sta.code][epoch]['end'] = datetime.datetime.strptime(chan.end_date.strftime('%Y-%m-%d %H:%M:%S'), "%Y-%m-%d %H:%M:%S")
                if not mps_dict[sta.code][epoch][chan.location_code]['sensor']:
                    mps_dict[sta.code][epoch][chan.location_code]['sensor']=sensor
                if not mps_dict[sta.code][epoch][chan.location_code][chan.code]:
                    mps_dict[sta.code][epoch][chan.location_code][chan.code]=chstr
                if not mps_dict[sta.code][epoch][chan.location_code]['chans']:
                    mps_dict[sta.code][epoch][chan.location_code]['chans']=[mystr]
                else:
                    mps_dict[sta.code][epoch][chan.location_code]['chans'].append(mystr)
    return mps_dict

def signedlogplot(myax,dats,vals,plotflag):
    myax.plot(dats,np.log10(np.abs(vals)+1)*np.sign(vals),plotflag,alpha=.3)
    #myax.plot(dats,vals,'b.')
    
        
##########################################################

# get metadata using input info
client = Client("IRIS")
starttime = UTCDateTime(args.begin)
endtime = UTCDateTime(args.end)
#ddst=datetime.datetime.strptime(args.begin, "%Y-%m-%d")
#ddet=datetime.datetime.strptime(args.end, "%Y-%m-%d")
inventory = client.get_stations(starttime=starttime, endtime=endtime, 
   network=args.network, sta=args.station, loc="00,10", channel="LH?", level="response")

chanaliases = {"LHZ": "LHZ-LHZ",
           "LH1": "LHND-LHND",
           "LH2": "LHED-LHED"
           }
plotflags=["k.","b.","r."]
mps_dict=make_dict(inventory)

#print('net-sta-chan,start,end,median,std,00-gain,00-freq,00-depth,00-az,
# print if out of tolerance
for sta in mps_dict:
    print("Station: %s"%(sta))
    fig, axs = plt.subplots(2,figsize=(9,7))
    estarts=[]
    for epoch in sorted(mps_dict[sta].keys()):
        print("\n ------------------------")
        print(epoch)
        #print(mps_dict[sta][epoch])
        for loc in mps_dict[sta][epoch]:
            if '00' in loc or '10' in loc:
                print(mps_dict[sta][epoch][loc]['sensor'])
                for strg in mps_dict[sta][epoch][loc]['chans']:
                    print(strg)
                if '00' in loc:
                    axs[0].plot([ mps_dict[sta][epoch]['start'] , mps_dict[sta][epoch]['start'] ],[0 , np.log10(8)],'r')
                    axs[1].plot([ mps_dict[sta][epoch]['start'] , mps_dict[sta][epoch]['start'] ],[0 , np.log10(2)],'r')
                elif '10' in loc:
                    axs[0].plot([ mps_dict[sta][epoch]['start'] , mps_dict[sta][epoch]['start'] ],[-np.log10(8) ,0],'r')
                    axs[1].plot([ mps_dict[sta][epoch]['start'] , mps_dict[sta][epoch]['start'] ],[-np.log10(2) ,0],'r')
        #print("00=%s%s"%(mps_dict[sta][epoch]['00']['sensor'],mps_dict[sta][epoch]['00'][chan]))
        
        estarts.append(mps_dict[sta][epoch]['start'])
        
        #axs[1].text(max([mps_dict[sta][epoch]['start'],args.begin]),0,"00=%s%s"%(mps_dict[sta][epoch]['00']['sensor'],mps_dict[sta][epoch]['00'][chan]))
        #axs[1].text(max([mps_dict[sta][epoch]['start'],args.begin]),-1,"10=%s%s"%(mps_dict[sta][epoch]['10']['sensor'],mps_dict[sta][epoch]['10'][chan]))
        #for chan in sorted(mps_dict[sta][epoch][loc]['chans']):
        #    print("\t %s "%(chan))
    estarts.append(args.end)
    for tt in range(0,len(estarts)-1):
        n=-1
        for chan in ["LHZ","LH1","LH2"]:
            n=n+1
            ### This is the section to replace with a mustang grab of channel to channel metrics
            params = urlparse.urlencode({"cmd":      args.command,
                                     "network":  args.network,
                                     "station":  sta,
                                     "location": args.location,
                                     "channel":  chanaliases[chan],
                                     "metric":   args.metric,
                                     #"sdate":    mps_dict[sta][epoch]['start'].strftime("%Y-%m-%d"),
                                     #"edate":    mps_dict[sta][epoch]['end'].strftime("%Y-%m-%d"),
                                     "sdate":    estarts[tt].strftime("%Y-%m-%d"),
                                     "edate":    estarts[tt+1].strftime("%Y-%m-%d"),
                                     "format":   args.format,
                                     "julian":   args.julian,
                                     "average":  args.average
                                     })
            fullsite = site + "/cgi-bin/dqaget.py?" + params
            response = urlrequest.urlopen(fullsite,context=myssl)
            output = response.read().decode('utf-8')
            #print(output)
            tave=estarts[tt]+datetime.timedelta(hours=7)
            ttave=UTCDateTime.strptime(tave.strftime('%Y-%m-%d %H:%M:%S'), "%Y-%m-%d %H:%M:%S")
            #print(ttave,args.network,sta,chan)
            #print(inventory)
            inv00=inventory.select(network=args.network, station=sta, location='00', channel="*"+chan, time=ttave)
            inv10=inventory.select(network=args.network, station=sta, location='10', channel=chan, time=ttave)
            #print(inv00)
            chan0=inv00[0][0][0]
            chan1=inv10[0][0][0]
            #chan.sensor.description
            sens0=chan0.sensor.description
            if "," in sens0:
                sens0.replace(","," ")
            sens1=chan1.sensor.description
            if "," in sens1:
                sens1.replace(","," ")
            resp0 = chan0.response.response_stages[0]
            resp1 = chan1.response.response_stages[0]
            #chan.depth,chan.azimuth,chan.dip
            #resp.stage_gain, resp.stage_gain_frequency
            dats=[]
            vals=[]
            for row in output.split('\n'):
                #print(row)
                rows=row.split(',')
                #print(rows)
                dats.append(datetime.datetime.strptime(rows[0], "%Y-%m-%d"))
                vals.append(np.float(rows[6]))
            #print('net-sta-chan,start,end,median,std,00-gain,00-freq,00-depth,00-az,10-gain,10-freq,10-depth,10-az,00-sensor,10-sensor
            print(" %s-%s-%s, %s,%s, %2.1f , %2.1f  ,%6.1f,%4.2f,%4.1f,%4.1f ,%6.1f,%4.2f,%4.1f,%4.1f, %s,%s" % (args.network,sta,str(chanaliases[chan]),str(estarts[tt]),str(estarts[tt+1])
                                                                                        ,np.median(vals),np.std(vals)
                                                                                        ,resp0.stage_gain, resp0.stage_gain_frequency,chan0.depth,chan0.azimuth
                                                                                        ,resp1.stage_gain, resp1.stage_gain_frequency,chan1.depth,chan1.azimuth
                                                                                        ,sens0,sens1))
            ### end of section to replace with Mustang grab
                
            #print(dats,vals)
            #axs[n].plot(dats,vals,'b.')
            signedlogplot(axs[0],dats,vals,plotflags[n])
            signedlogplot(axs[1],dats,vals,plotflags[n])
    n=-1
    for chan in ["LHZ","LH1","LH2"]:
        n=n+1
        axs[1].plot(dats[-1],0,plotflags[n],label=chan)
    
            
    axs[0].format_xdata = mdates.DateFormatter('%Y-%m-%d')
    v2=[-6,-3,-1,-.5,0.0,.5,1,3,6]
    axs[0].set_yticks(np.log10(np.abs(v2)+1)*np.sign(v2))
    axs[0].set_yticklabels(np.asarray(v2))
    axs[0].set_ylim([-np.log10(8), np.log10(8)])
    axs[0].set_xlim([args.begin,args.end])
    axs[0].text(args.begin+datetime.timedelta(days=5),np.log10(5.5),'00-epochs')
    axs[0].text(args.begin+datetime.timedelta(days=5),-np.log10(5.5),'10-epochs')
    axs[1].set_ylim([-np.log10(2), np.log10(2)])
    axs[1].format_xdata = mdates.DateFormatter('%Y-%m-%d')
    axs[1].set_xlim([args.begin,args.end])
    axs[1].legend()
    v2=[-1, -.5, -.25, 0.0, .25, .5, 1]
    axs[1].set_yticks(np.log10(np.abs(v2)+1)*np.sign(v2))
    axs[1].set_yticklabels(np.asarray(v2))
    plt.suptitle('%s, 00-10 (4-8s difference), %s to %s'%(sta,args.begin.strftime("%Y-%m-%d"),args.end.strftime("%Y-%m-%d")))
    axs[0].set_ylabel('dB')
    axs[1].set_ylabel('dB')
    axs[1].set_xlabel('date')
    
    #fig.autofmt_xdate()
    plt.show()


