from PyQt5 import QtCore, QtGui, QtWidgets
import logging

from .CollapsibleBox import CollapsibleBox
from tools.DEigerClient import DEigerClient

logging.basicConfig()
log = logging.getLogger(__name__)

class DetectorCommands(CollapsibleBox):
    def __init__(self, title="Detector Commands", parent=None):
        super(DetectorCommands, self).__init__(title, parent)
        self.ip = '192.168.30.26'
        self.port = 80
        self.client = DEigerClient(self.ip, self.port)
        
        self.vbox = QtWidgets.QVBoxLayout()
        
        self.buttonArm = QtWidgets.QPushButton(self)
        self.buttonArm.setText('arm')
        self.buttonArm.clicked.connect(self.onArm)
        self.vbox.addWidget(self.buttonArm)              
        
        self.buttonTrigger = QtWidgets.QPushButton(self)
        self.buttonTrigger.setText('trigger')
        self.buttonTrigger.clicked.connect(self.onTrigger)
        self.vbox.addWidget(self.buttonTrigger) 
        
        self.buttonAbort = QtWidgets.QPushButton(self)
        self.buttonAbort.setText('abort')
        self.buttonAbort.clicked.connect(self.onAbort)
        self.vbox.addWidget(self.buttonAbort)
 
        self.buttonInitalize = QtWidgets.QPushButton(self)
        self.buttonInitalize.setText('initialize')
        self.buttonInitalize.clicked.connect(self.onInitialize)
        self.vbox.addWidget(self.buttonInitalize)
               
        self.setContentLayout(self.vbox)
    
    def onTrigger(self):
        log.info(f'send trigger to {self.ip}:{self.port}')
        self.client.sendDetectorCommand('trigger')

    def onAbort(self):
        log.info(f'send abort to {self.ip}:{self.port}')
        self.client.sendDetectorCommand('abort')    
        
    def onArm(self):
        log.info(f'send arm to {self.ip}:{self.port}')
        self.client.sendDetectorCommand('arm')

    def onInitialize(self):
        log.info(f'initialize {self.ip}:{self.port}')
        self.client.sendDetectorCommand('initialize')