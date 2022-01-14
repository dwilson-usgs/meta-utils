#!/usr/bin/env python
import datetime
import glob
import os
import struct

from obspy.core import read, UTCDateTime

import sys


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def process_calibrations(start_year, start_day, end_year, end_day):
    start_date = datetime.datetime.strptime(start_year + ' ' + start_day, '%Y %j')
    end_date = datetime.datetime.strptime(end_year + ' ' + end_day, '%Y %j')

    filepaths = find_files(start_date, end_date)

    calibrations = find_calibrations([filepath for sublist in filepaths for filepath in sublist])
    print("network,station,location,channel,start,end,in_std,out_std,ratio")
    for cal in calibrations:
       sin_per=cal["signal_period"]
       cal_dur = float(cal['cal_duration'] / 10000)
       if sin_per=="1.0":
          if cal_dur > 300:

            try:
              fname = cal["file_name"]
              calInFile=""
              if('00_BHZ' in fname):
                   calInFile=fname.replace('00_BHZ','_BC0')
              elif('00_BH1' in fname):
                   calInFile=fname.replace('00_BH1','_BC0')
              elif('00_BH2' in fname):
                   calInFile=fname.replace('00_BH2','_BC0')
              elif('10_BHZ' in fname):
                   calInFile=fname.replace('10_BHZ','_BC1')
              elif('10_BH1' in fname):
                   calInFile=fname.replace('10_BH1','_BC1')
              elif('10_BH2' in fname):
                   calInFile=fname.replace('10_BH2','_BC1')
         
              st=read(fname)
              stIN=read(calInFile)
              stime = UTCDateTime(cal["start_time"])
              stime = stime + datetime.timedelta(seconds=cal_dur/3)
              etime = stime + datetime.timedelta(seconds=cal_dur/3)
         
              st.trim(stime,etime)
              stIN.trim(stime,etime)
              st.merge()
              stIN.merge()
              ins=stIN.std()
              outs=st.std()
         
              network_code = cal["network"]
              station_code = cal["station"]
              location_code = cal["location"]
              channel_code = cal["channel"]
              cal_input=cal["channel_input"]
         
              type = cal["type"]

              start_time = cal["start_time"]
              end_time = start_time + datetime.timedelta(seconds=get_end_time_delta_seconds(cal))
              if float(ins[0]) > 1000000.0:
                 start_time = start_time.strftime('%Y-%j %H:%M:%S')
                 end_time = end_time.strftime('%Y-%j %H:%M:%S')
                 print(network_code + "," + station_code + "," + location_code + "," + channel_code + "," + str(start_time) + "," + str(end_time) + ", %5.5f, %5.5f, %5.5f" % (ins[0], outs[0], outs[0]/ins[0]) )
         

            except:
            
                 pass

def find_files(start_date, end_date):
    """Find the files that may contain calibrations"""
    date = start_date
    filepaths = []
    while date <= end_date:
        #eprint("Searching "+str(date)+" until "+str(end_date))
        filepath = '/msd/%s_%s/%s/%s/*BC*.512.seed' % (MyNet, MySta, date.strftime('%Y'), date.strftime('%j'))
        if len(glob.glob(filepath)) > 0:
           filepath2 = '/msd/%s_%s/%s/%s/%s*%s*.512.seed' % (MyNet, MySta, date.strftime('%Y'), date.strftime('%j'), MyLoc, MyChan)
           #eprint(filepath2)
           filepaths.append(glob.glob(filepath2))
        date += datetime.timedelta(1)
    return filepaths


def find_calibrations(filepaths):
    """Attempts to retrieve calibrations by looking for calibration blockettes (310)"""
    # mostly written by Adam Ringler
    calibrations = []
    length = len(filepaths)
    curIndex = 0
    for filepath in filepaths:
        curIndex += 1
        #eprint("Parsing " + str(curIndex) + " of " + str(length))
        _, _, net_sta, year, jday, loc_chan_reclen_seed = filepath.split('/')
        date = UTCDateTime(year + jday)
        net, sta = net_sta.split('_')
        loc, chan = loc_chan_reclen_seed.split('.')[0].split('_')
        # read the first file and get the record length from blockette 1000
        fh = open(filepath, 'rb')
        record = fh.read(256)
        index = struct.unpack('>H', record[46:48])[0]
        file_stats = os.stat(filepath)
        try:
            record_length = 2 ** struct.unpack('>B', record[index + 6:index + 7])[0]
            # get the total number of records
            total_records = file_stats.st_size // record_length
            # now loop through the records and look for calibration blockettes
            for rec_idx in range(0, total_records):
                fh.seek(rec_idx * record_length, 0)
                record = fh.read(record_length)
                next_blockette = struct.unpack('>H', record[46:48])[0]
                while next_blockette != 0:
                    index = next_blockette
                    blockette_type, next_blockette = struct.unpack('>HH', record[index:index + 4])
                    #eprint("Blockette type %i" % ( blockette_type ) )
                    if blockette_type == 310:
                        year, jday, hour, minute, sec, _, tmsec, _, calFlags, duration = struct.unpack('>HHBBBBHBBL',
                                                                                                       record[
                                                                                                       index + 4:index + 20])
                        stime = UTCDateTime(year=year, julday=jday, hour=hour, minute=minute, second=sec)
                        # blockette for sine cals
                        signalPeriod, amplitude, calInput = struct.unpack('>ff3s', record[index + 20:index + 31])
                        calibrations.append(
                                {'network': str(net), 'station': str(sta), 'location': str(loc), 'channel': str(chan),
                                 'date': str(date), 'type': 310,
                                 'start_time': UTCDateTime(stime).datetime, 'flags': str(calFlags),
                                 'cal_duration': int(duration),
                                 'signal_period': str(signalPeriod), 'amplitude': str(amplitude),
                                 'channel_input': str(calInput.decode("ascii")),
                                 'file_name': str(filepath)})
                       

        except:
            pass
        fh.close()
    return calibrations


def java_time(datetime):
    return int(datetime.timestamp() * 1000)


def get_end_time_delta_seconds(calibration):
    if calibration['type'] == 300:
        step_delta = calibration['num_step_cals'] * calibration["step_duration"]
        interval_delta = calibration['num_step_cals'] * calibration["interval_duration"]
        seed_delta = step_delta + interval_delta
    else:
        seed_delta = calibration['cal_duration']
    # 0.0001 second ticks to seconds
    return seed_delta / 10000
#print(sys.argv[0])
if len(sys.argv)<3:
   sys.stderr.write('Usage:   sine_cal_process.py net sta [chan loc]\n\n')
   sys.exit()
MyNet = sys.argv[1]
MySta = sys.argv[2]
MyChan = "*[BE]H*"
MyLoc= "*"
if len(sys.argv) > 3:
   MyChan = sys.argv[3]
   #print(MyChan)
if len(sys.argv) > 4:
   MyLoc = sys.argv[4]
   #print(MyLoc)


process_calibrations("2016", "001", "2019", "101")


