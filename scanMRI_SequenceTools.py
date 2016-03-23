#!/usr/bin/env python
from numpy import absolute, max

'''					Class to Automatically Optimize Shimming
########################################################################

########################################################################	
'''
class Optimize_Shim(object):
    def __init__(self, main_w):
        if main_w.ui.pushButton_AutoGrad.text() == "Auto OFF":
            main_w.ui.pushButton_AutoGrad.setStyleSheet("QPushButton {font: 1000 9pt \"Comic Sans MS\";background-color: rgba(0, 255, 0, 150);}")
            main_w.ui.pushButton_AutoGrad.setText("Auto ON")
        else:
            main_w.ui.pushButton_AutoGrad.setStyleSheet("QPushButton {font: 1000 9pt \"Comic Sans MS\";background-color: rgba(255, 0, 0, 150);}")
            main_w.ui.pushButton_AutoGrad.setText("Auto OFF")
        self.main_w = main_w
        self.AutoStep = 0.1
        self.AutoIter = 0
        self.AutoGrad = 0
        self.AutoMaximum = 0

    def auto_update_shim(self):
        TempSpinBox = 0
        if self.AutoGrad == 0:
            TempSpinBox = getattr(self.main_w.ui, 'doubleSpinBox_GradX', None)
        elif self.AutoGrad == 1:
            TempSpinBox = getattr(self.main_w.ui, 'doubleSpinBox_GradY', None)
        elif self.AutoGrad == 2:
            TempSpinBox = getattr(self.main_w.ui, 'doubleSpinBox_GradZ', None)

        if self.AutoStep > 0.0001:
            if self.AutoIter == 2:
                if max(absolute(self.main_w.dataFFTShort[:, 0])) > self.AutoMaximum:
                    self.AutoIter = 0
                    self.AutoStep *= 0.5
                else:
                    TempSpinBox.setValue(TempSpinBox.value() + self.AutoStep)
                    self.AutoIter = 0
                    self.AutoStep *= 0.5
            elif self.AutoIter == 1:
                if max(absolute(self.main_w.dataFFTShort[:, 0])) > self.AutoMaximum:
                    self.AutoIter = 0
                    self.AutoStep *= 0.5
                else:
                    TempSpinBox.setValue(TempSpinBox.value() - 2 * self.AutoStep)
                    self.AutoIter = 2
            elif self.AutoIter == 0:
                self.AutoMaximum = max(absolute(self.main_w.dataFFTShort[:, 0]))
                TempSpinBox.setValue(TempSpinBox.value() + self.AutoStep)
                self.AutoIter = 1
        else:
            if self.AutoGrad < 2:
                self.AutoIter = 0
                self.AutoStep = 0.1
                self.AutoGrad += 1
            else:
                self.__init__(self.main_w)