from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import QTimer, QThread, pyqtSlot, pyqtSignal, QObject
import traceback
import time, logging, datetime, tifffile, sys, numpy

logging.basicConfig()
log = logging.getLogger(__name__)

class DummyReceiver(QThread):
    def __init__(self, ip, port=80, name=None, *args, **kwargs):
        super(DummyReceiver, self).__init__()
        self.ip = ip
        self.port = port
        self.name = name
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        
        self.data = tifffile.imread('./ressources/strela.tif')
                                
    def receive(self):
        """
        return noisy image data
        """
        log.debug("dummy receiver {} generating data".format(self.name))
        row,col = self.data.shape
        gauss = numpy.random.randn(row,col)
        gauss = gauss.reshape(row,col)
        noisy = self.data + self.data * gauss
        self.signals.dataReceived.emit(noisy)

    @pyqtSlot()
    def run(self):
        # wait 10s, afterward return noisy images with approx 20Hz
        time.sleep(10)
        while True:
            try:
                self.receive() 
                time.sleep(0.04)
            except:
                traceback.print_exc()
                exctype, value = sys.exc_info()[:2]
                self.signals.error.emit((exctype, value, traceback.format_exc()))
                
class WorkerSignals(QObject):
    error = pyqtSignal(tuple)
    dataReceived = pyqtSignal(object)