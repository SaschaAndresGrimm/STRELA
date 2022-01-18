from PyQt5.QtCore import QThread, pyqtSlot, pyqtSignal, QObject
import traceback
import logging, time, sys
from . import DEigerClient

logging.basicConfig()
log = logging.getLogger(__name__)

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
            log.debug("updating detector status")
            client = DEigerClient.DEigerClient(self.ip)

            status = {"det": client.detectorStatus('state')['value'],
                    "stream": client.streamStatus('state')['value'],
                    "monitor": client.monitorStatus('state')['value']
                    }
                
        except Exception as e:
            log.error(f'failure during detector status update: {e}')

            status = {"det": "no connection",
                    "stream": "no connection",
                    "monitor": "no connection"
                }         
    
        finally:
            self.signals.detectorStatus.emit(status)
            
            
    def setStatus(self, widget, status):
        text = widget.text()
        newText = f'{text.split(":")[0]}: {status}'
        widget.setText(newText)
        if status in ['error','na', 'disabled', 'no connection']:
            widget.setStyleSheet("background-color: red")
        elif status in ['overflow', 'initialize', 'configure']:
            widget.setStyleSheet("background-color: orange")
        elif status in ['acquire']:
            widget.setStyleSheet("background-color: blue")
        else:
            widget.setStyleSheet("background-color: green")

    @pyqtSlot()
    def run(self):
        while self.isRunning():
            try:
                self.getStatus()
            except:
                traceback.print_exc()
                exctype, value = sys.exc_info()[:2]
                self.signals.error.emit((exctype, value, traceback.format_exc()))
            finally:
                time.sleep(1)
                
class WorkerSignals(QObject):
    error = pyqtSignal(tuple)
    detectorStatus = pyqtSignal(object)