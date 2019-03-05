from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import QTimer, QThread, pyqtSlot, pyqtSignal, QObject, QThread

import sys, logging, os, time, traceback

from .tools import camera

PATH = os.path.abspath(__file__)
DIRPATH = os.path.dirname(PATH)

class Status(QWidget):
    ipChanged = pyqtSignal(str)
    statusSignal = pyqtSignal(bool)

    def __init__(self, ip):
        super().__init__()
        self.ui = loadUi(os.path.join(DIRPATH, "ui","status.ui"), self)
        self.detectorIP.returnPressed.connect(self.onIPChanged)
        self.ip = ip
        self.detectorIP.setText(self.ip)
        self.statusUpdater = StatusUpdater(self.ip)
        self.statusUpdater.signals.result.connect(self.updateStatus)
        self.statusUpdater.start()

    @pyqtSlot(dict)
    def updateStatus(self, status):
        logging.debug("status: {}".format(status))
        self.statusHumidity.setValue(status["humidity"])
        self.statusTemperature.setValue(status["temperature"])
        self.statusState.setText(status["state"])
        self.statusSignal.emit(True) #status["state"] not in ["error","NA"])
        #TODO: implement useful status signal to activate/deactivate control pannel and/or start user initialize dialog

    def onIPChanged(self):
        self.ip = self.detectorIP.text()
        self.statusUpdater.setIP(self.ip)
        logging.debug("IP changed to {}".format(self.ip))
        self.ipChanged.emit(self.ip)

class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)

class StatusUpdater(QThread):
    def __init__(self, ip, *args, **kwargs):
        super(StatusUpdater, self).__init__()
        self.ip = ip
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.setupClient()

    def setupClient(self):
        self.client = camera.Client(self.ip)

    def setIP(self, ip):
        self.ip = ip
        self.setupClient()

    def getState(self, key, default=None):
        status = self.client.query("detector","status",key)
        if status:
            return status["value"]
        else:
            return default

    @pyqtSlot()
    def run(self):
        while True:
            try:
                status = self.getState("state","NA")
                temperature = self.getState("board_000/th0_temp",-1)
                humidity = self.getState("board_000/th0_humidity",-1)
                result = {"state":status, "temperature":temperature, "humidity":humidity}
            except:
                traceback.print_exc()
                exctype, value = sys.exc_info()[:2]
                self.signals.error.emit((exctype, value, traceback.format_exc()))
            else:
                self.signals.result.emit(result)
            finally:
                self.signals.finished.emit()
                time.sleep(2)

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)
    app = QApplication(sys.argv)
    status = Status("192.168.30.62")
    status.show()
    sys.exit(app.exec_())
