#
# Copyright (c) 2015-2016 Javier G. Orlandi <javierorlandi@javierorlandi.com>
# - Universitat de Barcelona, 2015-2016
# - University of Calgary, 2016
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Based on the Python module for reading Hamamatsu DCIMG files from Stuart Littlefair
# https://github.com/StuartLittlefair/dcimg
#

# Hamamatsu DCIMG ImageJ VirtualStack Opener
# ------------------------------------------
# This script quickly opens as a VirtualStack the typical DCIMG files generated with 
# HCIMage and Hamamatsu Orca cameras (tested on Orca Flash 4.0 and HCImage Live 4.3).
#

from ij import IJ
from ij.io import FileInfo
from ij import VirtualStack
from ij.plugin import FileInfoVirtualStack
from ij.gui import MessageDialog
from ij.plugin.frame import PlugInFrame
from ij.gui import GenericDialog
from java.awt.Dialog import ModalityType
from ij.gui import HTMLDialog
#from org.python.core.util.StringUtil import toBytes
#from org.python.core.util.StringUtil import fromBytes
import struct
import os

def main():
  imp = IJ.getFilePath("Select DCIMG file")
  if not imp:
  	return
  root, ext = os.path.splitext(imp)
  if ext.lower() != '.dcimg':
    cFrame = PlugInFrame('ERR DLG')
    MessageDialog(cFrame, 'ERROR', 'Expected extension .dcimg')
    return

  #Lets start
  fID = open(imp, 'rb')

  hdr_bytes = read_header_bytes(fID)
  hdr = parse_header_bytes(fID, hdr_bytes)
  
  metadataStr = beginMetadata()
  for key, value in hdr.iteritems():
    metadataStr += addMetadataEntry(key, str(value))
  
  metadataStr += endMetadata()
  metadataDlg = HTMLDialog("DCIMG metadata", metadataStr, 0)
  size = metadataDlg.getSize()
  if size.width < 300:
    size.width = 300
  if size.height < 500:
    size.height = 500
  metadataDlg.setSize(size)

  finfo = FileInfo()
  finfo.fileName = imp
  #finfo.width = hdr['xsize_req']
  finfo.width = hdr['xsize']
  finfo.height = hdr['ysize']
  finfo.nImages = hdr['nframes']
  finfo.offset = 232
  finfo.fileType = hdr['bitdepth']/8-1 #Ugh
  finfo.intelByteOrder = 1
  #finfo.gapBetweenImages = int(hdr['bytes_per_img']*(1-float(hdr['xsize_req'])/float(hdr['xsize'])))
  finfo.gapBetweenImages = 0
  finfo.fileFormat = 1
  finfo.samplesPerPixel = 1
  finfo.displayRanges = None
  finfo.lutSize = 0
  finfo.whiteIsZero = 0
  vs = VirtualStack()
  finfo.virtualStack = vs
  FileInfoVirtualStack(finfo)

def addMetadataEntry(name, val):
  return "<tr><td style='padding:0 25px 0 0px;'><b>" + name + "</b></td><td>" + val + "</td></tr>"
  
def beginMetadata():
  return "<table border=0 cellspacing=0>"
  
def endMetadata():
  return "</table>"

def decode_float(self,whole_bytes,frac_bytes):
  whole  = from_bytes(whole_bytes,byteorder='little')
  frac   = from_bytes(frac_bytes,byteorder='little')
  if frac == 0:
    return whole
  else:
    return whole + frac * 10**-(floor(log10(frac))+1)

def read_header_bytes(self):
  self.seek(0)
  # initial metadata block is 232 bytes
  return self.read(232)
    
def parse_header_bytes(self,hdr_bytes):
  header = {}
  
  bytes_to_skip = 4*from_bytes(hdr_bytes[8:12],byteorder='little')
      
  curr_index = 8 + bytes_to_skip

  # nframes
  nfrms = from_bytes(hdr_bytes[curr_index:curr_index+4],byteorder='little')
  header['nframes'] = nfrms

  # filesize
  curr_index = 48
  header['filesize'] = from_bytes(hdr_bytes[curr_index:curr_index+8],byteorder='little')

  # bytes per pixel
  curr_index = 156
  header['bitdepth'] = 8*from_bytes(hdr_bytes[curr_index:curr_index+4],byteorder='little')

  # footer location 
  curr_index = 120
  header['footer_loc'] = from_bytes(hdr_bytes[curr_index:curr_index+4],byteorder='little')

  # number of columns (x-size)
  curr_index = 164
  header['xsize_req'] = from_bytes(hdr_bytes[curr_index:curr_index+4],byteorder='little')

  # bytes per row
  curr_index = 168
  header['bytes_per_row'] = from_bytes(hdr_bytes[curr_index:curr_index+4],byteorder='little')
  #if we requested an image of nx by ny pixels, then DCIMG files
  #for the ORCA flash 4.0 still save the full array in x.
  header['xsize'] = header['bytes_per_row']/2

  # binning
  # this only works because MOSCAM always reads out 2048 pixels per row
  # at least when connected via cameralink. This would fail on USB3 connection
  # and probably for other cameras.
  # TODO: find another way to work out binning
  header['binning'] = int(4096/header['bytes_per_row'])

  # funny entry pair which references footer location
  curr_index = 192
  odd = from_bytes(hdr_bytes[curr_index:curr_index+8],byteorder='little')
  curr_index = 40
  offset = from_bytes(hdr_bytes[curr_index:curr_index+8],byteorder='little')
  header['footer_loc'] = odd+offset

  # number of rows
  curr_index = 172
  header['ysize'] = from_bytes(hdr_bytes[curr_index:curr_index+4],byteorder='little')

  # TODO: what about ystart? 

  # bytes per image
  curr_index = 176
  header['bytes_per_img'] = from_bytes(hdr_bytes[curr_index:curr_index+4],byteorder='little')

  #if header['bytes_per_img'] != header['bytes_per_row']*header['ysize']:
  #    err_str = "bytes per img ({bytes_per_img}) /= nrows ({ysize}) * bytes_per_row ({bytes_per_row})".format(**header)
  #    raise DcimgError(err_str)
  
  return header

# There is probably an easier way to do that
def from_bytes (data, byteorder = 'little'):
  if byteorder!='little':
    data = reversed(data)
  num = 0
  for offset, byte in enumerate(data):
    #nb = toBytes(byte)
    nb = struct.unpack('B', byte[0])[0]
    #num += nb[0] << (offset * 8)
    num += nb << (offset * 8)
  return num

def sizeof_fmt(num, suffix='B'):
  for unit in ['','K','M','G','T','P','E','Z']:
    if abs(num) < 1024.0:
      return "%3.1f%s%s" % (num, unit, suffix)
    num /= 1024.0
  return "%.1f%s%s" % (num, 'Yi', suffix)
    
if __name__ == '__main__':
  main()
