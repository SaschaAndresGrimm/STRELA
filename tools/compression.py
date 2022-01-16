import logging
import lz4.block, bitshuffle
import numpy as np
import struct

logging.basicConfig()
log = logging.getLogger(__name__)

__author__ = "SasG"
__date__ = "26/11/18"
__version__ = "0.1"
__reviewer__ = ""

def decompress(frame, shape, dtype, encoding, verbose=False):
    if encoding == "lz4<":
        data = readLZ4(frame, shape, dtype)
    elif "bs" in encoding:
        data = readBSLZ4(frame, shape, dtype)
    else:
        msg = "decoding {} is not implemented".format(info["encoding"])
        log.error(msg)
        raise ValueError(msg)
    return data

def readBSLZ4(frame, shape, dtype, verbose=False):
    """
    unpack bitshuffle-lz4 compressed frame and return np array image data
    frame: zmq data blob frame
    shape: image shape
    dtype: image data type
    """

    data = frame.bytes
    blob = np.fromstring(data[12:], dtype=np.uint8)
    dtype = np.dtype(dtype)
    # blocksize is big endian uint32 starting at byte 8, divided by element size
    blocksize = np.ndarray(shape=(), dtype=">u4", buffer=data[8:12])/dtype.itemsize
    imgData = bitshuffle.decompress_lz4(blob, shape[::-1], dtype, blocksize)
    if verbose:
        log.debug("unpacked {0} bytes of bs-lz4 data".format(len(imgData)))
    return imgData

def readLZ4(frame, shape, dtype, verbose=False):
    """
    unpack lz4 compressed frame and return np array image data
    frame: zmq data blob frame
    shape: image shape
    dtype:image data type
    """

    dtype = np.dtype(dtype)
    dataSize = dtype.itemsize*shape[0]*shape[1] # bytes * image size

    imgData = lz4.block.decompress(struct.pack('<I', dataSize) + frame.bytes)
    if verbose:
        log.debug("unpacked {0} bytes of lz4 data".format(len(imgData)))
    return np.reshape(np.fromstring(imgData, dtype=dtype), shape[::-1])
