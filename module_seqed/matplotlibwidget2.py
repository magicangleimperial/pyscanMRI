import matplotlib
matplotlib.use("Qt5Agg")
from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from numpy import arange, sinc, hanning, linspace
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class MyMplCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(dpi=40)
        self.axes = self.fig.add_subplot(111)
        self.axes.hold(False)
        self.fig.set_facecolor('white')
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        self.axes.get_yaxis().set_visible(False)
        self.fig.tight_layout(pad=1, h_pad=1)

class matplotlibWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.canvas = MyMplCanvas()
        self.vbl = QVBoxLayout()
        self.vbl.setContentsMargins(0, 0, 0, 0)
        self.vbl.addWidget(self.canvas)
        self.setLayout(self.vbl)

        self.risetime = None
        self.plotrange = None

    def update_figure(self, seq, channel):
        self.plotrange = seq['Acquisition Length'][0] + seq['Acquisition Start'][0] + 5
        self.risetime = seq['Rise Time']
        if channel == 'RF':
            x = [0]
            y = [0]
            for i in range(seq['Pulse Number']):
                x_linspace = arange(-seq['Pulse Length'][i]/2, seq['Pulse Length'][i]/2, 0.1)
                if seq['Pulse Angle'][i] > 30:
                    y_linspace = sinc(x_linspace) * hanning(len(x_linspace)) * seq['Pulse Angle'][i] / 180
                else:
                    y_linspace = sinc(x_linspace) * hanning(len(x_linspace)) * 30 / 180
                x.append(seq['Pulse Start'][i])
                y.append(y_linspace[0])
                self.canvas.axes.plot([x[-1], x[-1]], [0, max(y_linspace) * 1.1], color='#d3d3d3')
                self.canvas.axes.hold(True)
                x.extend(x_linspace[1:] + seq['Pulse Length'][i]/2 + seq['Pulse Start'][i])
                y.extend(y_linspace[1:])
                self.canvas.axes.plot([x[-1], x[-1]], [0, max(y_linspace) * 1.1], color='#d3d3d3')
                x.append(self.plotrange)
                y.append(0)
            self.canvas.axes.plot(x, y, 'b')
        else:
            x = [0]
            y = [0]
            for i in range(seq[channel + ' Number']):
                ymin = min(seq[channel + ' Amplitude'] + seq[channel + ' Lobes Amplitude']) - 0.2
                ymax = max(seq[channel + ' Amplitude'] + seq[channel + ' Lobes Amplitude']) + 0.2
                x.append(seq[channel + ' Start'][i] - seq['Rise Time'])
                y.append(0)
                x.append(x[-1] + self.risetime)
                y.append(seq[channel + ' Lobes Amplitude'][i] + seq[channel + ' Amplitude'][i])
                x.append(x[-1] + seq[channel + ' Lobes Length'][i])
                y.append(seq[channel + ' Lobes Amplitude'][i] + seq[channel + ' Amplitude'][i])
                if seq[channel + ' Lobes Length'][i] != 0:
                    x.append(x[-1] + self.risetime)
                    y.append(seq[channel + ' Amplitude'][i])
                self.canvas.axes.plot([x[-1], x[-1]], [ymin, ymax], color='#d3d3d3')
                self.canvas.axes.hold(True)
                x.append(x[-1] + seq[channel + ' Length'][i])
                y.append(seq[channel + ' Amplitude'][i])
                self.canvas.axes.plot([x[-1], x[-1]], [ymin, ymax], color='#d3d3d3')
                if seq[channel + ' Lobes Length'][i] != 0:
                    x.append(x[-1] + self.risetime)
                    y.append(seq[channel + ' Lobes Amplitude'][i] + seq[channel + ' Amplitude'][i])
                x.append(x[-1] + seq[channel + ' Lobes Length'][i])
                y.append(seq[channel + ' Lobes Amplitude'][i] + seq[channel + ' Amplitude'][i])
                x.append(x[-1] + self.risetime)
                y.append(0)
            x.append(self.plotrange)
            y.append(0)
            if channel == 'Slice':
                self.canvas.axes.plot(x, y, 'g')
            if channel == 'Phase':
                self.canvas.axes.plot(x, y, 'r')
                for i in range(5):
                    y_linspace = linspace(1, -1, 6)
                    y2 = [x * y_linspace[i + 1] for x in y]
                    self.canvas.axes.plot(x, y2, 'r')
            elif channel == 'Read':
                self.canvas.axes.plot(x, y, 'c')
                x = [seq['Acquisition Start'][0]]
                y = [0]
                x.append(seq['Acquisition Start'][0])
                y.append(1)
                x.append(seq['Acquisition Start'][0] + seq['Acquisition Length'][0])
                y.append(1)
                x.append(seq['Acquisition Start'][0] + seq['Acquisition Length'][0])
                y.append(0)
                self.canvas.axes.plot(x, y, 'm')
                self.canvas.axes.fill(x, y, 'm')
        ## lines
        self.canvas.axes.set_xlim([0, self.plotrange])
        self.canvas.axes.autoscale_view(True, True, True)
        self.canvas.draw()
        self.canvas.axes.hold(False)
