# https://stackoverflow.com/questions/24469662/how-to-redirect-logger-output-into-pyqt-text-widget
import sys
from PyQt5 import QtCore
from PyQt5.QtWidgets import QDialog, QApplication, QTextBrowser, QPushButton, QVBoxLayout
import logging

class QtHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)
    def emit(self, record):
        record = self.format(record)
        if record: XStream.stdout().write('%s\n'%record)

logger = logging.getLogger(__name__)
handler = QtHandler()
handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


class XStream(QtCore.QObject):
    _stdout = None
    _stderr = None
    messageWritten = QtCore.pyqtSignal(str)
    def flush( self ):
        pass
    def fileno( self ):
        return -1
    def write( self, msg ):
        if ( not self.signalsBlocked() ):
            self.messageWritten.emit(str(msg))
    @staticmethod
    def stdout():
        if ( not XStream._stdout ):
            XStream._stdout = XStream()
            sys.stdout = XStream._stdout
        return XStream._stdout
    @staticmethod
    def stderr():
        if ( not XStream._stderr ):
            XStream._stderr = XStream()
            sys.stderr = XStream._stderr
        return XStream._stderr

class MyDialog(QDialog):
    def __init__( self, parent = None ):
        super(MyDialog, self).__init__(parent)

        self._console = QTextBrowser(self)
        self._button  = QPushButton(self)
        self._button.setText('Test Me')

        layout = QVBoxLayout()
        layout.addWidget(self._console)
        layout.addWidget(self._button)
        self.setLayout(layout)

        XStream.stdout().messageWritten.connect( self._console.insertPlainText )
        XStream.stderr().messageWritten.connect( self._console.insertPlainText )

        self._button.clicked.connect(self.test)

    def test( self ):
        logger.debug('debug message')
        logger.info('info message')
        logger.warning('warning message')
        logger.error('error message')
        print('Old school hand made print message')

if ( __name__ == '__main__' ):
    app = None
    if ( not QApplication.instance() ):
        app = QApplication([])
    dlg = MyDialog()
    dlg.show()
    if ( app ):
        app.exec_()