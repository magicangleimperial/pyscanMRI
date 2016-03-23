from grad import Grad
from sequence import Sequence


class ClassFlash(Sequence):
    def __init__(self, gui):
        super(ClassFlash, self).__init__(gui, 'Gradient Echo')
        self.name = 'Gradient Echo'
        self.gui_change()
        self.rf = []
        self.slice = []
        self.phase = []
        self.read = []
        self.acq = []
        self.ti = None
        self.tr = None
        self.te = None
        self.rt = None

    def get_parameters(self):
        rf_args = [self.gui.rft.value(), self.gui.rfw.value()]
        rf_args.append(self.gui.flipa.value())
        self.rf = [Grad(*rf_args)]
        phaset = self.gui.rft.value() + self.gui.rfw.value() + 0.4
        phasew = self.gui.te.value() - (self.gui.acqw.value() / 2)
        phasew -= (self.gui.rfw.value() / 2) + 0.8
        self.phase = [Grad(phaset, phasew, self.gui.phaseamp.value())]
        self.slice = [Grad(self.gui.rft.value(), self.gui.rfw.value(), self.gui.sliceamp.value(), postwidth=phasew)]
        readt = self.gui.te.value() - (self.gui.acqw.value() / 2)
        readt += 0.2 + (self.gui.rfw.value() / 2)
        self.read = [Grad(readt, self.gui.acqw.value(), self.gui.readamp.value(), prewidth=phasew)]
        self.acq = [Grad(readt, self.gui.acqw.value(), 0)]

    def gui_change(self):
        self.gui.acqw.show()
        self.gui.acqwlabel.show()
        self.gui.ti.hide()
        self.gui.tilabel.hide()
        self.gui.te.show()
        self.gui.telabel.show()
        self.gui.rft.hide()
        self.gui.rftlabel.hide()
        self.gui.acqnum.show()
        self.gui.acqnumlabel.show()
        self.gui.phase_steps.show()
        self.gui.phase_stepslabel.show()
        self.gui.slice_steps.show()
        self.gui.slice_stepslabel.show()
        self.gui.readamp.show()
        self.gui.readamplabel.show()
        self.gui.phaset.hide()
        self.gui.phasetlabel.hide()
        self.gui.phasew.hide()
        self.gui.phasewlabel.hide()
        self.gui.phaseamp.show()
        self.gui.phaseamplabel.show()
        self.gui.sliceamp.show()
        self.gui.sliceamplabel.show()
        self.gui.slicethickness.show()
        self.gui.slicethicknesslabel.show()
        self.gui.readtitle.show()
        self.gui.phasetitle.show()
        self.gui.slicetitle.show()
        self.gui.obliquetitle.show()
        self.gui.thetazlabel.show()
        self.gui.thetaplabel.show()
        self.gui.thetaz.show()
        self.gui.thetap.show()
        self.gui.option.clear()
        self.gui.option.addItems(['Multi Slice'])
