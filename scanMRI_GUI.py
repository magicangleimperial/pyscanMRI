import sys
from os import path
from PyQt5 import QtCore, uic
from PyQt5.QtWidgets import QMainWindow, QApplication
from scanMRI_Other import Save_Image
from scanMRI_Plot import PreviewDialog
from scanMRI_ReadSequence import GUI_SelectSequence, Object_Sequence
from scanMRI_HardwareControl import RunTime
sys.path.insert(0, path.dirname(path.realpath(__file__)) + '/module_seqed')
from module_seqed.main import SeqedWindow
from numpy import absolute
from threading import Thread


'''
                Class of the main GUI
########################################################################
-Contains some global variable
-Start function to start a sequence
-Close function to stop a sequence
########################################################################
'''


class GUIMainWindow(QMainWindow):
    # Two signals are defined here. They allow the GUI to be updated from
    # asynchronous process. PyQt forces you to use signal to update GUI.
    # up_index is for the textbox containing indexes and graph2d is for the
    # 2d matplotlib graph
    up_index = QtCore.pyqtSignal(object)
    up_graph2d = QtCore.pyqtSignal(object, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        ui_path = path.dirname(path.realpath(__file__)) + '/mainwindow.ui'
        self.ui = uic.loadUi(ui_path, self)
        self.up_index.connect(self.index_update)
        self.up_graph2d.connect(self.plot_update_2d)
        # Dialog windows for preview, sequence editor and select sequence
        # are pre-loaded
        self.gui_seqed = SeqedWindow()
        self.gui_preview = PreviewDialog(self)
        self.gui_select = GUI_SelectSequence(self)
        # Runtime is initialized with nothing , no sequence loaded yet
        self.runtime = None
        self.ui.startButton.clicked.connect(self.start)
        self.ui.stopButton.clicked.connect(self.stop)
        self.ui.saveButton.clicked.connect(lambda: Save_Image(self))
        self.ui.selectButton.clicked.connect(self.gui_select.exec)
        self.ui.selectButton.clicked.connect(self.stop)
        self.ui.act_preview.triggered.connect(self.gui_preview.show_close)
        self.ui.actionEdit_Create.triggered.connect(self.gui_seqed.show)

    def start(self):
        # when you click start, buttons are enabled/disabled, indexes are
        # initilized, a sequence is read, to become an obj_seq, signals
        # needed to update various GUI elements are loaded, and a runtime is
        # initialized and then loaded into a new thread.
        self.ui.stopButton.setEnabled(True)
        self.ui.startButton.setEnabled(False)
        self.ui.spinBox_Phase.setValue(1)
        self.ui.spinBox_CurrNx.setValue(1)
        obj_seq = Object_Sequence(self.gui_seqed.seq.dict_seq)
        up_sigs = [self.gui_preview.up_graph, self.up_graph2d, self.up_index]
        self.runtime = RunTime(obj_seq, up_sigs, self.gui_seqed.ui, self.stop)
        Thread(target=self.runtime.start).start()

    def stop(self):
        # Stops sequence generation
        if self.runtime is not None:
            self.runtime.stop()
            self.runtime = None
        self.ui.stopButton.setEnabled(False)
        self.ui.startButton.setEnabled(True)

    def closeEvent(self, event):
        # Close all windows when you close main window, saving some values
        self.gui_seqed.savedefault()
        self.stop()
        self.gui_seqed.close()

    def index_update(self, indices):
        self.ui.spinBox_CurrNx.setValue(indices[0])
        self.ui.spinBox_Phase.setValue(indices[1])
        self.ui.spinBox_Slice.setValue(indices[2])

    def plot_update_2d(self, fft, kspace):
        # The 2D matplotlib graph is updated here, k_space is also stored here
        # (in memory only but it can be saved in file if needed)
        plt_cvs = self.ui.matplotwidget.canvas
        plt_cvs.curr_slice = 0
        plt_cvs.kspace_data = kspace
        plt_cvs.data = fft
        plt_cvs.curr_data = fft
        plt_cvs.axes.imshow(absolute(fft[:, :, 0]), cmap='gray')
        plt_cvs.axes.set_aspect(len(fft[0, :, 0]) / len(fft[:, 0, 0]))
        plt_cvs.draw()


if __name__ == "__main__":
    # Triggers the app excecution when this script is ran
    app = QApplication(sys.argv)
    myapp = GUIMainWindow()
    myapp.show()
    sys.exit(app.exec_())
