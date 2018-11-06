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

# Based on the HISReader of The Open Microscopy Environment
# http://www.openmicroscopy.org/site/support/bio-formats5.2/formats/hamamatsu-his.html
#

# Hamamatsu HIS ImageJ VirtualStack Opener
# ----------------------------------------
# This script quickly opens as a VirtualStack the typical HIS files generated with 
# Hokawo and Hamamatsu Orca cameras (tested on Orca Flash 2.8 and 4.0 and Hokawo
# versions 2.5 and 2.8). Note that if the number of frames is large the stack
# might be corrupted towards the end of the file (you will see that if the image starts
# to "travel"). This is due to a change in metadata length inside the HIS file and cannot
# be easily avoided without a sequential opening. 
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

import struct
import os

def main():
  imp = IJ.getFilePath("Select HIS file")
  if not imp:
    return
  root, ext = os.path.splitext(imp)
  if ext.lower() != '.his':
    cFrame = PlugInFrame('ERR DLG')
    MessageDialog(cFrame, 'ERROR', 'Expected extension .his')
    return

  fID = open(imp, 'rb')
  fID.seek(2)
  offset = struct.unpack('<h', fID.read(2))[0]
  fID.seek(14)
  frames = struct.unpack('<I', fID.read(4))[0]
  fID.seek(2)
  commentBytes = struct.unpack('<h', fID.read(2))[0]
  width = struct.unpack('<h', fID.read(2))[0]
  height = struct.unpack('<h', fID.read(2))[0]
  struct.unpack('<I', fID.read(4))[0]
  fileType = struct.unpack('<h', fID.read(2))[0]
  fID.read(50)

  metadata = fID.read(commentBytes)
  metadataSplit = metadata.split(';')
  metadataStr = beginMetadata()
  for it in metadataSplit:
    sp = it.split("=")
    if len(sp) > 1:
      metadataStr += addMetadataEntry(sp[0], sp[1])
  metadataStr += endMetadata()
  metadataDlg = HTMLDialog("HIS metadata", metadataStr, 0)
  size = metadataDlg.getSize()
  if size.width < 300:
    size.width = 300
  if size.height < 500:
    size.height = 500
  metadataDlg.setSize(size)

  # The second image metadata
  # That's the gap (in case it is different)
  fID.seek(offset+64+width*height*(fileType)+2)
  gap = struct.unpack('<h', fID.read(2))[0]

  # Now let's check the metadata size across several frames to see if it's consistent
  vals = range(1, frames, int(frames/100))
  md_old = gap
  metadataInconsistency = 0
  for it in range(0, len(vals)):
    if metadataInconsistency > 0:
      break
    cFrame = vals[it]
    if cFrame < 3:
      continue
    cPixel = (width*height*(fileType)+gap+64)*(cFrame-2)+offset+64+width*height*(fileType)+2
    fID.seek(cPixel)
    md_new = struct.unpack('<h', fID.read(2))[0]
    if(md_new != md_old):
      # Let's narrow the search
      nvals = range(vals[it-1], vals[it]+1)
      print nvals
      for it2 in range(0, len(nvals)):
        cFrame = nvals[it2]
        if cFrame < 3:
          continue
        cPixel = (width*height*(fileType)+gap+64)*(cFrame-2)+offset+64+width*height*(fileType)+2
        fID.seek(cPixel)
        md_new = struct.unpack('<h', fID.read(2))[0]
        print md_new
        if(md_new != md_old):
          metadataInconsistency = cFrame
          offset = cPixel+gap
          gap = md_new
          break
        md_old = md_new
    md_old = md_new

  metadataStr = beginMetadata()
  metadataStr += addMetadataEntry('width', str(width))
  metadataStr += addMetadataEntry('height', str(height))
  metadataStr += addMetadataEntry('nImages', str(frames))
  metadataStr += addMetadataEntry('offset', str(offset+64))
  metadataStr += addMetadataEntry('fileType', str(fileType))
  metadataStr += addMetadataEntry('gapBetweenImages', str(gap+64))
  if(metadataInconsistency > 0):
    metadataStr += addMetadataEntry('Inconsistent METADATA', str(metadataInconsistency))
  metadataStr += endMetadata()
  metadataDlg = HTMLDialog("HIS parameters", metadataStr, 0)
  size = metadataDlg.getSize()
  if size.width < 300:
    size.width = 300
  if size.height < 300:
    size.height = 300
  metadataDlg.setSize(size)
  
  finfo = FileInfo()
  finfo.fileName = imp
  finfo.width = width
  finfo.height = height
  finfo.nImages = frames
  finfo.offset = offset+64
  finfo.fileType = fileType-1
  finfo.intelByteOrder = 1
  finfo.gapBetweenImages = gap+64
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
  

if __name__ == '__main__':
  main()
