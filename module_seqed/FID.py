from grad import Grad
from sequence import Sequence
'''                    Sequence Template
########################################################################
All sequence templates are based on the same idea, only this one is explained.
########################################################################
'''


class ClassFID(Sequence):
    def __init__(self, gui):
        super(ClassFID, self).__init__(gui, 'FID')
        # Template is initialized with various empty variable
        self.name = 'FID'
        self.rf = []
        self.slice = []
        self.phase = []
        self.read = []
        self.acq = []
        self.ti = None
        self.tr = None
        self.te = None
        self.rt = None
        # Gui is changed for the defined template
        self.gui_change()

    def get_parameters(self):
        # All the intelligence is defined here, linking values together
        # Grad is just a class to define gradient pulse
        pulse_start = self.gui.rft.value()
        pulse_length = self.gui.rfw.value()
        pulse_amplitude = self.gui.flipa.value()
        self.rf = [Grad(pulse_start, pulse_length, pulse_amplitude)]
        self.slice = [Grad(0, 0, 0)]
        self.phase = [Grad(0, 0, 0)]
        self.read = [Grad(0, 0, 0)]
        acqt = self.gui.rft.value() + self.gui.rfw.value() + 0.4
        self.acq = [Grad(acqt, self.gui.acqw.value(), 0)]

    def gui_change(self):
        # All gui changes are contained here
        self.gui.acqw.show()
        self.gui.acqwlabel.show()
        self.gui.ti.hide()
        self.gui.tilabel.hide()
        self.gui.te.hide()
        self.gui.telabel.hide()
        self.gui.rft.hide()
        self.gui.rftlabel.hide()
        self.gui.acqnum.hide()
        self.gui.acqnumlabel.hide()
        self.gui.phase_steps.hide()
        self.gui.phase_stepslabel.hide()
        self.gui.slice_steps.hide()
        self.gui.slice_stepslabel.hide()
        self.gui.readamp.hide()
        self.gui.readamplabel.hide()
        self.gui.phaset.hide()
        self.gui.phasetlabel.hide()
        self.gui.phasew.hide()
        self.gui.phasewlabel.hide()
        self.gui.phaseamp.hide()
        self.gui.phaseamplabel.hide()
        self.gui.sliceamp.hide()
        self.gui.sliceamplabel.hide()
        self.gui.slicethickness.hide()
        self.gui.slicethicknesslabel.hide()
        self.gui.readtitle.hide()
        self.gui.phasetitle.hide()
        self.gui.slicetitle.hide()
        self.gui.obliquetitle.hide()
        self.gui.thetazlabel.hide()
        self.gui.thetaplabel.hide()
        self.gui.thetaz.hide()
        self.gui.thetap.hide()
        self.gui.option.clear()
