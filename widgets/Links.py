from PyQt5 import QtCore, QtGui, QtWidgets
import logging

from .CollapsibleBox import CollapsibleBox

logging.basicConfig()
log = logging.getLogger(__name__)

class Links(CollapsibleBox):
    def __init__(self, ip, port=80, title="Links", parent=None):
        super(Links, self).__init__(title, parent)
        self.ip = ip
        self.port = port
        
        self.vbox = QtWidgets.QVBoxLayout()
        
        self.linkWebUi = QtWidgets.QLabel(self)
        self.linkWebUi.setText(f'<a href="http://{self.ip}:{self.port}">WebInterface</a>')
        self.linkWebUi.setOpenExternalLinks(True)
        self.vbox.addWidget(self.linkWebUi)
        
        self.linkData = QtWidgets.QLabel(self)
        self.linkData.setText(f'<a href="http://{self.ip}:{self.port}/data">Data</a>')
        self.linkData.setOpenExternalLinks(True)
        self.vbox.addWidget(self.linkData) 
        
        self.linkLogs = QtWidgets.QLabel(self)
        self.linkLogs.setText(f'<a href="http://{self.ip}:{self.port}/logs">Log Files</a>')
        self.linkLogs.setOpenExternalLinks(True)
        self.vbox.addWidget(self.linkLogs)        

        self.linkManuals = QtWidgets.QLabel(self)
        self.linkManuals.setText(f'<a href="https://www.dectris.com/support/manuals-docs/overview/">Manuals & Docs</a>')
        self.linkManuals.setOpenExternalLinks(True)
        self.vbox.addWidget(self.linkManuals)   
        
        self.setContentLayout(self.vbox)
