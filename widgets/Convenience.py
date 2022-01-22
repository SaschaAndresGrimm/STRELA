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
        self.client.sendDetectorCommand('abort')
        self.client.setStreamConfig('mode','enabled')
        detectorConfig = [ ('count_time', exposureTime),
                            ('frame_time', exposureTime),
                            ('trigger_mode', 'ints'),
                            ('nimages', 1),
                            ('ntrigger', 1),
                            ]
        for config in detectorConfig:
            self.client.setDetectorConfig(*config)
            time.sleep(0.1)
        
        log.info(f'starting {exposureTime} s single exposure')        
        self.client.sendDetectorCommand('arm')
        worker = Worker(self.trigger)
        self.threadPool.start(worker)
        
    def onContinuous(self):
        frameRate = 20
        self.client.sendDetectorCommand('abort')
       
        if self.buttonContinuous.isChecked():
            self.buttonContinuous.setText('STOP')
            
            log.info(f'preparing continuous {frameRate} Hz exposure')
            self.client.setStreamConfig('mode','enabled')
            detectorConfig = [('count_time', 1/frameRate),
                            ('frame_time', 1/frameRate),
                            ('trigger_mode', 'ints'),
                            ('nimages', 1000000),
                            ('ntrigger', 1),
                            ]
            for config in detectorConfig:
                self.client.setDetectorConfig(*config)
                time.sleep(0.1)
            
            log.info(f'starting continuous exposure')
            self.client.sendDetectorCommand('arm')
            
            worker = Worker(self.trigger)
            self.threadPool.start(worker)
            worker.signals.finished.connect(self.onContinuous)
            
        else:
            self.buttonContinuous.setText('Continuous')
            self.client.sendDetectorCommand('abort')
            log.info('stopped continuous acquisition')
            

    @QtCore.pyqtSlot()
    def trigger(self):
        retry = 3
        time.sleep(5)
        while retry:
            try:
                state = self.client.detectorStatus('state')['value']
                if state == 'acquire':
                    retry = 3
                elif state == 'ready':
                    self.client.sendDetectorCommand('trigger')
                else:
                    retry = 0
            except Exception as e:
                retry -= 1
            finally:
                time.sleep(0.2)
                
        self.buttonContinuous.setChecked(False)
        return