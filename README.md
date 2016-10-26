# hamamatsuOrcaTools
Set of tools to work with files created with Hamamatsu Orca cameras and their software (Hokawo and HCImage).

## Hamamatsu HIS ImageJ VirtualStack Opener

This script quickly opens as a VirtualStack the typical HIS files generated with 
Hokawo and Hamamatsu Orca cameras (tested on Orca Flash 2.8 and 4.0 and Hokawo
versions 2.5 and 2.8). 
If you see 'Inconsistent METADATA' in the HIS parameters window it means that the stack
might be corrupted (you will see that if the image starts to "travel"). This is due to a 
change in metadata length inside the HIS file and cannot be easily avoided without a sequential opening
and/or precaching.

Based on the [HISReader](http://www.openmicroscopy.org/site/support/bio-formats5.2/formats/hamamatsu-his.html)
of The Open Microscopy Environment.

### Installation
Copy the file [HIS_opener.py](HIS_opener.py) somwhere inside the plugins folder in ImageJ. To download only that
file press the Raw button and "Save As" in your browser.

Typical location is `FIJI.app/plugins/Scripts/Plugins`
Restart ImageJ and `HIS opener` should appear at the bottom of the Plugins menu.

### Usage
Select HIS opener from the ImageJ plugins menu and select the HIS file.

### Bugs
It looks like at some point Hokawo changed bit endianness. And I have no idea where that info is stored inside the HIS file (I am not even sure it is actually stored). So if the resulting movie makes no sense, you might have to change ` finfo.intelByteOrder` to `1` in the script.

## Hamamatsu DCIMG ImageJ VirtualStack Opener

This script quickly opens as a VirtualStack the typical DCIMG files generated with 
HCImage and Hamamatsu Orca cameras (tested on Orca Flash 2.8 and 4.0 and HCImage Live 4.3). 

Based on the Python module for reading Hamamatsu DCIMG files from [Stuart Littlefair](https://github.com/StuartLittlefair/dcimg).

### Installation
Copy the file [DCIMG_opener.py](DCIMG_opener.py) somwhere inside the plugins folder in ImageJ. To download only that
file press the Raw button and "Save As" in your browser.

Typical location is `FIJI.app/plugins/Scripts/Plugins`
Restart ImageJ and `DCIMG opener` should appear at the bottom of the Plugins menu.

### Usage
Select DCIMG opener from the ImageJ plugins menu and select the DCIMG file.