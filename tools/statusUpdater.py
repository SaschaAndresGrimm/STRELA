from PyQt5.QtCore import QThread, pyqtSlot, pyqtSignal, QObject, QThread
import traceback
import logging, time
from . import DEigerClient

class StatusUpdater(QThread):
    def __init__(self, ip, port=80, *args, **kwargs):
        super(StatusUpdater, self).__init__()
        self.ip = ip
        self.port = port
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
                
        self.client = DEigerClient.DEigerClient(self.ip, self.port)            
            
    def getStatus(self):
        """
        update detector, monitor, and stream state in status bar
        """
        try:
            logging.debug("updating detector status")
            client = DEigerClient.DEigerClient(self.ip)
            detectorStatus = client.detectorStatus('state')['value']
            streamStatus = client.streamStatus('state')['value']
            monitorStatus = client.monitorStatus('state')['value']   

            self.signals.detectorStatus.emit({"det":detectorStatus,
                                              "stream":streamStatus,
                                              "monitor":monitorStatus})
                
        except Exception as e:
            logging.error(f'failure during status update: {e}')

    @pyqtSlot()
    def run(self):
        while True:
            try:
                self.getStatus()
                time.sleep(1)
            except:
                traceback.print_exc()
                exctype, value = sys.exc_info()[:2]
                self.signals.error.emit((exctype, value, traceback.format_exc()))
            finally:
                time.sleep(3)
                
class WorkerSignals(QObject):
    error = pyqtSignal(tuple)
    detectorStatus = pyqtSignal(object)