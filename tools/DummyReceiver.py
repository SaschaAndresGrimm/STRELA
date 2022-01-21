from PyQt5.QtCore import QTimer, QRunnable, QThread, pyqtSlot, pyqtSignal, QObject, QEventLoop
import traceback
import time, logging, datetime, tifffile, sys, numpy

logging.basicConfig()
log = logging.getLogger(__name__)

class DummyReceiver(QRunnable):
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
        gauss = numpy.random.normal(1.5, 0.5, (row,col))
        gauss = gauss.reshape(row,col)
        noisy = self.data + self.data * gauss
        self.signals.dataReceived.emit(noisy)
 
    @pyqtSlot()       
    def run(self):
        while True:
           self.receive()
           time.sleep(0.05)
                    
class WorkerSignals(QObject):
    error = pyqtSignal(tuple)
    dataReceived = pyqtSignal(object)