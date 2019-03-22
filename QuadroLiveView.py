"""
Demonstrate basic use of a ZMQ LiveView
"""
import logging

import PyQt5
from PyQt5 import QtWidgets
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg
import pyqtgraph.ptime as ptime

import qdarkstyle

from widgets import control

import sys, os
import tifffile

__author__ = "SasG"
__date__ = "3/03/19"
__version__ = "0.5"
__reviewer__ = ""

class UI(QtWidgets.QMainWindow):

    def __init__(self, maxFrameRate=16):
        super(UI, self).__init__()
        self.setupUI()

        self._maxFrameRate = maxFrameRate
        self._imagesDisplayed = 0

        self.show()

    def setupUI(self):
        self.setWindowTitle("#MakE\'M Count")
        self.resize(1500,300)

        self.centralWidget = QtWidgets.QSplitter(self)
        self.setCentralWidget(self.centralWidget)
        self.layout = QtWidgets.QHBoxLayout(self.centralWidget)

        pg.setConfigOptions(imageAxisOrder='row-major')

        imgData = tifffile.imread(os.path.join("ressources","logo.tif"))
        self.plotItemReal = pg.PlotItem(title="real")
        self.imageViewReal = pg.ImageView(view=self.plotItemReal)
        self.centralWidget.addWidget(self.imageViewReal)
        self.imageViewReal.keyPressEvent = self.keyPressEvent
        self.imageViewReal.scene.sigMouseMoved.connect(self.mouseMoved)
        self.imageViewReal.setImage(imgData)

        self.plotItemFFT = pg.PlotItem(title="FFT")
        self.imageViewFFT = pg.ImageView(view=self.plotItemFFT)
        self.imageViewFFT.keyPressEvent = self.keyPressEvent
        self.centralWidget.addWidget(self.imageViewFFT)
        self.imageViewFFT.setImage(imgData)

        self.setupcontrolPannel()
        self.setupStatusBar()

    def setupcontrolPannel(self):
        self.controlPannel = control.DetectorControl("10.42.41.10")
        self.centralWidget.addWidget(self.controlPannel)
        handle = self.centralWidget.handle(1)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        button = QtWidgets.QToolButton(handle)
        button.setArrowType(QtCore.Qt.LeftArrow)
        button.clicked.connect(
            lambda: self.handleSplitterButton(True))
        layout.addWidget(button)
        button = QtWidgets.QToolButton(handle)
        button.setArrowType(QtCore.Qt.RightArrow)
        button.clicked.connect(
            lambda: self.handleSplitterButton(False))
        layout.addWidget(button)
        handle.setLayout(layout)

        self.controlPannel.receiver.dataReceived.connect(self.updateData)

    def handleSplitterButton(self, left=True):
        if not all(self.centralWidget.sizes()):
            self.centralWidget.setSizes([1, 1])
        elif left:
            self.centralWidget.setSizes([0, 1])
        else:
            self.centralWidget.setSizes([1, 0])

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

        self.statusBar.addWidget(widget)

    def mouseMoved(self, viewPos):
        try:
            data = self.imageViewReal.image
            nRows, nCols = data.shape

            scenePos = self.imageViewReal.getImageItem().mapFromScene(viewPos)
            row, col = int(scenePos.y()), int(scenePos.x())

            if 0 <= row and row < nRows and 0 <= col and col < nCols:
                value = data[col,row]
                self.labelCoordinates.setText("x %d, y %d, I %.1f" % (row, col, float(value)))

            else:
                self.labelCoordinates.setText("x, y, I")

        except Exception as e:
            self.labelCoordinates.setText("Error: %s"%e)

    def keyPressEvent(self, ev):
        if ev.key() == QtCore.Qt.Key_Space:
            self.controlPannel.receiver.buttonLiveView.toggle()

    def updateData(self, data):
        if data is not None:
            self._imagesDisplayed += 1
            logging.info("image received, {} {}".format(data["real"].shape, data["real"].dtype))
            self.imageViewReal.setImage(data["real"], autoRange=False,
                                autoLevels=False, autoHistogramRange= False)
            self.imageViewFFT.setImage(data["fft"], autoRange=False,
                                autoLevels=False, autoHistogramRange= False)
            self.labelImagesDisplayed.setText("images displayed: {}".format(self._imagesDisplayed))

if __name__ == "__main__":
    try:
        logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)
        app = QtGui.QApplication(sys.argv)
        app.setWindowIcon(QtGui.QIcon(os.path.join("ressources","icon.png")))
        app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        ui = UI()
    except Exception as e:
        logging.error(e)
    finally:
        sys.exit(app.exec_())
