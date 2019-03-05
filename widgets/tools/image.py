import logging
import numpy as np
import pandas
import tifffile
import os

PATH = os.path.abspath(__file__)
DIRPATH = os.path.dirname(PATH)

class ImageHandler():
    def __init__(self):
        self._maskpath = os.path.join(DIRPATH,"mask.tif")
        self.maskFromTiff(self._maskpath)

    def fft(self, real_img):
        real_img = real_img.astype(float)
        real_img = self.maskImage(real_img)

        img = np.fft.fft2(real_img)
        mag = np.abs(np.fft.fftshift(img))

        return 20*np.log10(mag**2+1)

    def maskImage(self, img):
        if img.shape != self.mask.shape:
            logging.warning("mask shape and image shape are different. Discarding mask.")
            self.mask = self.maskFromImage(img)

        img[self.mask] = np.nan
        img[img >= 2**(img.itemsize*8)-1] = np.nan
        df = pandas.DataFrame(img)
        return df.interpolate(method="linear").values

    def maskFromImage(self, img):
        bitDepth = img.itemsize * 8
        mask = np.zeros(img.shape)
        mask[img >= 2**bitDepth-1] = -1
        mask[img < 0] = 1
        logging.info("auto generated mask with shape {} , {} masked pixels".format(mask.shape, len(mask[mask != 0])))
        return mask != 0

    def maskFromTiff(self, fname):
        try:
            mask = tifffile.imread(fname)
        except Exception as e:
            logging.error("loading mask from {}: {}".format(fname, e))
            mask = np.zeros((514,514))
        else:
            self._maskpath = fname
            self.mask = mask != 0
            logging.info("loaded mask {} with shape {}, {} masked pixels".format(fname, mask.shape, len(mask[mask == True])))

        return self.mask

    def maskFromDetector(self, ip):
        logging.info("not implemented, not yet supported by SIMPLON API")
        return None
