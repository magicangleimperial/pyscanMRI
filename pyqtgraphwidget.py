from pyqtgraph import PlotWidget, setConfigOption
from numpy import zeros, arange


class pyqtgraphWidget(PlotWidget):
    def __init__(self, parent=None, scale_min=0, scale_max=1, steps=0.1, title='None'):
        setConfigOption('background', 'w')
        PlotWidget.__init__(self,  parent, enableMenu=False, border=False, title=title)
        self.range_ = arange(scale_min, scale_max, steps)
        self.curve = self.plot(self.range_, zeros([len(self.range_)]), clear=False, pen='b')
        # self.curve2 = self.plot(self.range_, zeros([len(self.range_)]) + 0.5, clear=False, pen='r')
        self.disableAutoRange()
        self.setRange(xRange=(scale_min, scale_max))

    def update_graph(self, title, scale_min, scale_max, steps):
        self.clear()
        self.setTitle(title=title)
        self.range_ = arange(scale_min, scale_max, steps)
        self.curve = self.plot(self.range_, zeros([len(self.range_)]), clear=False, pen='b')
        # self.curve2 = self.plot(self.range_, zeros([len(self.range_)]) + 0.5, clear=False, pen='r')
        self.setRange(xRange=(scale_min, scale_max))

    def update_plot(self, data):
        self.curve.setData(self.range_[:len(data)], data)
        # self.curve2.setData(self.range_[:len(data2)], data2 + 0.5)
        minim = min(data)
        maxim = max(data)
        self.setRange(yRange=(minim, maxim))
