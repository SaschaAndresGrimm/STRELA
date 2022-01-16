"""
STRELA -- STRE(am) L(iveview) A(pp)
Demonstration of a basic LiveViewer for small DECTRIS area detectors with SIMPLON API.
"""
import PyQt5
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
import qdarkstyle
import signal

import logging, logging.handlers
import sys, os, argparse, datetime, time
import tifffile

#log to log file and stdout
fileHandler = logging.FileHandler(filename='strela.log')
stdoutHandler = logging.StreamHandler(sys.stdout)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s: %(message)s',
                    handlers=[fileHandler, stdoutHandler],
                    )
log = logging.getLogger()

from tools import DummyReceiver, MonitorReceiver, StatusUpdater, ZmqReceiver, DEigerClient

__author__ = "Sascha Grimm"
__date__ = "2022.01.15"
__version__ = "0.9"

class UI(QtWidgets.QMainWindow):

    def __init__(self, ip, threads=1, fps=10, sType='zmq'):
        super(UI, self).__init__()
        self.ip = ip
        self.setupUI()
        self.setupReceivers(self.ip, threads, sType)
        self.show()
                
        #frame rate calculations
        self.startTime = datetime.datetime.now().time()
        self.imageCounter = 0
        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.updateFrameRate)
        self.timer.start(300)
        
        #display refresh frequency
        self.fps = fps
        self.displayTimer = pg.QtCore.QTimer()
        self.displayTimer.timeout.connect(self.updateImageView)
        self.displayTimer.start(1/self.fps*1000)    
        log.info(f"max. display refresh rate: {self.fps} Hz")
        
        #detector status information update
        self.statusUpdater = StatusUpdater.StatusUpdater(self.ip)
        self.statusUpdater.start()
        self.statusUpdater.signals.detectorStatus.connect(self.updateStatus)
        
    def setupUI(self):
        self.setWindowTitle("STRELA -- Stream LiveView App")
        self.resize(1000,1000)

        self.centralWidget = QtWidgets.QSplitter(self)
        self.setCentralWidget(self.centralWidget)
        self.layout = QtWidgets.QHBoxLayout(self.centralWidget)

        pg.setConfigOptions(imageAxisOrder='row-major')
        
        self.plotItemReal = pg.PlotItem(title="")
        self.imageViewReal = pg.ImageView(view=self.plotItemReal)
        self.centralWidget.addWidget(self.imageViewReal)
        self.imageViewReal.keyPressEvent = self.keyPressEvent
        self.imageViewReal.scene.sigMouseMoved.connect(self.mouseMoved)
  
        self.imageData = None
        welcomeImage = tifffile.imread(os.path.join("ressources","strela.tif"))      
        self.imageViewReal.setImage(welcomeImage)
        self._imagesDisplayed = 0

        self.setupStatusBar()

    def setupStatusBar(self):
        self.statusBar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusBar)

        widget = QtWidgets.QWidget()
        horizontalLayout = QtWidgets.QHBoxLayout()
        widget.setLayout(horizontalLayout)

        self.labelCoordinates = QtWidgets.QLabel(self.centralWidget)
        horizontalLayout.addWidget(self.labelCoordinates)
        self.labelCoordinates.setText("I(x, y)")

        spacerItem = PyQt5.QtWidgets.QSpacerItem(10000, 0, PyQt5.QtWidgets.QSizePolicy.Expanding,
                                                PyQt5.QtWidgets.QSizePolicy.Expanding)
        horizontalLayout.addItem(spacerItem)

        self.labelImagesDisplayed = QtWidgets.QLabel(self.centralWidget)
        horizontalLayout.addWidget(self.labelImagesDisplayed)
        self.labelImagesDisplayed.setText("images displayed: 0")
                
        self.labelFrameRate = QtWidgets.QLabel(self.centralWidget)
        horizontalLayout.addWidget(self.labelFrameRate)
        
        horizontalLayout.addItem(spacerItem)

        #detector states
        self.statusZmq = QtWidgets.QLabel('Stream: na', self.centralWidget)
        self.statusMonitor = QtWidgets.QLabel('Monitor: na', self.centralWidget)
        self.statusDetector = QtWidgets.QLabel('Detector: na', self.centralWidget)
        horizontalLayout.addWidget(self.statusZmq)
        horizontalLayout.addWidget(self.statusMonitor)
        horizontalLayout.addWidget(self.statusDetector)

        self.statusBar.addWidget(widget)

    def mouseMoved(self, viewPos):
        """
        show x,y coordinates and pixel value for mouse position
        """
        try:
            data = self.imageViewReal.image
            nRows, nCols = data.shape

            scenePos = self.imageViewReal.getImageItem().mapFromScene(viewPos)
            row, col = int(scenePos.y()), int(scenePos.x())

            if 0 <= row and row < nRows and 0 <= col and col < nCols:
                value = data[row,col]
                self.labelCoordinates.setText("I(%d,%d) = %d" % (col, row, value))

            else:
                self.labelCoordinates.setText("I(x,y) = NaN")

        except Exception as e:
            self.labelCoordinates.setText("Error: %s"%e)

    def updateImageView(self):
        """
        update image if new one available
        """
        if self.imageData is not None:
            self._imagesDisplayed += 1
            log.debug("plot image {} ({} {})".format(self._imagesDisplayed, self.imageData.shape, self.imageData.dtype))
            self.imageViewReal.setImage(self.imageData, autoRange=False,
                                autoLevels=False, autoHistogramRange= False)
        self.imageData = None

    def updateData(self, data):
        self.imageData = data
        self.imagesReceived += 1
                
    def updateFrameRate(self):
        dImages = self._imagesDisplayed - self.imageCounter
        self.labelImagesDisplayed.setText("images received: {}".format(self.imagesReceived))
        
        t = datetime.datetime.now().time()
        dt = t.second - self.startTime.second + (t.microsecond-self.startTime.microsecond)/1000000
        frameRate = dImages/dt
        self.labelFrameRate.setText(f"display {frameRate:.1f} fps")
        self.startTime = datetime.datetime.now().time() 
        self.imageCounter = self._imagesDisplayed
        return frameRate

    def setupReceivers(self, ip, threads=1, sType='zmq'):
        self.imagesReceived = 0
        log.info(f"starting {threads} {sType} receiver(s)")
        if sType == 'monitor':
            self.receivers = [MonitorReceiver.MonitorReceiver(ip, port=80, name = i+1) for i in range(threads)]
        elif sType == 'zmq':
            self.receivers = [ZmqReceiver.ZMQReceiver(ip, port=9999, name = i+1) for i in range(threads)]
        elif sType == 'dummy':
            self.receivers = [DummyReceiver.DummyReceiver(ip, port=9999, name = i+1) for i in range(threads)]

        else:
            log.info(f'receiver type {sType} unknown, using zmq')
            self.receivers = [ZmqReceiver.ZMQReceiver(ip, port=9999, name = i+1) for i in range(threads)]

        for receiver in self.receivers:
            receiver.start()
            receiver.signals.dataReceived.connect(self.updateData)        

    def updateStatus(self, status):
        self.statusUpdater.setStatus(self.statusDetector, status['det'])
        self.statusUpdater.setStatus(self.statusMonitor, status['monitor'])
        self.statusUpdater.setStatus(self.statusZmq, status['stream'])

def parseArgs():
    parser = argparse.ArgumentParser(description='STRELA LiveView for DECTRIS detectors')
    parser.add_argument('ip', type=str, help="DECTRIS detector IP or hostname")
    parser.add_argument('--nThreads', '-n', type=int, default=1, help="number of receiver threads")
    parser.add_argument('--fps', '-f', type=float, default=10.0, help="display refresh rate in Hz")
    parser.add_argument('--stream', '-s', type=str, default="zmq", help="interface to use: [zmq|monitor|dummy]")

    return parser.parse_args()

if __name__ == "__main__":        
    signal.signal(signal.SIGINT, signal.SIG_DFL) #enable ctrl + c abort   
    
    try:    
        args = parseArgs()
        app = QtGui.QApplication(sys.argv)
        app.setWindowIcon(QtGui.QIcon(os.path.join("ressources","icon.png")))
        app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        ui = UI(args.ip, args.nThreads, args.fps, args.stream)
        
    except (Exception, KeyboardInterrupt) as e:
        log.error(e)
        
    finally:
        sys.exit(app.exec_())