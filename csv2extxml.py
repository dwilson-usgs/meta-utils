#!/usr/bin/env python
import csv
import argparse
import datetime

parser = argparse.ArgumentParser(description='Reads in a csv file of equipment and writes out a extended station xml file for uploading to SIS. '+
                                 'The first three columns must contain Category, ModelName, SerialNumber.  The remaining columns need to be '+
                                 'key and value pairs')

parser.add_argument("-f", action="store", dest="infile",
                    required=True, help="input csv file")
parser.add_argument("-o", action="store", dest="outfile",
                    default='OutExtSta.xml', help="output extxml file (default is OutExtSta.xml)")
parser.add_argument("-d", action="store", dest="ondate",
                    default='1990-01-01T00:00:00Z', help="On Date (default is 1990-01-01T00:00:00Z)")
parser.add_argument("-op", action="store", dest="operator",
                    default='ASL', help="Operator (default is ASL)")
parser.add_argument("-ow", action="store", dest="owner",
                    default='ASL', help="Owner (default is ASL)")
parser.add_argument("-net", action="store", dest="network",
                    default='GS', help="Network (default is GS)")

args = parser.parse_args()
fil = args.infile
od = args.ondate
op = args.operator
ofil=args.outfile
net=args.network
ow=args.owner

f=open(ofil,'w')
f.write('<fsx:FDSNStationXML xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:fsx=\"http://www.fdsn.org/xml/station/1\" xmlns:sis=\"http://anss-sis.sc'+
        'sn.org/xml/ext-stationxml/2.2\" xsi:type=\"sis:RootType\" schemaVersion=\"2.2\" sis:schemaLocation=\"http://anss-sis.scsn.org/xml/ext-stationxml/2.2 https://anss-sis.sc'+
        'sn.org/xml/ext-stationxml/2.2/sis_extension.xsd\">\n')
f.write('   <fsx:Source>ASL</fsx:Source>\n')
f.write('    <fsx:Sender>ASL</fsx:Sender>\n')
f.write('    <fsx:Created>%s</fsx:Created>\n'%(datetime.datetime.utcnow().isoformat(timespec='seconds')+"Z"))
f.write('    <fsx:Network code="%s">\n'%(net))
f.write('    </fsx:Network>\n')
f.write('    <sis:HardwareResponse>\n')
f.write('    <sis:Hardware>     \n ')

with open(fil) as csvfile:
    readCSV = csv.reader(csvfile, delimiter=',')
    for row in readCSV:
        f.write('<sis:Equipment>\n')
        f.write('<sis:SerialNumber>%s</sis:SerialNumber>\n'%(row[2]))
        f.write('<sis:ModelName>%s</sis:ModelName>\n'%(row[1]))
        f.write('<sis:Category>%s</sis:Category>\n'%(row[0]))
        f.write('<sis:IsActualSerialNumber>true</sis:IsActualSerialNumber>\n')
        f.write('<sis:EquipmentEpoch>\n')
        f.write('  <sis:OnDate>%s</sis:OnDate>\n'%(od))
        f.write('  <sis:InventoryStatus>FUNCTIONAL</sis:InventoryStatus>\n')
        f.write('  <sis:Operator>%s</sis:Operator>\n'%(op))
        f.write('  <sis:Owner>%s</sis:Owner>\n'%(ow))
        f.write('</sis:EquipmentEpoch>\n')
        # now loop through rest of columns of paired keys and values
        if len(row) > 3:
            for n in range(3,len(row),2):
                f.write('<sis:EquipSetting>\n')
                f.write('  <sis:Key>%s</sis:Key>\n'%(row[n]))
                f.write('  <sis:Value>%s</sis:Value>\n'%(row[n+1]))
                f.write('  <sis:OnDate>%s</sis:OnDate>\n'%(od))
                f.write('</sis:EquipSetting>\n')
                
        f.write('</sis:Equipment>\n')

f.write('</sis:Hardware>\n')
f.write('</sis:HardwareResponse>\n')
f.write('</fsx:FDSNStationXML>\n')
f.close()
