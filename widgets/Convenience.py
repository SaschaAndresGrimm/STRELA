from PyQt5 import QtCore, QtGui, QtWidgets
import logging, time

from .CollapsibleBox import CollapsibleBox
from tools.EigerClient import EigerClient

logging.basicConfig()
log = logging.getLogger(__name__)

#need proper rewriting of eigerclient using pyqt signals

class ConvenienceFunc(CollapsibleBox):
    def __init__(self, ip, port=80, title="Convenience Functions", parent=None):
        super(ConvenienceFunc, self).__init__(title, parent)
        self.ip = ip
        self.port = port
        self.client = EigerClient(self.ip, self.port)
        
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
        self.client.sendDetectorCommand('arm')
        time.sleep(1)
        self.client.sendDetectorCommand('trigger')
        #time.sleep(exposureTime)
        #self.client.sendDetectorCommand('disarm')
        log.info(f'finished {exposureTime} s single exposure')        

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
            self.client.sendDetectorCommand('arm')
            time.sleep(1)
            self.client.sendDetectorCommand('trigger')
            # add method to poll status and re-set button
            # needs to become a thread
        
        else:
            self.buttonContinuous.setText('Continuous')
            self.client.sendDetectorCommand('abort')
            log.info('stopped continuous acquisition')
