from obspy import read_inventory, UTCDateTime
from obspy.core.inventory.response import ResponseStage
import sys, os
from numpy import median
#from string import string

if len(sys.argv)<5:
   sys.stderr.write('Usage:   resp2ims.py net sta loc chan sensor date \n')
   sys.exit()
net = sys.argv[1]
st = sys.argv[2]
lo = sys.argv[3]
ch = sys.argv[4]
sens=sys.argv[5]
d1 = sys.argv[6]
d1 = d1.strip()

if ch == "BH1":
   ch2 = "BHN"
elif ch == "BH2":
   ch2 = "BHE"
else:
   ch2=ch


myfile='/APPS/metadata/RESPS/RESP.%s.%s.%s.%s' % (net, st, lo, ch)
#print(myfile)
inv = read_inventory(myfile)
t = UTCDateTime(d1)
seed_id='%s.%s.%s.%s' % (net, st, lo, ch)
inv = inv.select(channel=ch, station=st, time=t)
response = inv.get_response(seed_id,t)
#print(response)

ncalib1=response.get_evalresp_response_for_frequencies([1.0],output='DISP')
ncalib = 1e9 / abs(ncalib1)
scal1=response.get_evalresp_response_for_frequencies([1.0],output='VEL',start_stage=1, end_stage=1)
scal = 1e9 / abs(scal1)
scal1=response.get_evalresp_response_for_frequencies([1.0],output='VEL',start_stage=2, end_stage=2)
scal2 = abs(scal1)
scal1=response.get_evalresp_response_for_frequencies([1.0],output='VEL',start_stage=3, end_stage=3)
scal3 = abs(scal1)
pzs=response.get_paz()
np=len(pzs.poles)
nz=len(pzs.zeros)

print("STA_LIST %s" % (st) )
print("CHAN_LIST %s" % (ch2) )
print("CALIBRATE_RESULT")
print("IN_SPEC yes")
print("CALIB %9.7f" % ( ncalib ) )
print("CALPER 1")
print("DATA_TYPE RESPONSE IMS2.0")
print("CAL2 %5s %3s      %6s %15.8e %7.3f %11.5f %s 00:00" % ( st, ch2, sens, ncalib,  1.0, 40.0, d1 ) ) 
print("PAZ2 01 V %15.8e  0    0.000   %3d %3d   %10s" % (scal, np, nz+1, sens) )
for myp in pzs.poles:
   print(" %15.8e %15.8e" % ( myp.real, myp.imag ) )
for myp in pzs.zeros:
   print(" %15.8e %15.8e" % ( myp.real, myp.imag ) )
print(" %15.8e %15.8e" % ( 0.0, 0.0 ) )

print("DIG2 2  %15.8e %11.5f          Q330HR" % (scal2, 40.0 ) )
fir=response.response_stages
newlist=[ float(i) for i in fir[2].numerator]
print("FIR2 3  %10.2e 1    %8.3f A %4d  " % (scal3, 0.430, len(newlist)) )
i=0
while i < (len(newlist)-4):
   print(" %15.8e %15.8e %15.8e %15.8e %15.8e" % (  newlist[i], newlist[i+1], newlist[i+2], newlist[i+3], newlist[i+4] ) )
   i = i+5
if i < len(newlist):
   if len(newlist)-i == 1:
      print(" %15.8e " % (  newlist[i] ) )
   if len(newlist)-i == 2:
      print(" %15.8e %15.8e" % (  newlist[i], newlist[i+1] ) )
   if len(newlist)-i == 3:
      print(" %15.8e %15.8e %15.8e" % (  newlist[i], newlist[i+1], newlist[i+2] ) )
   if len(newlist)-i == 4:
      print(" %15.8e %15.8e %15.8e %15.8e" % (  newlist[i], newlist[i+1], newlist[i+2], newlist[i+3] ) )


