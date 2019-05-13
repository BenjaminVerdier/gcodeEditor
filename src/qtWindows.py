from gcodeUtil import *
from QxTSpanSlider import QxtSpanSlider
from debugThingies import *

import sys
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import pyqtgraph as pg
import pyqtgraph.opengl as gl

import numpy as np

"""
TODO: fix gcode reader.
- Add support for comments in gcode (slic3r adds tons of comments to its generated gcode).
- If the last layer is empty, remove it.
TODO: add interactive path editing in the 2D view.
How to do that:
Apparently there are movable objects in pyqtgraph 2d graphics widgets. So.
- Take all unique points in the layer and put them in the graph as editable.
- Draw the lines connecting the points together.
- When a user clicks a point (left single click, hold), drags the point around.
- Double-click and hold a point to create a new node (adding a new subpath at the end or creating a new node in between two existing nodes)
TODO: add gcode writer.
The hard part is to determine the amount of extruded material for new/edited nodes.
- First (easy) way to do it is to take the amount per mm of surrounding nodes and use the same/an average. This is not ideal but it might work.
- Second (hard) way to do it is to do the calculation ourselves, but we are lacking a lot of info for this.
"""

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

        self.editBtn = QPushButton("Edit current layer")
        self.editBtn.clicked.connect(self.launchEditor)
        self.editBtn.setDisabled(True)

        layout2DTab.addWidget(self.canvas,0,0,5,15)
        layout2DTab.addWidget(QLabel("Layer:"),15,0)
        layout2DTab.addWidget(self.layerSpin,15,1)
        layout2DTab.addWidget(self.layerSlid,15,2)
        layout2DTab.addWidget(self.editBtn, 15,3)

        #3D Tab
        threeDTab.setLayout(layout3DTab)
        self.view = gl.GLViewWidget()
        self.view.show()

        self.minLayerSpin = QSpinBox()
        self.minLayerSpin.setRange(1, 1)
        self.minLayerSpin.setSingleStep(1)
        self.minLayerSpin.setValue(1)
        self.minLayerSpin.valueChanged.connect(self.minmaxSpinnerChanged)

        self.maxLayerSpin = QSpinBox()
        self.maxLayerSpin.setRange(1, 1)
        self.maxLayerSpin.setSingleStep(1)
        self.maxLayerSpin.setValue(1)
        self.maxLayerSpin.valueChanged.connect(self.minmaxSpinnerChanged)

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

        #Utility buttons
        buttonsLayout = QHBoxLayout()

        loadGcBtn = QPushButton("Load Gcode")
        buttonsLayout.addWidget(loadGcBtn)
        loadGcBtn.clicked.connect(self.loadGcode)

        self.describeBtn = QPushButton("Describe gcode")
        buttonsLayout.addWidget(self.describeBtn)
        self.describeBtn.clicked.connect(self.describe_gcode)
        self.describeBtn.setDisabled(True)

        self.describeMeshBtn = QPushButton("Describe mesh")
        buttonsLayout.addWidget(self.describeMeshBtn)
        self.describeMeshBtn.clicked.connect(self.describe_gcode_mesh)
        self.describeMeshBtn.setDisabled(True)

        mainLayout.addLayout(buttonsLayout)

        #Other variables

        self.lines = None

        self.show()

    @pyqtSlot()
    def loadGcode(self):
        gcodePath = QFileDialog.getOpenFileName(self, 'Open Gcode', '../resources', '*.gcode')
        if gcodePath[0] == '':
            print("No file chosen")
            return
        #Loading gcode and preprocessing
        self.gcode = GcodeReader(gcodePath[0])
        self.gcode._compute_subpaths()
        self.gcode.mesh(1)
        #Changing sliders and spinners
        self.layerSpin.setMaximum(self.gcode.n_layers)
        self.layerSlid.setMaximum(self.gcode.n_layers)
        self.minLayerSpin.setMaximum(self.gcode.n_layers)
        self.maxLayerSpin.setMaximum(self.gcode.n_layers)
        self.maxLayerSpin.setValue(self.gcode.n_layers)
        self.spanSlider.setRange(1,self.gcode.n_layers)
        self.spanSlider.setSpan(1,self.gcode.n_layers)

        #Enabling description and edition
        self.describeBtn.setDisabled(False)
        self.describeMeshBtn.setDisabled(False)
        self.editBtn.setDisabled(False)

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

    @pyqtSlot()
    def describe_gcode(self):
        self.gcode.describe()

    @pyqtSlot()
    def describe_gcode_mesh(self):
        self.gcode.describe_mesh(1)

    @pyqtSlot()
    def launchEditor(self):
        layer = self.layerSpin.value()
        subpaths = np.array(self.gcode.subpaths[self.gcode.subpath_index_bars[layer - 1]:self.gcode.subpath_index_bars[layer]])
        self.edit = EditWindow(self, subpaths)
        self.edit.show()
        self.layerBeingEdited = layer
        self.edit.finishedEdit.connect(self.receiveNewLayer)


    @pyqtSlot(np.ndarray)
    def receiveNewLayer(self, subpaths):
        dbg("The layer that was edited was number " + str(self.layerBeingEdited))
        dbg("And now for some nonsense:")
        dbg(subpaths)

    def printLayer(self, layer = 1):
        self.plot.clear()
        beg,end = self.gcode.subpath_index_bars[layer - 1],self.gcode.subpath_index_bars[layer]
        for path in self.gcode.subpaths[self.gcode.subpath_index_bars[layer - 1]:self.gcode.subpath_index_bars[layer]]:
            self.plot.plot(path[0], path[1])

    def displayScatter(self, minimum = 1, maximum = 0):
        #preprocess
        if not self.gcode.elements:
            self.gcode.mesh(1)
        if maximum < minimum:
            maximum = self.gcode.n_layers
        translatex, translatey = ((self.gcode.xyzlimits[0] + self.gcode.xyzlimits[1])/2, (self.gcode.xyzlimits[2] + self.gcode.xyzlimits[3])/2)
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

