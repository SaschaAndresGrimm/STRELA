from PyQt5 import QtCore, QtGui, QtWidgets
import logging, time

from .CollapsibleBox import CollapsibleBox
from tools.EigerClient import EigerClient
from tools.Worker import Worker

logging.basicConfig()
log = logging.getLogger(__name__)

#need proper rewriting of eigerclient using pyqt signals

class ConvenienceFunc(CollapsibleBox):
    def __init__(self, ip, port=80, title="Quick Acquisition", parent=None):
        super(ConvenienceFunc, self).__init__(title, parent)
        self.ip = ip
        self.port = port
        self.client = EigerClient(self.ip, self.port)
        self.threadPool = QtCore.QThreadPool()
        
        self.vbox = QtWidgets.QVBoxLayout()
        
        self.buttonContinuous = QtWidgets.QPushButton(self)
        self.buttonContinuous.setText('Continuous')
        self.buttonContinuous.setCheckable(True)
        self.buttonContinuous.clicked.connect(self.onContinuous)
        self.vbox.addWidget(self.buttonContinuous)  
        
        self.buttonSingleShot = QtWidgets.QPushButton(self)
        self.buttonSingleShot.setText('Single Shot')
        self.buttonSingleShot.clicked.connect(lambda: self.onSingleShot(1))
        self.vbox.addWidget(self.buttonSingleShot)               
        
        self.setContentLayout(self.vbox)
    
    def onSingleShot(self, exposureTime=1):
        log.info(f'preparing {exposureTime} s single exposure')
        self.client.setStreamConfig('mode','enabled')
        self.client.setDetectorConfig('count_time', exposureTime)
        self.client.setDetectorConfig('frame_time', exposureTime)
        self.client.setDetectorConfig('trigger_mode', 'ints')
        self.client.setDetectorConfig('nimages', 1)
        self.client.setDetectorConfig('ntrigger', 1)
        
        log.info(f'starting {exposureTime} s single exposure')        
        worker = Worker(lambda: self.client.sendDetectorCommand('arm'))
        self.threadPool.start(worker)
        worker.signals.finished.connect(lambda: self.client.sendDetectorCommand('trigger'))
        
    def onContinuous(self):
        frameRate = 20
        
        if self.buttonContinuous.isChecked():
            self.buttonContinuous.setText('STOP')
            
            log.info(f'preparing continuous {frameRate} Hz exposure')
            self.client.setStreamConfig('mode','enabled')
            self.client.setDetectorConfig('count_time', 1./frameRate)
            self.client.setDetectorConfig('frame_time', 1./frameRate)
            self.client.setDetectorConfig('trigger_mode', 'ints')
            self.client.setDetectorConfig('nimages', frameRate*24*60*60)
            self.client.setDetectorConfig('ntrigger', 1)
            
            log.info(f'starting continuous exposure')
            worker = Worker(lambda: self.client.sendDetectorCommand('arm'))
            self.threadPool.start(worker)
            worker.signals.finished.connect(lambda: self.client.sendDetectorCommand('trigger'))
            
            worker = Worker(self.checkIdle)
            self.threadPool.start(worker)
            worker.signals.finished.connect(self.onContinuous)
            
        else:
            self.buttonContinuous.setText('Continuous')
            self.client.sendDetectorCommand('abort')
            log.info('stopped continuous acquisition')
            

    @QtCore.pyqtSlot()
    def checkIdle(self):
        time.sleep(5)
        while self.client.detectorStatus('state')['value'] in ['acquire',]:
            time.sleep(1)
        self.buttonContinuous.setChecked(False)
        return