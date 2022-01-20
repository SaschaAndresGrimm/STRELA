from PyQt5 import QtCore, QtGui, QtWidgets
import logging

from .CollapsibleBox import CollapsibleBox
from tools.EigerClient import EigerClient

logging.basicConfig()
log = logging.getLogger(__name__)

class FileWriterCommands(CollapsibleBox):
    def __init__(self, ip, port=80, title="FileWriter Commands", parent=None):
        super(FileWriterCommands, self).__init__(title, parent)
        self.ip = ip
        self.port = port
        self.client = EigerClient(self.ip, self.port)
        
        self.vbox = QtWidgets.QVBoxLayout()
        
        self.buttonInitialize = QtWidgets.QPushButton(self)
        self.buttonInitialize.setText('initialize')
        self.buttonInitialize.clicked.connect(self.onInitialize)
        self.vbox.addWidget(self.buttonInitialize)              

        self.buttonClear = QtWidgets.QPushButton(self)
        self.buttonClear.setText('clear')
        self.buttonClear.clicked.connect(self.onClear)
        self.vbox.addWidget(self.buttonClear)    
        
        self.setContentLayout(self.vbox)
    
    def onInitialize(self):
        log.info(f'initialize filewriter on {self.ip}:{self.port}')
        self.client.sendFileWriterCommand('initialize')

    def onClear(self):
        log.info(f'clear filewriter data on {self.ip}:{self.port}')
        self.client.sendFileWriterCommand('clear')