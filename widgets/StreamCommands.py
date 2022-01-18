from PyQt5 import QtCore, QtGui, QtWidgets
import logging

from .CollapsibleBox import CollapsibleBox
from tools.DEigerClient import DEigerClient

logging.basicConfig()
log = logging.getLogger(__name__)

class StreamCommands(CollapsibleBox):
    def __init__(self, title="Stream Commands", parent=None):
        super(StreamCommands, self).__init__(title, parent)
        self.ip = '192.168.30.26'
        self.port = 80
        self.client = DEigerClient(self.ip, self.port)
        
        self.vbox = QtWidgets.QVBoxLayout()
        
        self.buttonInitialize = QtWidgets.QPushButton(self)
        self.buttonInitialize.setText('initialize')
        self.buttonInitialize.clicked.connect(self.onInitialize)
        self.vbox.addWidget(self.buttonInitialize)              
        
        self.setContentLayout(self.vbox)
    
    def onInitialize(self):
        log.info(f'initialize stream on {self.ip}:{self.port}')
        self.client.sendStreamCommand('initialize')
