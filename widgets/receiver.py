from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import QTimer, QThread, pyqtSlot, pyqtSignal, QObject, QThread

import sys, logging, os, traceback, time
import zmq, json

from .tools import camera, compression, image

PATH = os.path.abspath(__file__)
DIRPATH = os.path.dirname(PATH)

class Receiver(QWidget):
    dataReceived = pyqtSignal(object)

    def __init__(self, ip):
        super().__init__()
        self.ui = loadUi(os.path.join(DIRPATH, "ui","receiver.ui"), self)
        self.ip = ip
        self.setupCamera()
        self.portZMQ.editingFinished.connect(self.onPort)
        self.data = None
        self.setupReceivers()

    def setupCamera(self):
        self.zmqPort = self.ui.portZMQ.value()
        self.client = camera.Client(self.ip)
        self.client.query("stream","config","mode",key="enabled")
        self.imagesReceived = 0

    def setupReceivers(self):
        self.receivers = [ZMQReceiver(self.ip, name=str(i)) for i in range(8)]
        for receiver in self.receivers:
            receiver.signals.result.connect(self.handleData)
            self.buttonLiveView.clicked.connect(self.onLiveViewClicked)
            receiver.start()

    def onLiveViewClicked(self):
        for receiver in self.receivers:
            receiver.setRunning(self.buttonLiveView.isChecked())

    def handleData(self, data):
        self.data = data
        self.imagesReceived += 1
        self.statusImagesReceived.setValue(self.imagesReceived)
        self.dataReceived.emit(data)

    def getData(self):
        data = self.data
        self.data = None
        return data

    @pyqtSlot(str)
    def setIP(self, ip):
        self.ip = ip
        self.setupCamera()
        for receiver in self.receivers:
            receiver.changeHost(self.ip, self.zmqPort)

    def onPort(self):
        self.zmqPort = self.ui.portZMQ.value()
        for receiver in self.receivers:
            receiver.changeHost(self.ip, self.zmqPort)

class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)

class ZMQReceiver(QThread):
    def __init__(self, ip, port=9999, name=None, *args, **kwargs):
        super(ZMQReceiver, self).__init__()
        self.ip = ip
        self.port = port
        self.name = name
        self.imageHandler = image.ImageHandler()
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.connect()

    def setRunning(self, value):
        self.running = value

    def connect(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PULL)
        self.socket.connect("tcp://{0}:{1}".format(self.ip, self.port))
        logging.info("zmq receiver {} connected to tcp://{}:{}".format(self.name, self.ip, self.port))
        self.running = True

    def changeHost(self, ip, port):
        self.socket.disconnect("tcp://{0}:{1}".format(self.ip, self.port))
        self.ip = ip
        self.port = port
        self.socket.connect("tcp://{0}:{1}".format(self.ip, self.port))
        logging.info("zmq receiver {} connected to tcp://{}:{}".format(self.name, self.ip, self.port))

    def receive(self):
        """
        receive and return processed ZMQ frames
        """
        logging.debug("zmq receiver {} polling tcp://{}:{}".format(self.name, self.ip, self.port))
        if self.socket.poll(100):
            frames = self.socket.recv_multipart(copy = False)
            return self.processFrames(frames)

    def processFrames(self, frames):
        """
        process EIGER ZMQ stream frames
        """
        if frames:
            header = json.loads(frames[0].bytes)
            if header["htype"].startswith("dimage-"):
                info = json.loads(frames[1].bytes)
                data = compression.decompress(frames[2], info["shape"], info["type"], info["encoding"])
                logging.debug("receiver {} got data {}".format(self.name, info))
                fft = self.imageHandler.fft(data)
                logging.debug("receiver {} finished fft".format(self.name))
                # workaround strange pyqtgraph/np bug, where histogram cannot
                # be built for empty data
                data[0,0] = -1
                data[-1,0] = -1
                data[0,-1] = -1
                data[-1,-1] = -1
                return {"real":data, "fft":fft}

    @pyqtSlot()
    def run(self):
        while True:
            try:
                if self.running:
                    data = self.receive()
                else:
                    time.sleep(.5)
            except:
                traceback.print_exc()
                exctype, value = sys.exc_info()[:2]
                self.signals.error.emit((exctype, value, traceback.format_exc()))
            else:
                if data is not None:
                    self.signals.result.emit(data)
                else:
                    time.sleep(0.5)
            finally:
                self.signals.finished.emit()

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)
    app = QApplication(sys.argv)
    rec = Receiver("192.168.30.62")
    rec.show()
    sys.exit(app.exec_())
