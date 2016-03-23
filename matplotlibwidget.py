import matplotlib
matplotlib.use("Qt5Agg")
from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from numpy import absolute, copy
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class MyMplCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure()
        self.axes = self.fig.add_subplot(111)
        self.axes.hold(False)
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        self.axes.get_xaxis().set_visible(False)
        self.axes.get_yaxis().set_visible(False)
        self.fig.tight_layout(pad=0.3, w_pad=0.3, h_pad=0.3)

        self.curr_slice = 0
        self.delta = 0
        self.curr_data = None
        self.kspace_data = None
        self.data = None
        self.xmin = None
        self.ymin = None

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            if self.curr_data is None:
                self.curr_data = copy(self.data)
            if self.data is not None:
                self.xmin = int(event.pos().x() / self.height() * len(self.curr_data[0, :, self.curr_slice]))
                self.ymin = int(event.pos().y() / self.height() * len(self.curr_data[:, 0, self.curr_slice]))
        if event.button() == QtCore.Qt.RightButton:
            if self.data is not None:
                self.curr_data = copy(self.data)
                self.axes.imshow(absolute(self.data[:, :, self.curr_slice]), aspect=len(self.data[0, :, self.curr_slice]) / len(self.data[:, 0, self.curr_slice]), cmap='gray')
                self.draw()
        if event.button() == QtCore.Qt.MiddleButton:
            if self.kspace_data is not None:
                pass
            #    self.axes.imshow(self.kspace_data[:, :, 0].real, aspect=len(self.kspace_data[0, :, 0]) / len(self.kspace_data[:, 0, 0]), cmap='gray')
            #    self.draw()

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            if self.data is not None:
                xmax = int(event.pos().x() / self.height() * len(self.curr_data[0, :, self.curr_slice]))
                ymax = int(event.pos().y() / self.height() * len(self.curr_data[:, 0, self.curr_slice]))
                if xmax < 0:
                    xmax = 0
                if xmax > len(self.data[0, :]) - 1:
                    xmax = len(self.data[0, :]) - 1
                if ymax < 0:
                    ymax = 0
                if ymax > len(self.data[:, 0]) - 1:
                    ymax = len(self.data[:, 0]) - 1
                if self.xmin == xmax:
                    xmax = self.xmin + 1
                if self.ymin == ymax:
                    ymax = self.ymin + 1
                new_data = self.curr_data[min(ymax, self.ymin):max(ymax, self.ymin), min(self.xmin, xmax):max(self.xmin, xmax)]
                self.curr_data = copy(new_data)
                self.axes.imshow(absolute(new_data[:, :, self.curr_slice]), aspect=len(new_data[0, :, self.curr_slice]) / len(new_data[:, 0, self.curr_slice]), cmap='gray')
                self.draw()
        if event.button() == QtCore.Qt.MiddleButton:
            if self.data is not None:
                pass
                #self.curr_data = copy(self.data)
                #self.axes.imshow(absolute(self.data[:, :, self.curr_slice]), aspect=len(self.data[0, :, self.curr_slice]) / len(self.data[:, 0, self.curr_slice]), cmap='gray')
                #self.draw()

    def wheelEvent(self, event):
        if self.data is not None:
            nbr_slice = len(self.data[0, 0, :])
            print()
            self.delta += event.angleDelta().y()
            if self.delta >= 120 * nbr_slice:
                self.delta = 120 * nbr_slice - 120
            elif self.delta <= -120:
                self.delta = 0
            for i in range(nbr_slice):
                if self.delta == 120 * i:
                    self.curr_slice = i
            self.axes.imshow(absolute(self.curr_data[:, :, self.curr_slice]), aspect=len(self.curr_data[0, :, self.curr_slice]) / len(self.curr_data[:, 0, self.curr_slice]), cmap='gray')
            self.draw()


class matplotlibWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.canvas = MyMplCanvas()
        self.vbl = QVBoxLayout()
        self.vbl.addWidget(self.canvas)
        self.setLayout(self.vbl)

    def resizeEvent(self, e):
        self.setMinimumWidth(self.height())
        self.setMaximumWidth(self.height())
