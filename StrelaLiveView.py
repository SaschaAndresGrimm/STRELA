"""
Basic implementation of a ZMQ LiveView for DECTRIS detector
"""
import PyQt5
from PyQt5 import QtWidgets
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
import qdarkstyle
import signal


import logging
import sys, os, argparse, datetime
import tifffile
from tools import zmqReceiver

__author__ = "Sascha Grimm"
__date__ = "2022.01.14"
__version__ = "1.0"

DBGLVL = logging.INFO

class UI(QtWidgets.QMainWindow):

    def __init__(self, ip, threads=4):
        super(UI, self).__init__()
        self.setupUI()
        self.setupZmqReceivers(ip, threads)
        self._imagesDisplayed = 0
        self.show()
        
        for receiver in self.receivers:
            receiver.signals.dataReceived.connect(self.updateData)
            
        #frame time calculation
        self.startTime = datetime.datetime.now().time()
        self.imageCounter = 0
        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.updateFrameRate)
        self.timer.start(500)

    def setupUI(self):
        self.setWindowTitle("STRELA LiveView")
        self.resize(1000,1000)

        self.centralWidget = QtWidgets.QSplitter(self)
        self.setCentralWidget(self.centralWidget)
        self.layout = QtWidgets.QHBoxLayout(self.centralWidget)

        pg.setConfigOptions(imageAxisOrder='row-major')

        imgData = tifffile.imread(os.path.join("ressources","pizQuadro.tif"))
        
        self.plotItemReal = pg.PlotItem(title="")
        self.imageViewReal = pg.ImageView(view=self.plotItemReal)
        self.centralWidget.addWidget(self.imageViewReal)
        self.imageViewReal.keyPressEvent = self.keyPressEvent
        self.imageViewReal.scene.sigMouseMoved.connect(self.mouseMoved)
        self.imageViewReal.setImage(imgData)

        self.setupStatusBar()

    def setupStatusBar(self):
        self.statusBar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusBar)

        widget = QtWidgets.QWidget()
        horizontalLayout = QtWidgets.QHBoxLayout()
        widget.setLayout(horizontalLayout)

        self.labelCoordinates = QtWidgets.QLabel(self.centralWidget)
        horizontalLayout.addWidget(self.labelCoordinates)
        self.labelCoordinates.setText("x, y, z")

        spacerItem = PyQt5.QtWidgets.QSpacerItem(10000, 0, PyQt5.QtWidgets.QSizePolicy.Expanding,
                                                PyQt5.QtWidgets.QSizePolicy.Expanding)
        horizontalLayout.addItem(spacerItem)

        self.labelImagesDisplayed = QtWidgets.QLabel(self.centralWidget)
        horizontalLayout.addWidget(self.labelImagesDisplayed)
        self.labelImagesDisplayed.setText("images displayed: 0")
        
        horizontalLayout.addItem(spacerItem)
        
        self.labelFrameRate = QtWidgets.QLabel(self.centralWidget)
        horizontalLayout.addWidget(self.labelFrameRate)
        self.labelFrameRate.setText("display frame rate: NaN Hz")

        self.statusBar.addWidget(widget)

    def mouseMoved(self, viewPos):
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

    def updateData(self, data):
        if data is not None:
            self._imagesDisplayed += 1
            logging.debug("image {} received, {} {}".format(self._imagesDisplayed, data.shape, data.dtype))
            self.imageViewReal.setImage(data, autoRange=False,
                                autoLevels=False, autoHistogramRange= False)
            self.labelImagesDisplayed.setText("images displayed: {}".format(self._imagesDisplayed))
                
    def updateFrameRate(self):
        dImages = self._imagesDisplayed - self.imageCounter
        t = datetime.datetime.now().time()
        dt = t.second - self.startTime.second + (t.microsecond-self.startTime.microsecond)/1000000
        frameRate = dImages/dt
        self.labelFrameRate.setText(f"display frame rate: {frameRate:.1f} Hz")
        self.startTime = datetime.datetime.now().time() 
        self.imageCounter = self._imagesDisplayed
        return frameRate

    def setupZmqReceivers(self, ip, threads=1):
        self.receivers = [zmqReceiver.ZMQReceiver(ip, port=9999, name = i+1) for i in range(threads)]
        for receiver in self.receivers:
            receiver.start()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='STRELA LiveView for DECTRIS detectors')
    parser.add_argument('ip', type=str, help="DECTRIS detector IP or hostname")
    parser.add_argument('--nThreads', '-n', type=int, default=1, help="number of ZMQ receiver threads")
    args = parser.parse_args()
    
    signal.signal(signal.SIGINT, signal.SIG_DFL) #enable ctrl + c abort
    
    try:
        logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=DBGLVL)
        
        app = QtGui.QApplication(sys.argv)
        app.setWindowIcon(QtGui.QIcon(os.path.join("ressources","icon.png")))
        app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        ui = UI(args.ip, args.nThreads)
        
    except (Exception, KeyboardInterrupt) as e:
        logging.error(e)
        app.quit()
        
    finally:
        sys.exit(app.exec_())