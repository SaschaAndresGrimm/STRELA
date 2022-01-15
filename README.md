# STRELA LiveView
PyQtGraph-based LiveViewer GUI for the DECTRIS detectors 
using the DECTRIS zmq stream itnerface.


## How to run
usage: Strela.py [-h] [--nThreads NTHREADS] [--fps FPS] ip

STRELA ZMQ LiveView for DECTRIS detectors

positional arguments:
  ip                    DECTRIS detector IP or hostname

optional arguments:
  -h, --help            show this help message and exit
  --nThreads NTHREADS, -n NTHREADS
                        number of ZMQ receiver threads
  --fps FPS, -f FPS     display refresh rate in Hz

## Functionalities
LiveView via ZMQ stream interface
ROI and projection
zoom, pan
contrast, brightness, and color map control 
export images


## Dependencies
UI: PyQt5, pyqtgraph, qdarkstyle
data handling: zmq, lz4, bitshuffle, tifffile, numpy

### Installation in Debian Bullseye
sudo apt install hdf5lib-dev python3-pip bitshuffle
pip3 install numpy tifffile lz4 zmq PyQt5 pyqtgraph qdarkstyle