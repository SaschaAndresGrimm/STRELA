from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QApplication, QWidget, QCheckBox, QFileDialog
from PyQt5.QtCore import pyqtSlot, QThread, QObject, pyqtSignal, QRunnable, QThreadPool, QTimer

import traceback
import urllib.request, requests
import sys, logging, os, time

from .tools import camera

PATH = os.path.abspath(__file__)
DIRPATH = os.path.dirname(PATH)

class Files(QWidget):
    ipChanged = pyqtSignal(str)

    def __init__(self, ip):
        super().__init__()
        self.ui = loadUi(os.path.join(DIRPATH, "ui", "files.ui"), self)
        self.threadpool = QThreadPool()
        self.ip = ip
        self._setButtons()
        self.fileList = []
        self.setupClient()
        self.updateFiles()

    def _setButtons(self):
        self.buttonUpdate.clicked.connect(self.onButtonUpdate)
        self.buttonClear.clicked.connect(self.onButtonClear)
        self.buttonDownload.clicked.connect(self.onButtonDownload)
        self.buttonSelect.clicked.connect(self.onButtonSelect)
        self.buttonUnselect.clicked.connect(self.onButtonUnselect)

    def setupClient(self):
        self.client = camera.Client(self.ip)
        setter = Worker(self.setFileWriterSettings)
        self.threadpool.start(setter)
        self.updateFiles()

    @pyqtSlot(str)
    def setIP(self, ip):
        self.ip = ip
        self.setupClient()

    def setFileWriterSettings(self):
        self.client.query("filewriter","config","mode", "enabled")
        self.client.query("filewriter","config","nimages_per_file", 1000)
        self.client.query("filewriter","config","compression_enabled", True)
        self.client.query("detector","config","compression", "lz4")
        self.client.query("filewriter","config","name_pattern", "LiveView_$id")

    def updateFiles(self):
        logging.debug("updateFiles")
        [f.deleteLater()  for f in self.fileList]
        self.fileList = self.getFileList()

    def getFileList(self):
        fileList = self.client.listFiles()
        logging.debug(self.fileList)
        items = [QCheckBox(f) for f in fileList]
        [self.ui.fileLayout.addWidget(item) for item in items]
        return items

    def onButtonUpdate(self):
        self.updateFiles()

    def onButtonClear(self):
        fileList = [f.text() for f in self.fileList if f.isChecked()]
        deleter = Deleter(self.ip, fileList)
        deleter.signals.result.connect(self.statusText.setText)
        deleter.signals.progress.connect(self.progressBar.setValue)
        deleter.signals.finished.connect(self.updateFiles)
        self.threadpool.start(deleter)

    def onButtonDownload(self):
        fpath = str(QFileDialog.getExistingDirectory(self, "Select a Directory"))
        if len(fpath) > 0:
            downloadList = [f.text() for f in self.fileList if f.isChecked()]
            downloader = Downloader(self.ip, downloadList, fpath)
            downloader.signals.result.connect(self.statusText.setText)
            downloader.signals.progress.connect(self.progressBar.setValue)

            self.threadpool.start(downloader)

    def onButtonSelect(self):
        for f in self.fileList:
            f.setChecked(True)

    def onButtonUnselect(self):
        for f in self.fileList:
            f.setChecked(False)


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

class Downloader(QRunnable):
    def __init__(self, ip, fileList, fpath=".", *args, **kwargs):
        super(Downloader, self).__init__()
        self.fileList = fileList
        self.fpath = fpath
        self.ip = ip
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def download(self):
        logging.debug("download {} to {}".format(self.fileList, self.fpath))
        self.signals.progress.emit(0)
        for index, item in enumerate(self.fileList):
            self.signals.progress.emit(round(100./len(self.fileList)*(index)))
            self.downloadItem(item, self.fpath)
        return "downloaded {} files to {}".format(len(self.fileList), self.fpath)

    def downloadItem(self, item, path):
        src = "http://{}/data/{}".format(self.ip, item)
        dest = os.path.join(path, item)
        self.signals.result.emit("copy {}".format(item))
        urllib.request.urlretrieve(src, dest)
        self.signals.result.emit("copied {}".format(item))
        logging.info("downloaded {} to {}".format(src, self.fpath))

    @pyqtSlot()
    def run(self):
        try:
            result = self.download(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
            self.signals.progress.emit(0)
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()
            self.signals.progress.emit(100)

class Deleter(QRunnable):
    def __init__(self, ip, fileList, fpath=".", *args, **kwargs):
        super(Deleter, self).__init__()
        self.fileList = fileList
        self.ip = ip
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def download(self):
        logging.debug("deleting {}".format(self.fileList))
        self.signals.progress.emit(0)
        for index, item in enumerate(self.fileList):
            self.signals.progress.emit(round(100./len(self.fileList)*(index)))
            self.deleteItem(item)
        return "deleted {} items".format(len(self.fileList))

    def deleteItem(self, item):
        src = "http://{}/data/{}".format(self.ip, item)
        self.signals.result.emit("delete {}".format(item))
        requests.delete(src)
        self.signals.result.emit("deleted {}".format(item))
        logging.info("deleted {}".format(src))

    @pyqtSlot()
    def run(self):
        try:
            result = self.download(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
            self.signals.progress.emit(0)
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()
            self.signals.progress.emit(100)


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)
    app = QApplication(sys.argv)
    files = Files("192.168.30.62")
    files.show()
    sys.exit(app.exec_())
