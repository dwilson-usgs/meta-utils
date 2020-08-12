#!/usr/bin/env python
import sys
import warnings

#from obspy.clients.fdsn.header import FDSNNoDataException
#from numpy import median
#import collections
import numpy as np
import collections
from obspy import read_inventory, UTCDateTime
import matplotlib.pyplot as plt
import argparse

def calc_resp2(self, freqs, output="VEL", start_stage=None,
             end_stage=None, sampling_rate=None,
             unwrap_phase=False, plot_degrees=False):

    cpx_response= self.get_evalresp_response_for_frequencies(
        freqs, output=output, start_stage=start_stage,
        end_stage=end_stage)
    amp=abs(cpx_response)
    phase = np.angle(cpx_response, deg=plot_degrees)
    if unwrap_phase and not plot_degrees:
        phase = np.unwrap(phase)
    return amp, phase

parser = argparse.ArgumentParser(description='read in RESP and recalculate a0 and overall sensitivity at given frequency ')

parser.add_argument("-f1", action="store", dest="RespFile",
                    required=True, help="Resp file")
parser.add_argument("-f2", action="store", dest="RespFile2",
                    required=True, help="Resp file2")
parser.add_argument("-t1", action="store", dest="RespTime",
                    default='2099-12-31',  help="Time in case there are multiple epochs (default is latest)")
parser.add_argument("-t2", action="store", dest="RespTime2",
                    default=999,  help="Time to select from second epoch (default is same as t1)")

parser.add_argument("-freq1", action="store", dest="StitchFreq1",
                    default=.001,  help="Lower frequency bound for error calc, default is .001")
parser.add_argument("-freq2", action="store", dest="StitchFreq2",
                    default=1,  help="Upper frequency bound for error calc, (default is 1Hz)")
parser.add_argument("-s1", action="store", dest="StartStage",
                    default=1, help="Start Stage, default =1")
parser.add_argument("-s2", action="store", dest="EndStage",
                    default=1, help="End Stage, default =1")
args = parser.parse_args()

freq1= np.float(args.StitchFreq1)
freq2= np.float(args.StitchFreq2)
fil = args.RespFile
fil2 = args.RespFile2
tt = args.RespTime
tt2 = args.RespTime2
ss=int(args.StartStage)
es=int(args.EndStage)

if tt2==999:
    tt2=tt

try:
    xmlf = read_inventory(fil)
except:
    sys.exit("Couldn't read in file 1.")

try:
    xmlf2 = read_inventory(fil2)
except:
    sys.exit("Couldn't read in file 2.")

myresp1 = xmlf.select(time=UTCDateTime(tt))
myresp2 = xmlf2.select(time=UTCDateTime(tt2))

cha=myresp1[0][0][0]
cha2=myresp2[0][0][0]

logf=np.arange(np.log(freq1),np.log(freq2),.01)
freqs=np.exp(logf)
mypz=cha.response.get_paz()
print(mypz.normalization_frequency)
ff=np.argmin(np.abs(freqs-mypz.normalization_frequency))

amp1, phase1 = calc_resp2(cha.response,freqs,plot_degrees=True,start_stage=ss,end_stage=es)
amp2, phase2 = calc_resp2(cha2.response,freqs,plot_degrees=True,start_stage=ss,end_stage=es)

#amp1=amp1-amp1[ff]
#amp2=10**(np.log10(amp2)-(np.log10(amp2[ff])-np.log10(amp1[ff])))
amp1=20*np.log10(amp1)
amp2=20*np.log10(amp2)
amp1=amp1-(amp1[ff]-amp2[ff])
ampdiff = amp1-amp2
amprat=10**(ampdiff/20)
ampper=100*(amprat-1)

plt.figure(figsize=(7,9))
ax1 = plt.subplot(311)
ax2 = plt.subplot(312)
ax3 = plt.subplot(313)

ax1.semilogx(freqs,amp1,label=fil+" "+tt)
ax1.semilogx(freqs,amp2,label=fil2+" "+tt2)
ax1.legend(loc='best')

ax2.semilogx(freqs,ampper,color='g',label='amp1/amp2')
ax2.set_ylabel("amp diff (%)")
ax1.set_ylabel("amp (dB)")
ax3.semilogx(freqs,phase1-phase2,color='g',label='phase1-phase2')
ax3.set_ylabel("Phase diff (deg)")
ax3.set_xlabel("frequency (Hz)")
ax2.legend(loc='best')
ax2.legend(loc='best')
ax3.grid()
ax2.grid()
ax1.set_title('%s / %s '%(fil,fil2))
#ax1.set_xlim([.0001, 40])
#ax2.set_xlim([.0001, 40])

plt.show()



