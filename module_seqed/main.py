import sys
from PyQt5 import uic
from csv import writer, reader
from os.path import dirname, realpath
from PyQt5.QtWidgets import QDialog, QFileDialog, QApplication
from FID import ClassFID
from flash import ClassFlash
from spinecho import ClassSpinEcho


class SeqedWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.path = dirname(realpath(__file__))
        self.ui = uic.loadUi(self.path + '/MainWidget.ui', self)
        # To save a new sequence
        self.savecsv.clicked.connect(lambda: self.writecsv(self.seq))
        # When a new sequence type is chosen
        self.seqtype.currentIndexChanged.connect(self.load_new_type)

    def writecsv(self, sequence):
        # Open a dialog box to save a sequence
        path = dirname(self.path) + '/Sequence'
        text = 'Save Sequence'
        fn = QFileDialog.getSaveFileName(self, text, path, 'CSV (*.csv)')[0]
        print(fn)
        if fn:
            sequence.writetocsv(fn)

    def readdefault(self, default_file):
        # Read values that are independant from sequence
        dictionnary = self.read_file_dict(default_file)
        self.ui.pulse_frequency.setValue(dictionnary['Pulse Frequency'])
        self.ui.pulse_amplitude.setValue(dictionnary['Pulse Value 90'])
        self.ui.gradx_offset.setValue(dictionnary['Offset'][0])
        self.ui.grady_offset.setValue(dictionnary['Offset'][1])
        self.ui.gradz_offset.setValue(dictionnary['Offset'][2])
        self.ui.b0_offset.setValue(dictionnary['Offset'][3])
        self.ui.nx.setValue(dictionnary['Averaging'])

    def savedefault(self):
        # Save values independant from sequence when software is closed
        dictionary = {}
        dictionary.update({'Pulse Frequency': self.ui.pulse_frequency.value()})
        dictionary.update({'Pulse Value 90': self.ui.pulse_amplitude.value()})
        offset_list = [self.ui.gradx_offset.value()]
        offset_list.append(self.ui.grady_offset.value())
        offset_list.append(self.ui.gradz_offset.value())
        offset_list.append(self.ui.b0_offset.value())
        dictionary.update({'Offset': offset_list})
        dictionary.update({'Averaging': self.ui.nx.value()})
        fn = dirname(realpath(__file__)) + '/default.csv'
        keys = list(dictionary.keys())
        with open(fn, 'w') as out:
            csv_out = writer(out, lineterminator='\n')
            for key_ in sorted(keys):
                val_ = dictionary[key_]
                csv_out.writerow([key_, val_])

    def block(self, widget, state):
        # Block all signals/slots, used when we load a new sequence
        for x in widget.children():
            x.blockSignals(state)
            if x.children() != []:
                self.block(x, state)
            else:
                x.blockSignals(state)

    def load_new_sequence(self, dict_file):
        # Load a new sequence from a csv file
        dictionnary = self.read_file_dict(dict_file)
        self.block(self.ui, True)
        curr_index = self.ui.seqtype.findText(dictionnary['Sequence Type'])
        self.ui.seqtype.setCurrentIndex(curr_index)
        self.block(self.ui, False)
        self.change_sequence_type()
        self.block(self.ui, True)
        self.seq.readfromdict(dictionnary)
        self.block(self.ui, False)
        self.seq.up_all()

    def load_new_type(self):
        # Load a new sequence type but with the same previous parameters
        self.change_sequence_type()
        self.seq.up_all()

    def change_sequence_type(self):
        # Switch between sequence type
        if self.ui.seqtype.currentText() == 'FID':
            self.seq = ClassFID(self.ui)
        elif self.ui.seqtype.currentText() == 'Gradient Echo':
            self.seq = ClassFlash(self.ui)
        elif self.ui.seqtype.currentText() == 'Spin Echo':
            self.seq = ClassSpinEcho(self.ui)

    def read_file_dict(self, filename):
        # Load a csv file into dictionnary
        dict_seq = dict()
        read_file = reader(open(filename))
        for row in read_file:
            try:
                dict_seq[row[0]] = eval(row[1])
            except NameError:
                dict_seq[row[0]] = row[1]
            except SyntaxError:
                dict_seq[row[0]] = row[1]

        return dict_seq

if __name__ == "__main__":
    qApp = QApplication(sys.argv)

    aw = SeqedWindow()
    aw.show()

    sys.exit(qApp.exec_())
    qApp.exec_()
