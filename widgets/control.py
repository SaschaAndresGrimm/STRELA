from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import pyqtSlot

import logging
import sys, os

from .tools import camera
from . import status, files, receiver, acquisition

PATH = os.path.abspath(__file__)
DIRPATH = os.path.dirname(PATH)


class DetectorControl(QWidget):
    def __init__(self, ip="10.42.41.10"):
        super().__init__()
        self.ui = loadUi(os.path.join(DIRPATH,"ui","controlPannel.ui"), self)
        self.ip = ip

        self.setupClient()

        self.receiver = receiver.Receiver(self.ip)
        self.ui.receiverLayout.addWidget(self.receiver)

        self.files = files.Files(self.ip)
        self.ui.filesLayout.addWidget(self.files)

        self.acquisition = acquisition.Acquisition(self.ip)
        self.ui.controlLayout.addWidget(self.acquisition)

        self.status = status.Status(self.ip)
        self.ui.statusLayout.addWidget(self.status)

        self.status.ipChanged.connect(self.setIP)
        self.status.ipChanged.connect(self.receiver.setIP)
        self.status.ipChanged.connect(self.files.setIP)
        self.status.ipChanged.connect(self.acquisition.setIP)

        self.status.statusSignal.connect(self.controlPannel.setEnabled)

        self.controlPannel.currentChanged.connect(self.files.onButtonUpdate)

    def setupClient(self):
        self.client = camera.Client(self.ip)

    @pyqtSlot(str)
    def setIP(self, ip):
        self.ip = ip
        self.setupClient()

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s %(message)s', level=logging.DEBUG)
    app = QApplication(sys.argv)
    detectorControl = DetectorControl(ip="0.0.0.0")
    detectorControl.show()
    sys.exit(app.exec_())
