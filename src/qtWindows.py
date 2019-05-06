from gcodeUtil import *
from QxTSpanSlider import QxtSpanSlider
from debugThingies import *

import sys
#from PyQt4.QtCore import pyqtSlot
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import pyqtgraph as pg
import pyqtgraph.opengl as gl

import numpy as np

class MainWidget(QWidget):

    def __init__(self):
        super(MainWidget, self).__init__()
        self.initUI()

    def initUI(self):
        mainLayout = QVBoxLayout()
        self.setLayout(mainLayout)
        #Tabs definition
        tabs = QTabWidget()
        twoDTab = QWidget()
        threeDTab = QWidget()
        layout2DTab = QGridLayout()
        layout3DTab = QGridLayout()

        #2D Tab
        twoDTab.setLayout(layout2DTab)
        self.canvas = pg.GraphicsLayoutWidget()
        self.plot = self.canvas.addPlot()
        self.pt = self.plot.plot(pen='w')

        self.layerSpin = QSpinBox()
        self.layerSpin.setRange(1, 1)
        self.layerSpin.setSingleStep(1)
        self.layerSpin.setValue(1)

        self.layerSlid = QSlider(Qt.Horizontal)
        self.layerSlid.setMinimum(1)
        self.layerSlid.setMaximum(1)
        self.layerSlid.setValue(1)

        self.layerSpin.valueChanged.connect(lambda: self.layerSpinChange(self.layerSpin, self.layerSlid))
        self.layerSlid.valueChanged.connect(lambda: self.layerSlidChange(self.layerSpin, self.layerSlid))

        layout2DTab.addWidget(self.canvas,0,0,5,15)
        layout2DTab.addWidget(QLabel("Layer:"),15,0)
        layout2DTab.addWidget(self.layerSpin,15,1)
        layout2DTab.addWidget(self.layerSlid,15,2)

        #3D Tab
        threeDTab.setLayout(layout3DTab)
        self.view = gl.GLViewWidget()
        self.view.show()

        self.minLayerSpin = QSpinBox()
        self.minLayerSpin.setRange(1, 1)
        self.minLayerSpin.setSingleStep(1)
        self.minLayerSpin.setValue(1)

        self.minLayerSpin.valueChanged.connect(self.minmaxSpinnerChanged)
        """

        self.minLayerSlid = QSlider(Qt.Horizontal)
        self.minLayerSlid.setMinimum(1)
        self.minLayerSlid.setMaximum(1)
        self.minLayerSlid.setValue(1)


        self.minLayerSpin.valueChanged.connect(lambda: self.layerSpinChange(self.minLayerSpin, self.minLayerSlid, True))
        self.minLayerSlid.valueChanged.connect(lambda: self.layerSlidChange(self.minLayerSpin, self.minLayerSlid, True))
        """
        self.maxLayerSpin = QSpinBox()
        self.maxLayerSpin.setRange(1, 1)
        self.maxLayerSpin.setSingleStep(1)
        self.maxLayerSpin.setValue(1)

        self.maxLayerSpin.valueChanged.connect(self.minmaxSpinnerChanged)
        """
        self.maxLayerSlid = QSlider(Qt.Horizontal)
        self.maxLayerSlid.setMinimum(1)
        self.maxLayerSlid.setMaximum(1)
        self.maxLayerSlid.setValue(1)

        self.maxLayerSpin.valueChanged.connect(lambda: self.layerSpinChange(self.maxLayerSpin, self.maxLayerSlid, True))
        self.maxLayerSlid.valueChanged.connect(lambda: self.layerSlidChange(self.maxLayerSpin, self.maxLayerSlid, True))
        """

        self.spanSlider = QxtSpanSlider()
        self.spanSlider.setRange(1,1)
        self.spanSlider.setSpan(1,1)

        self.spanSlider.spanChangedSig.connect(self.spanSliderChanged)

        layout3DTab.addWidget(self.view,0,0,5,15)
        layout3DTab.addWidget(QLabel("Min Layer:"),15,0)
        layout3DTab.addWidget(self.minLayerSpin,15,1)
        layout3DTab.addWidget(self.spanSlider,15,2)
        layout3DTab.addWidget(QLabel("Max Layer:"),15,3)
        layout3DTab.addWidget(self.maxLayerSpin,15,4)

        #Adding tabs
        tabs.addTab(twoDTab, "Single Layer View")
        tabs.addTab(threeDTab, "3D View")


        mainLayout.addWidget(tabs)

        loadGcBtn = QPushButton("Load Gcode")
        mainLayout.addWidget(loadGcBtn)
        loadGcBtn.clicked.connect(self.loadGcode)

        #Other variables

        self.lines = None

        self.show()

    @pyqtSlot()
    def loadGcode(self):
        gcodePath = QFileDialog.getOpenFileName(self, 'Open Gcode', '../resources', '*.gcode')
        self.gcode = GcodeReader(gcodePath[0])
        self.gcode.describe()
        #self.gcode.describe_mesh()
        self.layerSpin.setMaximum(self.gcode.n_layers)
        self.layerSlid.setMaximum(self.gcode.n_layers)
        self.minLayerSpin.setMaximum(self.gcode.n_layers)
        self.maxLayerSpin.setMaximum(self.gcode.n_layers)
        self.maxLayerSpin.setValue(self.gcode.n_layers)
        self.spanSlider.setRange(1,self.gcode.n_layers)
        self.spanSlider.setSpan(1,self.gcode.n_layers)

        self.printLayer()
        self.displayScatter()

    @pyqtSlot()
    def layerSpinChange(self, spinner, slider):
        if slider.value() == spinner.value():
            return
        slider.setValue(spinner.value())
        self.printLayer(spinner.value())

    @pyqtSlot()
    def layerSlidChange(self, spinner, slider):
        if slider.value() == spinner.value():
            return
        spinner.setValue(slider.value())
        self.printLayer(slider.value())

    @pyqtSlot()
    def spanSliderChanged(self):
        changeLow, changeHigh = (False, False)
        if not self.minLayerSpin.value() == self.spanSlider.lowerValue:
            self.minLayerSpin.setValue(self.spanSlider.lowerValue)
            changeLow = True
        if not self.maxLayerSpin.value() == self.spanSlider.upperValue:
            self.maxLayerSpin.setValue(self.spanSlider.upperValue)
            changeHigh = True
        if changeLow or changeHigh:
            self.displayScatter(self.spanSlider.lowerValue, self.spanSlider.upperValue)

    @pyqtSlot()
    def minmaxSpinnerChanged(self):
        changeLow, changeHigh = (False, False)
        if not self.minLayerSpin.value() == self.spanSlider.lowerValue:
            self.spanSlider.setLowerValue(self.minLayerSpin.value())
            changeLow = True
        if not self.maxLayerSpin.value() == self.spanSlider.upperValue:
            self.spanSlider.setUpperValue(self.maxLayerSpin.value())
            changeHigh = True
        if changeLow or changeHigh:
            self.displayScatter(self.spanSlider.lowerValue, self.spanSlider.upperValue)

    def printLayer(self, layer = 1):
        self.plot.clear()
        beg,end = self.gcode.subpath_index_bars[layer - 1],self.gcode.subpath_index_bars[layer]
        for path in self.gcode.subpaths[self.gcode.subpath_index_bars[layer - 1]:self.gcode.subpath_index_bars[layer]]:
            self.plot.plot(path[0], path[1])

    def displayScatter(self, minimum = 1, maximum = 0):
        #preprocess
        if maximum < minimum:
            maximum = self.gcode.n_layers
        if not self.gcode.elements:
            self.gcode.mesh(1)
        translatex, translatey = (max(self.gcode.xyzlimits[2],self.gcode.xyzlimits[0]),max(self.gcode.xyzlimits[1],self.gcode.xyzlimits[3]))
        #Create gird for pretty plot
        zgrid = gl.GLGridItem()
        zgrid.scale(1, 1, 1)
        self.view.addItem(zgrid)
        #compute data
        data = []
        left, right = (self.gcode.elements_index_bars[minimum - 1],self.gcode.elements_index_bars[maximum])
        for x0, y0, x1, y1, z in self.gcode.elements[left:right]:
            data.append([x0,y0,z])
            data.append([x1,y1,z])
        #Create scatter plot
        if not self.lines == None:
            self.view.removeItem(self.lines)
        self.lines = gl.GLLinePlotItem()
        self.lines.setData(pos=np.array(data), width=5, mode='lines')
        self.lines.translate(-translatex, -translatey,0)
        self.view.addItem(self.lines)

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
