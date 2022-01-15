from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import QTimer, QThread, pyqtSlot, pyqtSignal, QObject, QThread
import traceback
import time, zmq, logging, json, datetime
from . import compression, DEigerClient

class ZMQReceiver(QThread):
    def __init__(self, ip, port=9999, name=None, *args, **kwargs):
        super(ZMQReceiver, self).__init__()
        self.ip = ip
        self.port = port
        self.name = name
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
                
        self.enableStream()
        self.connect()
        
    def enableStream(self):
        client = DEigerClient.DEigerClient(self.ip)
        resp = client.setStreamConfig('mode','enabled')
        logging.debug(f'stream enabled on {self.ip}')

    def connect(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PULL)
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
        if frames:
            header = json.loads(frames[0].bytes)
            if header["htype"].startswith("dimage-"):
                info = json.loads(frames[1].bytes)
                data = compression.decompress(frames[2], info["shape"], info["type"], info["encoding"])
                # workaround strange pyqtgraph/np bug, where histogram cannot be built for empty data
                data[0,0] = -1
                data[-1,0] = -1
                data[0,-1] = -1
                data[-1,-1] = -1
                
                # set overflow values to 0 for better contrast
                data[data==(2**(8*data.itemsize)-1)] = 0
                                
                return data

    @pyqtSlot()
    def run(self):
        self.start_time = datetime.datetime.now().time()
        while True:
            try:
                data = self.receive()
            except:
                traceback.print_exc()
                exctype, value = sys.exc_info()[:2]
                self.signals.error.emit((exctype, value, traceback.format_exc()))
            else:
                if data is not None:
                    self.signals.dataReceived.emit(data)
                    t = datetime.datetime.now().time()
                    dt = t.second - self.start_time.second + (t.microsecond-self.start_time.microsecond)/1000000
                    self.start_time = datetime.datetime.now().time()
                    logging.debug("receiver {} got image data with {} Hz".format(self.name, 1/dt))
            #finally:
            #    self.signals.finished.emit()
                
class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    dataReceived = pyqtSignal(object)