from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QDialog
from numpy import absolute, fft
from scanMRI_ReadSequence import DACrate, ADCrate
'''                 Class for signal preview
########################################################################
We use a pyqtgraph package which is lightweight and fast to optionnaly
plot the signal (time / frequency).
########################################################################
'''


class PreviewDialog(QDialog):
    up_graph = pyqtSignal(object, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = uic.loadUi('dialog_preview.ui', self)
        self.graph_t = self.ui.widget_pyqtgraph_time
        self.graph_f = self.ui.widget_pyqtgraph_freq
        self.guis = parent.gui_seqed
        self.act_preview = parent.ui.act_preview

    def show_close(self):
        # Show or hide
        if self.act_preview.isChecked():
            self.show()
        else:
            self.close()

    def showEvent(self, event):
        # Update the x scale of both graphs
        self.up_graph.connect(self.plot_update)
        acq_len = self.guis.seq.dict_seq['Acquisition Length'][0]
        lim = ADCrate/4000
        self.graph_t.update_graph('Time', 0, acq_len, 1000 / DACrate)
        self.graph_f.update_graph('Frequency', -lim, lim, 1 / acq_len)

    def closeEvent(self, event):
        self.up_graph.disconnect(self.plot_update)
        self.act_preview.setChecked(False)

    def plot_update(self, all_k, all_k_shift):
        data_kspace = all_k[self.ui.channels.currentIndex()]
        kspace_shift = all_k_shift[self.ui.channels.currentIndex()]
        # Dynamic fft
        pts = len(kspace_shift)
        fft_temp = fft.fft(kspace_shift)
        fft_temp = fft.fftshift(fft_temp)[pts / 4: 3 * pts / 4] / pts
        self.graph_t.update_plot(data_kspace)
        self.graph_f.update_plot(absolute(fft_temp))
