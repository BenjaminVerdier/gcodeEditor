from gcodeUtil import *

import sys
#from PyQt4.QtCore import pyqtSlot
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import pyqtgraph as pg
import pyqtgraph.opengl as gl

import numpy as np

class MainWidget(QWidget):

    def __init__(self):
        super(MainWidget, self).__init__()
        self.initUI()

    def initUI(self):
        layout = QGridLayout()
        self.setLayout(layout)

        tabs = QTabWidget()

        self.canvas = pg.GraphicsLayoutWidget()
        self.plot = self.canvas.addPlot()
        self.pt = self.plot.plot(pen='w')

        self.view = gl.GLViewWidget()
        self.view.show()

        #Create gird
        zgrid = gl.GLGridItem()
        zgrid.scale(0.1, 0.1, 0.1)
        self.view.addItem(zgrid)

        tabs.addTab(self.canvas, "Single Layer View")
        tabs.addTab(self.view, "3D View")

        layout.addWidget(tabs,0,0,5,15)

        loadGcBtn = QPushButton("Load Gcode")
        layout.addWidget(loadGcBtn,15,0)
        loadGcBtn.clicked.connect(self.loadGcode)

        self.layerSpin = QDoubleSpinBox()
        self.layerSpin.setRange(1, 1)
        self.layerSpin.setSingleStep(1)
        self.layerSpin.setValue(1)
        self.layerSpin.setDecimals(0)
        layout.addWidget(self.layerSpin,15,1)
        self.layerSpin.valueChanged.connect(self.layerSpinChange)

        self.layerSlid = QSlider(Qt.Horizontal)
        self.layerSlid.setMinimum(1)
        self.layerSlid.setMaximum(1)
        self.layerSlid.setValue(1)
        layout.addWidget(self.layerSlid,15,2)
        self.layerSlid.valueChanged.connect(self.layerSlidChange)

        #Other variables

        self.show()

    @pyqtSlot()
    def loadGcode(self):
        gcodePath = QFileDialog.getOpenFileName(self, 'Open Gcode', '../resources', '*.gcode')
        self.gcode = GcodeReader(gcodePath)
        #self.gcode.describe()
        self.gcode.describe_mesh()
        self.layerSpin.setMaximum(self.gcode.n_layers)
        self.layerSlid.setMaximum(self.gcode.n_layers)
        xoffset = (self.gcode.xyzlimits[1] - self.gcode.xyzlimits[0])/5
        yoffset = (self.gcode.xyzlimits[2] - self.gcode.xyzlimits[3])/5

        self.printLayer()

    @pyqtSlot()
    def layerSpinChange(self):
        if self.layerSlid.value() == int(self.layerSpin.value()):
            return
        self.layerSlid.setValue(int(self.layerSpin.value()))
        self.printLayer(int(self.layerSpin.value()))

    @pyqtSlot()
    def layerSlidChange(self):
        if self.layerSlid.value() == int(self.layerSpin.value()):
            return
        self.layerSpin.setValue(self.layerSlid.value())
        self.printLayer(self.layerSlid.value())

    def printLayer(self, layer = 1):
        self.plot.clear()
        beg,end = self.gcode.subpath_index_bars[layer - 1],self.gcode.subpath_index_bars[layer]
        for path in self.gcode.subpaths[self.gcode.subpath_index_bars[layer - 1]:self.gcode.subpath_index_bars[layer]]:
            self.plot.plot(path[0], path[1])

class MainWindow(QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__()
        self.initUI()

    def initUI(self):
        mw = MainWidget()
        self.setCentralWidget(mw)
        self.setWindowTitle('GCode Editor')
        self.resize(1300,1200)

        self.show()
