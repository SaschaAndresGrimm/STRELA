from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QApplication, QWidget, QCheckBox
from PyQt5.QtCore import pyqtSlot, QThread, QObject, pyqtSignal, QRunnable, QThreadPool, QTimer

import traceback
import sys, logging, os, time

from .tools import camera

PATH = os.path.abspath(__file__)
DIRPATH = os.path.dirname(PATH)

class Acquisition(QWidget):

    def __init__(self, ip):
        super().__init__()
        self.ui = loadUi(os.path.join(DIRPATH, "ui", "acquisition.ui"), self)
        self.threadpool = QThreadPool()
        self.setUpButtons()
        self.setIP(ip)

    def setupClient(self):
        self.client = camera.Client(self.ip)
        getter = Worker(self.getAcquisitionSettings)
        self.threadpool.start(getter)

    @pyqtSlot(str)
    def setIP(self, ip):
        self.ip = ip
        self.setupClient()

    def getAcquisitionSettings(self):
        self.client.query("detector","config","compression", "lz4")
        self._getValue(("detector","config","nimages"), self.settingNimages.setValue)
        self._getValue(("detector","config","ntrigger"), self.settingNtrigger.setValue)
        self._getValue(("detector","config","frame_time"), self.settingFrameTime.setValue)
        self._getValue(("detector","config","count_time"), self.settingExposureTime.setValue)
        self._getValue(("detector","config","threshold_energy"), self.settingThreshold.setValue)
        self._getValue(("filewriter","config","name_pattern"), self.settingFileName.setText)
        self._getValue(("detector","config","trigger_mode"), self._setTriggerMode)

    def _getValue(self, param, fnSet):
        try:
            values = self.client.query(*param)
            if values:
                fnSet(values["value"])
                self.statusText.setText("set {} to {}".format(param[-1],values["value"]))
        except:
            self.statusText.setText("cannot set {}".format(param[-1]))

    def _setTriggerMode(self, value):
        index = self.settingTriggerMode.findText(value)
        if index >= 0:
            self.settingTriggerMode.setCurrentIndex(index)

    def _setValue(self, param, value, timeout=2):
        logging.info("set {} to {} with timeout {} s".format(param, value, timeout))
        self.client.query(*param, value, timeout=timeout)
        getter = Worker(self.getAcquisitionSettings)
        self.threadpool.start(getter)

    def setUpButtons(self):
        self.buttonAcquire.clicked.connect(self.onAcquire)
        self.buttonDisarm.clicked.connect(self.onDisarm)
        self.buttonCancel.clicked.connect(self.onCancel)
        self.buttonAbort.clicked.connect(self.onAbort)
        self.buttonInitialize.clicked.connect(self.onInitialize)
        self.buttonDAQRestart.clicked.connect(self.onDAQRestart)
        self.buttonReboot.clicked.connect(self.onReboot)

        self.settingNimages.editingFinished.connect(self.onNimages)
        self.settingNtrigger.editingFinished.connect(self.onNtrigger)
        self.settingTriggerMode.currentIndexChanged.connect(self.onTriggerMode)
        self.settingExposureTime.editingFinished.connect(self.onExposureTime)
        self.settingFrameTime.editingFinished.connect(self.onFrameTime)
        self.settingThreshold.editingFinished.connect(self.onThreshold)
        self.settingFileName.editingFinished.connect(self.onFileName)


    def onAcquire(self):
        acquirer = Worker(self.acquire)
        self.threadpool.start(acquirer)

    def acquire(self):
        try:
            self.buttonAcquire.setEnabled(False)
            self.statusText.setText("starting acquisition")
            self.client.query("detector","command","arm",True)
            self.statusText.setText("armed")
            time.sleep(.1)

            if "ext" in self.settingTriggerMode.currentText():
                self.statusText.setText("waiting for external triggers")
            else:
                for t in range(self.settingNtrigger.value()):
                    self.statusText.setText("triggered trigger {}".format(t+1))
                    self.client.query("detector","command","trigger",True, timeout=None)

            acquiring = True
            while acquiring:
                status = self.client.query("detector","status","state")
                if status is None:
                    acquiring = False
                elif status["value"] not in ["acquire", "ready", "configure"]:
                    acquiring = False
                else:
                    time.sleep(0.5)

        except Exception as e:
            logging.error(e)
            self.statusText.setText(str(e))
        else:
            self.statusText.setText("acquisition successful")
        finally:
            self.client.query("detector","command","disarm",True)
            self.buttonAcquire.setEnabled(True)

    def onDisarm(self):
        self._setValue(param=("detector","command","disarm"),value=True)
    def onCancel(self):
        self._setValue(param=("detector","command","cancel"),value=True)
    def onAbort(self):
        self._setValue(param=("detector","command","abort"),value=True)
    def onInitialize(self):
        self._setValue(param=("detector","command","initialize"),value=True, timeout=30)
    def onDAQRestart(self):
        self._setValue(param=("detector","command","restart"),value=True, timeout=30)
    def onReboot(self):
        self._setValue(param=("detector","command","reboot"),value=True, timeout=180)

    def onNimages(self):
        self._setValue(param=("detector","config","nimages"),value=self.settingNimages.value())
    def onNtrigger(self):
        self._setValue(param=("detector","config","ntrigger"),value=self.settingNtrigger.value())
    def onTriggerMode(self):
        self._setValue(param=("detector","config","trigger_mode"),value=self.settingTriggerMode.currentText())
    def onExposureTime(self):
        self._setValue(param=("detector","config","count_time"),value=self.settingExposureTime.value())
    def onFrameTime(self):
        self._setValue(param=("detector","config","frame_time"),value=self.settingFrameTime.value())
    def onThreshold(self):
        self._setValue(param=("detector","config","threshold_energy"),value=self.settingThreshold.value())
    def onFileName(self):
        self._setValue(param=("filewriter","config","name_pattern"),value=self.settingFileName.text())


class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)

class Worker(QRunnable):
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)
    app = QApplication(sys.argv)
    acquisition = Acquisition("192.168.30.62")
    acquisition.show()
    sys.exit(app.exec_())
