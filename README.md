# hamamatsuOrcaTools
Set of tools to work with files created with Hamamatsu Orca cameras and their software (Hokawo and HCImage).

## Hamamatsu HIS MATLAB handler

This class contains a few methods to load, view and handle HIS files generated with Hokawo (streaming)  and Hammamatsu Orca cameras (teste on Orca Flash 2.8 and 4.0 and Hokawo versions 2.5 and 2.8).

One of the main advantages comapared with using Hokawo is that i can load and preview any frame on the file almost instantly. Without the need to read the whole file first.

### Installation
Just copy [his.m](his.m) somewhere in your path

### Usage
Create a new object with its constructor:
~~~
exp = his(); % This will open a uigetfile dialog to ask for the HIS file
exp = his('/path/to/his/file.his'); % To automatically load the file
~~~
The created object has a few public properties, namely `numFrames, width, height, metadata, pixelType, bpp, fps, totalTime` (self explanatory).

Now, if you want to pull a specific frame:
~~~
img = exp.getFrame(2); % Will pull frame number 2;
~~~
And to directly preview it (opens a figure and calls imagesc):
~~~
hFig = exp.previewFrame(2); % Returns the figure handle
~~~
Full working code to iterate through all the frames:
~~~
exp = his('/path/to/his/file.his'); % To automatically load the file
exp = exp.openStream();
for it = 1:exp.numFrames
  img = exp.getFrame(it);
  % Do something with the image
end
exp = exp.closeStream();
~~~

### Notes
This HIS reader makes use of a precaching hack to predict frames positions, but if you have issues pulling specific frames, you might want to look at the precacheHISframes function inside the class.

### TODO
Verification of precaching on incomplete HIS files

Based on the [HISReader](https://docs.openmicroscopy.org/bio-formats/5.9.2/formats/hamamatsu-his.html)
of The Open Microscopy Environment.

## Hamamatsu HIS ImageJ VirtualStack Opener

This script quickly opens as a VirtualStack the typical HIS files generated with 
Hokawo and Hamamatsu Orca cameras (tested on Orca Flash 2.8 and 4.0 and Hokawo
versions 2.5 and 2.8). 
If you see 'Inconsistent METADATA' in the HIS parameters window it means that the stack
might be corrupted (you will see that if the image starts to "travel"). This is due to a 
change in metadata length inside the HIS file and cannot be easily avoided without a sequential opening
and/or precaching.

Based on the [HISReader](https://docs.openmicroscopy.org/bio-formats/5.9.2/formats/hamamatsu-his.html)
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