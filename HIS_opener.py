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
import struct

imp = IJ.getFilePath("Select HIS file")

fID = open(imp, 'rb')

fID.seek(2)
offset = struct.unpack('<h', fID.read(2))[0]


fID.seek(14)
frames = struct.unpack('<I', fID.read(4))[0]


fID.seek(4)
width = struct.unpack('<h', fID.read(2))[0]
height = struct.unpack('<h', fID.read(2))[0]
struct.unpack('<I', fID.read(4))[0]
fileType = struct.unpack('<h', fID.read(2))[0]

finfo = FileInfo()
finfo.fileName = imp
finfo.width = width
finfo.height = height
finfo.nImages = frames
finfo.offset = offset+64
finfo.fileType = fileType-1
finfo.intelByteOrder = 1
finfo.gapBetweenImages = offset+64
finfo.fileFormat = 1
finfo.samplesPerPixel = 1
finfo.displayRanges = None
finfo.lutSize = 0
finfo.whiteIsZero = 0
vs = VirtualStack()
finfo.virtualStack = vs
FileInfoVirtualStack(ar)
