from PyQt5 import QtCore, QtGui, QtWidgets
import logging

from .CollapsibleBox import CollapsibleBox
from tools.EigerClient import EigerClient

logging.basicConfig()
log = logging.getLogger(__name__)

class StreamCommands(CollapsibleBox):
    def __init__(self, ip, port=80, title="Stream Commands", parent=None):
        super(StreamCommands, self).__init__(title, parent)
        self.ip = ip
        self.port = port
        self.client = EigerClient(self.ip, self.port)
        
        self.vbox = QtWidgets.QVBoxLayout()
        
        self.buttonInitialize = QtWidgets.QPushButton(self)
        self.buttonInitialize.setText('initialize')
        self.buttonInitialize.clicked.connect(self.onInitialize)
        self.vbox.addWidget(self.buttonInitialize)              
        
        self.setContentLayout(self.vbox)
    
    def onInitialize(self):
        log.info(f'initialize stream on {self.ip}:{self.port}')
        self.client.sendStreamCommand('initialize')
