from PyQt5.QtCore import QThread, QRunnable, pyqtSlot, pyqtSignal, QObject
import traceback, sys, logging
import numpy as np
import pandas

logging.basicConfig()
log = logging.getLogger(__name__)

class FFT(QRunnable):
    def __init__(self, image, *args, **kwargs):
        super(FFT, self).__init__()
        self.img = image
        self.signals = WorkerSignals()
        
    def fft(self, mask=None):
        # takes approx 50ms for 1M image
        maskedImg = self.maskImage(self.img.astype(float), mask)
        img = np.fft.fft2(maskedImg)
        mag = np.abs(np.fft.fftshift(img))

        return 20*np.log10(mag**2+1)

    def maskImage(self, img, mask=None):
        if mask is not None:
            img[mask] = np.nan
        img[img >= 2**(img.itemsize*8)-1] = np.nan
        df = pandas.DataFrame(img)
        interpolated = df.interpolate(method="linear").values
        return interpolated
        
    @pyqtSlot()
    def run(self):
        try:
            fft = self.fft()
            self.signals.finished.emit(fft)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
                
class WorkerSignals(QObject):
    error = pyqtSignal(tuple)
    finished = pyqtSignal(object)