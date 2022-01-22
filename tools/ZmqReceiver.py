from PyQt5.QtCore import QTimer, QRunnable, QThread, pyqtSlot, pyqtSignal, QObject, QEventLoop
import traceback, sys
import time, zmq, logging, json, datetime
from . import compression, EigerClient

logging.basicConfig()
log = logging.getLogger(__name__)

class ZMQReceiver(QRunnable):
    def __init__(self, ip, port=9999, name=None, *args, **kwargs):
        super(ZMQReceiver, self).__init__()
        self.ip = ip
        self.port = port
        self.name = name
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
 
        # processing frames
        self.timerProcess = QTimer()
        self.timerProcess.timeout.connect(self.processFrames)
        self.timerProcess.start(50)
 
        # receiving frames
        self.timerReceive = QTimer()
        self.timerReceive.timeout.connect(self.receive)
        self.timerReceive.start(10)
        
        self.frames = None
        self.data = None
        
    def enableStream(self):
        log.debug(f'enabling stream on {self.ip}')
        client = EigerClient.EigerClient(self.ip)
        resp = client.setStreamConfig('mode','enabled')

    def connect(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PULL)
        self.socket.connect("tcp://{0}:{1}".format(self.ip, self.port))
        log.info("zmq receiver {} connected to tcp://{}:{}".format(self.name, self.ip, self.port))

    def receive(self):
        """
        receive and remit QT signal with image data
        """
        log.debug("zmq receiver {} polling tcp://{}:{}".format(self.name, self.ip, self.port))
        if self.socket.poll(100):
            frames = self.socket.recv_multipart(copy = False)
            self.frames = frames

    def processFrames(self):
        if self.frames is not None:
            frames = self.frames
            self.frames = None
            
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
                # typecasting to signed int might be better...
                data[data==(2**(8*data.itemsize)-1)] = 0
                                
                self.signals.dataReceived.emit(data)

    @pyqtSlot()
    def run(self):
        self.enableStream()
        self.connect()
        loop = QEventLoop()
        loop.exec_()
                
class WorkerSignals(QObject):
    error = pyqtSignal(tuple)
    dataReceived = pyqtSignal(object)