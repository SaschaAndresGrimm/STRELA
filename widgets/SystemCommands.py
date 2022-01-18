from PyQt5 import QtCore, QtGui, QtWidgets
import logging

from .CollapsibleBox import CollapsibleBox
from tools.DEigerClient import DEigerClient

logging.basicConfig()
log = logging.getLogger(__name__)

class SystemCommands(CollapsibleBox):
    def __init__(self, ip, port=80, title="System Commands", parent=None):
        super(SystemCommands, self).__init__(title, parent)
        self.ip = ip
        self.port = port
        self.client = DEigerClient(self.ip, self.port)
        
        self.vbox = QtWidgets.QVBoxLayout()
        
        self.buttonRestart = QtWidgets.QPushButton(self)
        self.buttonRestart.setText('restart')
        self.buttonRestart.clicked.connect(self.onRestart)
        self.vbox.addWidget(self.buttonRestart)              
               
        self.buttonReboot = QtWidgets.QPushButton(self)
        self.buttonReboot.setText('reboot')
        self.buttonReboot.clicked.connect(self.onReboot)
        self.vbox.addWidget(self.buttonReboot)                 
               
        self.setContentLayout(self.vbox)
    
    def onRestart(self):
        log.info(f'restart {self.ip}:{self.port}')
        self.client.sendSystemCommand('restart')
        
    def onReboot(self):
        log.info(f'reboot {self.ip}:{self.port}')
        self.client.sendSystemCommand('reboot')