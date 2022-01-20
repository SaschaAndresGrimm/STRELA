import logging
import numpy as np
import pandas

logging.basicConfig()
log = logging.getLogger(__name__)

def fft(realImg, mask=None):
    # approx 50ms for 1M image
    maskedImg = maskImage(realImg.astype(float), mask)
    img = np.fft.fft2(maskedImg)
    mag = np.abs(np.fft.fftshift(img))

    return 20*np.log10(mag**2+1)

def maskImage(img, mask=None):
    if mask is not None:
        img[mask] = np.nan
    img[img >= 2**(img.itemsize*8)-1] = np.nan
    df = pandas.DataFrame(img)
    interpolated = df.interpolate(method="linear").values
    return interpolated