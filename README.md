# hamamatsuOrcaTools
Set of tools to work with files created with Hamamatsu Orca cameras and their software (Hokawo and HCImage).

## Hamamatsu HIS ImageJ VirtualStack Opener

This script quickly opens as a VirtualStack the typical HIS files generated with 
Hokawo and Hamamatsu Orca cameras (tested on Orca Flash 2.8 and 4.0 and Hokawo
versions 2.5 and 2.8). Note that if the number of frames is large the stack
might be corrupted towards the end of the file (you will see that if the image starts
to "travel"). This is due to a change in metadata length inside the HIS file and cannot
be easily avoided without a sequential opening. 

Based on the [HISReader](http://www.openmicroscopy.org/site/support/bio-formats5.2/formats/hamamatsu-his.html)
of The Open Microscopy Environment.

### Installation
Copy the file [HIS_opener.py](HIS_opener.py) somwhere inside the plugins folder in ImageJ.

Typical location is `FIJI.app/plugins/Scripts/Plugins`
Restart ImageJ and `HIS opener` should appear at the bottom of the Plugins menu.

### Usage
Select HIS opener from the ImageJ plugins menu and select the HIS file.

