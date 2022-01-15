# QuadroLiveView
PyQtGraph-based LiveViewer GUI for the DECTRIS QUADRO detector.
Uses the DECTRIS zmq stream itnerface.

## How to run
```python
python QuadroLiveView.py
```

## Dependencies
GUI: PyQt5, pyqtgraph, qdarkstyle
data handling: zmq, lz4, bitshuffle, tifffile, numpy