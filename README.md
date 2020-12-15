# meta-utils
scripts and utilities for dealing with seismic metadata

Contents
======
* xmldump.py - dump the contents of a xml or dataless into a readable output format
* respplotcompare.py - plot two response files, comparing amplitude and phase
* resputil.py - reads in a resp file and checks a0 and overall sensitivity
* respstitch.py - stitches two resp files together at a specified frequency
* resp2sql.py - turns a resp file into a sql statement for inserting into a database
* resp2extxml.py - reads poles and zeros from a resp file and converts to SIS extended station xml for uploading into SIS. For example, a pole-zero set from a station calibration.
* csv2extxml.py - reads a csv file and outputs an extended StationXML file for uploaded into SIS. This is meant for hardware (non-seismic) equipment.
* FIR2extxml.py - reads a FIR filter cascade from a resp file and converts to SIS extended station xml for uploading into SIS.

**External Dependencies:**
 * most of these were built on
 Python 3.7.3  [GCC 7.3.0],
 obspy verson '1.1.0',
 but they should run on other versions as well.
 
---------------------------------------------------------

**Disclaimer:**

>This software is preliminary or provisional and is subject to revision. It is 
being provided to meet the need for timely best science. The software has not 
received final approval by the U.S. Geological Survey (USGS). No warranty, 
expressed or implied, is made by the USGS or the U.S. Government as to the 
functionality of the software and related material nor shall the fact of release 
constitute any such warranty. The software is provided on the condition that 
neither the USGS nor the U.S. Government shall be held liable for any damages 
resulting from the authorized or unauthorized use of the software.

---------------------------------------------------------
