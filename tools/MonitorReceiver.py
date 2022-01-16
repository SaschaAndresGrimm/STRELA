from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import QTimer, QThread, pyqtSlot, pyqtSignal, QObject
import traceback
import time, logging, json, datetime, tifffile, io, sys, numpy
from . import DEigerClient

logging.basicConfig()
log = logging.getLogger(__name__)

class MonitorReceiver(QThread):
    def __init__(self, ip, port=80, name=None, *args, **kwargs):
        super(MonitorReceiver, self).__init__()
        self.ip = ip
        self.port = port
        self.name = name
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        
        self.client = DEigerClient.DEigerClient(self.ip, self.port)
                
        self.enableStream()
        
    def enableStream(self):
        log.debug(f'enabling monitor on {self.ip}')
        resp = self.client.setMonitorConfig('mode','enabled')

    def receive(self):
        """
        receive and remit QT signal with image data
        """
        log.debug("monitor receiver {} polling {}:{}".format(self.name, self.ip, self.port))
        try:
            frame = self.client.monitorImages("monitor")
            return self.processFrames(frame)
        except Exception as e:
            log.error(f'monitos {self.name} error: {e}')

    def processFrames(self, frame):
        data = tifffile.imread(io.BytesIO(frame))

        # workaround strange pyqtgraph/np bug, where histogram cannot be built for empty data
        data[0,0] = -1
        data[-1,0] = -1
        data[0,-1] = -1
        data[-1,-1] = -1
        
        # set overflow values to 0 for better contrast
        data[data==(2**(8*data.itemsize)-1)] = 0
                        
        return data

    @pyqtSlot()
    def run(self):
        self.data = numpy.ndarray((512,512), dtype='uint32')
        while True:
            try:
                #poll as fast as possible, will be just approx 2Hz
                data =  self.receive() 
                #lazy way to check if new image frame was polled (likely)
                if data is not None and (numpy.sum(self.data) != numpy.sum(data)):
                    self.signals.dataReceived.emit(data)
                    self.data = data
            except:
                traceback.print_exc()
                exctype, value = sys.exc_info()[:2]
                self.signals.error.emit((exctype, value, traceback.format_exc()))
                
class WorkerSignals(QObject):
    error = pyqtSignal(tuple)
    dataReceived = pyqtSignal(object)