class EditWindow(QWidget):

    finishedEdit = pyqtSignal(np.ndarray, name="finishedEdit")

    def __init__(self, parent, subpaths):
        super(EditWindow, self).__init__(parent=None)
        self.origSubpaths = subpaths
        self.initUI()

    def initUI(self):
        mainLayout = QGridLayout()
        self.setLayout(mainLayout)
        #2D plot
        self.canvas = pg.GraphicsLayoutWidget()
        self.plot = self.canvas.addPlot()
        self.pt = self.plot.plot(pen='w')

        mainLayout.addWidget(self.canvas,0,0,5,15)
        #Buttons
        resetButton = QPushButton("Reset")
        resetButton.clicked.connect(self.resetEdit)

        confirmButton = QPushButton("Confirm")
        confirmButton.clicked.connect(self.confirmEdit)

        cancelButton = QPushButton("Cancel")
        cancelButton.clicked.connect(self.cancelEdit)

        mainLayout.addWidget(resetButton,15,0)
        mainLayout.addWidget(confirmButton,15,1)
        mainLayout.addWidget(cancelButton,15,2)

        self.loadOriginalPaths()

        self.resize(1300,1200)

    def loadOriginalPaths(self):
        self.plot.clear()
        for path in self.origSubpaths:
            self.plot.plot(path[0], path[1])

    @pyqtSlot()
    def resetEdit(self):
        #confirm = QMessageBox.question(self, 'Confirmation', "Are you sure you want to reset the path?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        #if confirm == QMessageBox.Yes:  # accepted
        self.loadOriginalPaths()

    @pyqtSlot()
    def confirmEdit(self):
        #confirm = QMessageBox.question(self, 'Confirmation', "Are you sure you want to confirm the edit?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        #if confirm == QMessageBox.Yes:  # accepted
        self.finishedEdit.emit(self.origSubpaths)
        self.close()

    @pyqtSlot()
    def cancelEdit(self):
        #confirm = QMessageBox.question(self, 'Confirmation', "Are you sure you want to cancel the edit?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        #if confirm == QMessageBox.Yes:  # accepted
        self.close()
